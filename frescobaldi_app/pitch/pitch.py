# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Implementation of the tools to edit pitch of selected music.
"""

from __future__ import unicode_literals

import itertools
import re

from PyQt4.QtGui import QMessageBox, QTextCursor
from fractions import Fraction

import app
import userguide
import icons
import ly.pitch.translate
import ly.pitch.transpose
import ly.pitch.rel2abs
import ly.lex.lilypond
import cursortools
import qutil
import lydocument
import tokeniter
import documentinfo
import lilypondinfo
import inputdialog


def changeLanguage(cursor, language):
    """Changes the language of the pitch names."""
    c = lydocument.cursor(cursor)
    try:
        changed = ly.pitch.translate.translate(c, language)
    except ly.pitch.PitchNameNotAvailable:
        QMessageBox.critical(None, app.caption(_("Pitch Name Language")), _(
            "Can't perform the requested translation.\n\n"
            "The music contains quarter-tone alterations, but "
            "those are not available in the pitch language \"{name}\"."
            ).format(name=language))
        return
    if changed:
        return
    if not cursor.hasSelection():
        # there was no selection and no language command, so insert one
        version = (documentinfo.info(cursor.document()).version()
                   or lilypondinfo.preferred().version())
        ly.pitch.translate.insert_language(c.document, language, version)
        return
    # there was a selection but no command, user must insert manually.
    QMessageBox.information(None, app.caption(_("Pitch Name Language")),
        '<p>{0}</p>'
        '<p><code>\\include "{1}.ly"</code> {2}</p>'
        '<p><code>\\language "{1}"</code> {3}</p>'.format(
            _("The pitch language of the selected text has been "
                "updated, but you need to manually add the following "
                "command to your document:"),
            language,
            _("(for LilyPond below 2.14), or"),
            _("(for LilyPond 2.14 and higher.)")))


def rel2abs(cursor):
    """Converts pitches from relative to absolute."""
    with qutil.busyCursor():
        c = lydocument.cursor(cursor)
        ly.pitch.rel2abs.rel2abs(c)


def abs2rel(cursor):
    """Converts pitches from absolute to relative."""
    selection = cursor.hasSelection()
    if selection:
        start = cursor.selectionStart()
        cursor.setPosition(cursor.selectionEnd())
        cursor.setPosition(0, QTextCursor.KeepAnchor)
        source = tokeniter.Source.selection(cursor, True)
    else:
        source = tokeniter.Source.document(cursor, True)
    
    pitches = PitchIterator(source)
    psource = pitches.pitches()
    if selection:
        # consume tokens before the selection, following the language
        t = source.consume(pitches.tokens(), start)
        if t:
            psource = itertools.chain((t,), psource)
    
    # this class dispatches the tokens. we can't use a generator function
    # as that doesn't like to be called again while there is already a body
    # running.
    class gen(object):
        def __iter__(self):
            return self
        
        def __next__(self):
            t = next(psource)
            while isinstance(t, (ly.lex.Space, ly.lex.Comment)):
                t = next(psource)
            if t == '\\relative' and isinstance(t, ly.lex.lilypond.Command):
                relative()
                t = next(psource)
            elif isinstance(t, ly.lex.lilypond.ChordMode):
                consume() # do not change chords
                t = next(psource)
            elif isinstance(t, ly.lex.lilypond.MarkupScore):
                consume()
                t = next(psource)
            return t
        
        next = __next__
            
    tsource = gen()

    def context():
        """Consume tokens till the level drops (we exit a construct)."""
        depth = source.state.depth()
        for t in tsource:
            yield t
            if source.state.depth() < depth:
                return
    
    def consume():
        """Consume tokens from context() returning the last token, if any."""
        t = None
        for t in context():
            pass
        return t
    
    def relative():
        """Consume the whole \relative expression without doing anything. """
        # skip pitch argument
        t = next(tsource)
        if isinstance(t, Pitch):
            t = next(tsource)
        
        while True:
            # eat stuff like \new Staff == "bla" \new Voice \notes etc.
            if isinstance(source.state.parser(), ly.lex.lilypond.ParseTranslator):
                t = consume()
            elif isinstance(t, ly.lex.lilypond.NoteMode):
                t = next(tsource)
            else:
                break
        
        if t in ('{', '<<', '<'):
            consume()
    
    # Do it!
    with qutil.busyCursor():
        with cursortools.Writer(cursor.document()) as writer:
            for t in tsource:
                if t in ('{', '<<'):
                    # Ok, parse current expression.
                    c = source.cursor(t, end=0) # insert the \relative command
                    lastPitch = None
                    chord = None
                    for t in context():
                        # skip commands with pitches that do not count
                        if isinstance(t, ly.lex.lilypond.PitchCommand):
                            consume()
                        elif isinstance(t, ly.lex.lilypond.ChordStart):
                            # Handle chord
                            chord = []
                        elif isinstance(t, ly.lex.lilypond.ChordEnd):
                            if chord:
                                lastPitch = chord[0]
                            chord = None
                        elif isinstance(t, Pitch):
                            # Handle pitch
                            if lastPitch is None:
                                lastPitch = Pitch.c1()
                                lastPitch.octave = t.octave
                                if t.note > 3:
                                    lastPitch.octave += 1
                                writer.insertText(c,
                                    "\\relative {0} ".format(
                                        lastPitch.output(pitches.language)))
                            p = t.copy()
                            t.makeRelative(lastPitch)
                            pitches.write(t, writer)
                            lastPitch = p
                            # remember the first pitch of a chord
                            if chord == []:
                                chord.append(p)


def getTransposer(document, mainwindow):
    """Show a dialog and return the desired transposer.
    
    Returns None if the dialog was cancelled.
    
    """
    language = documentinfo.info(document).pitchLanguage() or 'nederlands'
    
    def readpitches(text):
        """Reads pitches from text."""
        result = []
        for pitch, octave in re.findall(r"([a-z]+)([,']*)", text):
            r = ly.pitch.pitchReader(language)(pitch)
            if r:
                result.append(ly.pitch.Pitch(*r, octave=ly.pitch.octaveToNum(octave)))
        return result
    
    def validate(text):
        """Returns whether the text contains exactly two pitches."""
        return len(readpitches(text)) == 2
    
    text = inputdialog.getText(mainwindow, _("Transpose"), _(
        "Please enter two absolute pitches, separated by a space, "
        "using the pitch name language \"{language}\"."
        ).format(language=language), icon = icons.get('tools-transpose'),
        help = "transpose", validate = validate)
    
    if text:
        return ly.pitch.transpose.Transposer(*readpitches(text))


def getModalTransposer(document, mainwindow):
    """Show a dialog and return the desired modal transposer.
    
    Returns None if the dialog was cancelled.
    
    """
    language = documentinfo.info(document).pitchLanguage() or 'nederlands'
    
    def readpitches(text):
        """Reads pitches from text."""
        result = []
        for pitch, octave in re.findall(r"([a-z]+)([,']*)", text):
            r = ly.pitch.pitchReader(language)(pitch)
            if r:
                result.append(ly.pitch.Pitch(*r, octave=ly.pitch.octaveToNum(octave)))
        return result
    
    def validate(text):
        """Returns whether the text is an integer followed by the name of a key."""
        words = text.split()
        if len(words) != 2:
            return False
        try:
            steps = int(words[0])
            keyIndex = ly.pitch.transpose.ModalTransposer.getKeyIndex(words[1])
            return True
        except ValueError:
            return False
    
    text = inputdialog.getText(mainwindow, _("Transpose"), _(
        "Please enter the number of steps to alter by, followed by a key signature. (i.e. \"5 F\")"
        ), icon = icons.get('tools-transpose'),
        help = "modal_transpose", validate = validate)
    if text:
        words = text.split()
        return ly.pitch.transpose.ModalTransposer(int(words[0]), ly.pitch.transpose.ModalTransposer.getKeyIndex(words[1]))

    
def transpose(cursor, transposer, mainwindow=None):
    """Transpose pitches using the specified transposer."""
    c = lydocument.cursor(cursor)
    try:
        ly.pitch.transpose.transpose(c, transposer)
    except ly.pitch.PitchNameNotAvailable as e:
        QMessageBox.critical(mainwindow, app.caption(_("Transpose")), _(
            "Can't perform the requested transposition.\n\n"
            "The transposed music would contain quarter-tone alterations "
            "that are not available in the pitch language \"{language}\"."
            ).format(language = e.language))


class PitchIterator(object):
    """Iterate over notes or pitches in a source."""
    
    def __init__(self, source):
        """Initializes us with a tokeniter.Source.
        
        The language is set to "nederlands".
        
        """
        self.source = source
        self.setLanguage("nederlands")
    
    def setLanguage(self, lang):
        """Changes the pitch name language to use.
        
        Called internally when \language or \include tokens are encoutered
        with a valid language name/file.
        
        Sets the language attribute to the language name and the read attribute
        to an instance of ly.pitch.PitchReader.
        
        """
        if lang in ly.pitch.pitchInfo.keys():
            self.language = lang
            return True
    
    def position(self, t):
        """Returns the cursor position for the given token or Pitch."""
        if isinstance(t, Pitch):
            return t.noteCursor.selectionStart()
        else:
            return self.source.position(t)
    
    def tokens(self):
        """Yield just all tokens from the source, following the language."""
        for t in self.source:
            yield t
            if isinstance(t, ly.lex.lilypond.Keyword):
                if t in ("\\include", "\\language"):
                    for t in self.source:
                        if not isinstance(t, ly.lex.Space) and t != '"':
                            lang = t[:-3] if t.endswith('.ly') else t[:]
                            if self.setLanguage(lang):
                                yield LanguageName(lang, t.pos)
                            break
                        yield t
    
    def pitches(self):
        """Yields all tokens, but collects Note and Octave tokens.
        
        When a Note is encoutered, also reads octave and octave check and then
        a Pitch is yielded instead of the tokens.
        
        """
        tokens = self.tokens()
        for t in tokens:
            while isinstance(t, ly.lex.lilypond.Note):
                p = self.read(t)
                if not p:
                    break
                p = Pitch(*p)
                p.origNoteToken = t
                p.noteCursor = self.source.cursor(t)
                p.octaveCursor = self.source.cursor(t, start=len(t))
                t = None # prevent hang in this loop
                for t in tokens:
                    if isinstance(t, ly.lex.lilypond.OctaveCheck):
                        p.octaveCheck = p.origOctaveCheck = ly.pitch.octaveToNum(t)
                        p.octaveCheckCursor = self.source.cursor(t)
                        break
                    elif isinstance(t, ly.lex.lilypond.Octave):
                        p.octave = p.origOctave = ly.pitch.octaveToNum(t)
                        p.octaveCursor = self.source.cursor(t)
                    elif not isinstance(t, (ly.lex.Space, ly.lex.lilypond.Accidental)):
                        break
                yield p
                if t is None:
                    break
            else:
                yield t
        
    def read(self, token):
        """Reads the token and returns (note, alter) or None."""
        return ly.pitch.pitchReader(self.language)(token)
    
    def write(self, pitch, writer, language=None):
        """Outputs a changed Pitch to the cursortools.Writer."""
        pwriter = ly.pitch.pitchWriter(language or self.language)
        note = pwriter(pitch.note, pitch.alter)
        if note != pitch.origNoteToken:
            writer.insertText(pitch.noteCursor, note)
        if pitch.octave != pitch.origOctave:
            writer.insertText(pitch.octaveCursor, ly.pitch.octaveToString(pitch.octave))
        if pitch.origOctaveCheck is not None:
            if pitch.octaveCheck is None:
                writer.removeSelectedText(pitch.octaveCheckCursor)
            else:
                octaveCheck = '=' + ly.pitch.octaveToString(pitch.octaveCheck)
                writer.insertText(pitch.octaveCheckCursor, octaveCheck)


class LanguageName(ly.lex.Token):
    pass


class Pitch(ly.pitch.Pitch):
    """A Pitch storing cursors for the note name, octave and octaveCheck."""
    noteCursor = None
    octaveCheck = None
    octaveCursor = None
    octaveCheckCursor = None
    origNoteToken = None
    origOctave = 0
    origOctaveCheck = None


def getpitches(iterable):
    """Consumes iterable but only yields Pitch instances."""
    for p in iterable:
        if isinstance(p, Pitch):
            yield p


