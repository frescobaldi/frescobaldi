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
import ly.pitch
import ly.lex.lilypond
import cursortools
import qutil
import tokeniter
import documentinfo
import lilypondinfo
import inputdialog


def changeLanguage(cursor, language):
    """Changes the language of the pitch names."""
    selection = cursor.hasSelection()
    if selection:
        start = cursor.selectionStart()
        cursor.setPosition(cursor.selectionEnd())
        cursor.setPosition(0, QTextCursor.KeepAnchor)
        source = tokeniter.Source.selection(cursor)
    else:
        source = tokeniter.Source.document(cursor)
    
    pitches = PitchIterator(source)
    tokens = pitches.tokens()
    writer = ly.pitch.pitchWriter(language)
    
    if selection:
        # consume tokens before the selection, following the language
        source.consume(tokens, start)
    
    changed = False # track change of \language or \include language command
    with cursortools.compress_undo(cursor):
        try:
            with qutil.busyCursor():
                with cursortools.Editor() as e:
                    for t in tokens:
                        if isinstance(t, ly.lex.lilypond.Note):
                            # translate the pitch name
                            p = pitches.read(t)
                            if p:
                                n = writer(*p)
                                if n != t:
                                    e.insertText(source.cursor(t), n)
                        elif isinstance(t, LanguageName) and t != language:
                            # change the language name in a command
                            e.insertText(source.cursor(t), language)
                            changed = True
        except ly.pitch.PitchNameNotAvailable:
            QMessageBox.critical(None, app.caption(_("Pitch Name Language")), _(
                "Can't perform the requested translation.\n\n"
                "The music contains quarter-tone alterations, but "
                "those are not available in the pitch language \"{name}\"."
                ).format(name=language))
            return
        if changed:
            return
        if not selection:
            # there was no selection and no language command, so insert one
            insertLanguage(cursor.document(), language)
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


def insertLanguage(document, language):
    """Inserts a language command in the document.
    
    The command is inserted at the top or just below the version line.
    If the document uses LilyPond < 2.13.38, the \\include command is used,
    otherwise the newer \\language command.
    
    """
    version = (documentinfo.info(document).version()
               or lilypondinfo.preferred().version())
    if version and version < (2, 13, 38):
        text = '\\include "{0}.ly"'
    else:
        text = '\\language "{0}"'
    # insert language command on top of file, but below version
    block = document.firstBlock()
    c = QTextCursor(block)
    if '\\version' in tokeniter.tokens(block):
        c.movePosition(QTextCursor.EndOfBlock)
        text = '\n' + text
    else:
        text += '\n'
    c.insertText(text.format(language))


def rel2abs(cursor):
    """Converts pitches from relative to absolute."""
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
                relative(t)
                t = next(psource)
            elif isinstance(t, ly.lex.lilypond.MarkupScore):
                consume()
                t = next(psource)
            return t
        
        next = __next__
            
    tsource = gen()
    
    def makeAbsolute(p, lastPitch):
        """Makes pitch absolute (honoring and removing possible octaveCheck)."""
        if p.octaveCheck is not None:
            p.octave = p.octaveCheck
            p.octaveCheck = None
        else:
            p.makeAbsolute(lastPitch)
        pitches.write(p, editor)
    
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
    
    def relative(t):
        c = source.cursor(t)
        lastPitch = None
        
        t = next(tsource)
        if isinstance(t, Pitch):
            lastPitch = t
            t = next(tsource)
        else:
            lastPitch = Pitch.c1()
        
        # remove the \relative <pitch> tokens
        c.setPosition(source.position(t), c.KeepAnchor)
        editor.removeSelectedText(c)
        
        while True:
            # eat stuff like \new Staff == "bla" \new Voice \notes etc.
            if isinstance(source.state.parser(), ly.lex.lilypond.ParseTranslator):
                t = consume()
            elif isinstance(t, (ly.lex.lilypond.ChordMode, ly.lex.lilypond.NoteMode)):
                t = next(tsource)
            else:
                break
        
        # now convert the relative expression to absolute
        if t in ('{', '<<'):
            # Handle full music expression { ... } or << ... >>
            for t in context():
                # skip commands with pitches that do not count
                if isinstance(t, ly.lex.lilypond.PitchCommand):
                    if t == '\\octaveCheck':
                        c = source.cursor(t)
                        for p in getpitches(context()):
                            # remove the \octaveCheck
                            lastPitch = p
                            c.setPosition((p.octaveCursor or p.noteCursor).selectionEnd(), c.KeepAnchor)
                            editor.removeSelectedText(c)
                            break
                    else:
                        consume()
                elif isinstance(t, ly.lex.lilypond.ChordStart):
                    # handle chord
                    chord = [lastPitch]
                    for p in getpitches(context()):
                        makeAbsolute(p, chord[-1])
                        chord.append(p)
                    lastPitch = chord[:2][-1] # same or first
                elif isinstance(t, Pitch):
                    makeAbsolute(t, lastPitch)
                    lastPitch = t
        elif isinstance(t, ly.lex.lilypond.ChordStart):
            # Handle just one chord
            for p in getpitches(context()):
                makeAbsolute(p, lastPitch)
                lastPitch = p
        elif isinstance(t, Pitch):
            # Handle just one pitch
            makeAbsolute(t, lastPitch)
    
    # Do it!
    with qutil.busyCursor():
        with cursortools.Editor() as editor:
            for t in tsource:
                pass


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
        with cursortools.Editor() as editor:
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
                                editor.insertText(c,
                                    "\\relative {0} ".format(
                                        lastPitch.output(pitches.language)))
                            p = t.copy()
                            t.makeRelative(lastPitch)
                            pitches.write(t, editor)
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
        return ly.pitch.Transposer(*readpitches(text))


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
            keyIndex = ly.pitch.ModalTransposer.getKeyIndex(words[1])
            return True
        except ValueError:
            return False
    
    text = inputdialog.getText(mainwindow, _("Transpose"), _(
        "Please enter the number of steps to alter by, followed by a key signature. (i.e. \"5 F\")"
        ), icon = icons.get('tools-transpose'),
        help = "modal_transpose", validate = validate)
    if text:
        words = text.split()
        return ly.pitch.ModalTransposer(int(words[0]), ly.pitch.ModalTransposer.getKeyIndex(words[1]))

    
def transpose(cursor, transposer, mainwindow=None):
    """Transpose pitches using the specified transposer."""
    
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
    
    class gen(object):
        def __init__(self):
            self.inSelection = not selection
        
        def __iter__(self):
            return self
        
        def __next__(self):
            while True:
                t = next(psource)
                if isinstance(t, (ly.lex.Space, ly.lex.Comment)):
                    continue
                elif not self.inSelection and pitches.position(t) >= start:
                    self.inSelection = True
                # Handle stuff that's the same in relative and absolute here
                if t == "\\relative":
                    relative()
                elif isinstance(t, ly.lex.lilypond.MarkupScore):
                    absolute(context())
                elif isinstance(t, ly.lex.lilypond.ChordMode):
                    chordmode()
                elif isinstance(t, ly.lex.lilypond.PitchCommand):
                    if t == "\\transposition":
                        next(psource) # skip pitch
                    elif t == "\\transpose":
                        for p in getpitches(context()):
                            transpose(p)
                    elif t == "\\key":
                        for p in getpitches(context()):
                            transpose(p, 0)
                    else:
                        return t
                else:
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
        
    def transpose(p, resetOctave = None):
        """Transpose absolute pitch, using octave if given."""
        transposer.transpose(p)
        if resetOctave is not None:
            p.octave = resetOctave
        if tsource.inSelection:
            pitches.write(p, editor)

    def chordmode():
        """Called inside \\chordmode or \\chords."""
        for p in getpitches(context()):
            transpose(p, 0)
            
    def absolute(tokens):
        """Called when outside a possible \\relative environment."""
        for p in getpitches(tokens):
            transpose(p)
    
    def relative():
        """Called when \\relative is encountered."""
        def transposeRelative(p, lastPitch):
            """Transposes a relative pitch; returns the pitch in absolute form."""
            # absolute pitch determined from untransposed pitch of lastPitch
            p.makeAbsolute(lastPitch)
            if not tsource.inSelection:
                return p
            # we may change this pitch. Make it relative against the
            # transposed lastPitch.
            try:
                last = lastPitch.transposed
            except AttributeError:
                last = lastPitch
            # transpose a copy and store that in the transposed
            # attribute of lastPitch. Next time that is used for
            # making the next pitch relative correctly.
            newLastPitch = p.copy()
            transposer.transpose(p)
            newLastPitch.transposed = p.copy()
            if p.octaveCheck is not None:
                p.octaveCheck = p.octave
            p.makeRelative(last)
            if relPitch:
                # we are allowed to change the pitch after the
                # \relative command. lastPitch contains this pitch.
                lastPitch.octave += p.octave
                p.octave = 0
                pitches.write(lastPitch, editor)
                del relPitch[:]
            pitches.write(p, editor)
            return newLastPitch

        lastPitch = None
        relPitch = [] # we use a list so it can be changed from inside functions
        
        # find the pitch after the \relative command
        t = next(tsource)
        if isinstance(t, Pitch):
            lastPitch = t
            if tsource.inSelection:
                relPitch.append(lastPitch)
            t = next(tsource)
        else:
            lastPitch = Pitch.c1()
        
        while True:
            # eat stuff like \new Staff == "bla" \new Voice \notes etc.
            if isinstance(source.state.parser(), ly.lex.lilypond.ParseTranslator):
                t = consume()
            elif isinstance(t, ly.lex.lilypond.NoteMode):
                t = next(tsource)
            else:
                break
        
        # now transpose the relative expression
        if t in ('{', '<<'):
            # Handle full music expression { ... } or << ... >>
            for t in context():
                if t == '\\octaveCheck':
                    for p in getpitches(context()):
                        lastPitch = p.copy()
                        del relPitch[:]
                        if tsource.inSelection:
                            transposer.transpose(p)
                            lastPitch.transposed = p
                            pitches.write(p, editor)
                elif isinstance(t, ly.lex.lilypond.ChordStart):
                    chord = [lastPitch]
                    for p in getpitches(context()):
                        chord.append(transposeRelative(p, chord[-1]))
                    lastPitch = chord[:2][-1] # same or first
                elif isinstance(t, Pitch):
                    lastPitch = transposeRelative(t, lastPitch)
        elif isinstance(t, ly.lex.lilypond.ChordStart):
            # Handle just one chord
            for p in getpitches(context()):
                lastPitch = transposeRelative(p, lastPitch)
        elif isinstance(t, Pitch):
            # Handle just one pitch
            transposeRelative(token, lastPitch)

    # Do it!
    try:
        with qutil.busyCursor():
            with cursortools.Editor() as editor:
                absolute(tsource)
    except ly.pitch.PitchNameNotAvailable:
        QMessageBox.critical(mainwindow, app.caption(_("Transpose")), _(
            "Can't perform the requested transposition.\n\n"
            "The transposed music would contain quarter-tone alterations "
            "that are not available in the pitch language \"{language}\"."
            ).format(language = pitches.language))


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
    
    def write(self, pitch, editor, language=None):
        """Outputs a changed Pitch to the cursortools.Editor."""
        writer = ly.pitch.pitchWriter(language or self.language)
        note = writer(pitch.note, pitch.alter)
        if note != pitch.origNoteToken:
            editor.insertText(pitch.noteCursor, note)
        if pitch.octave != pitch.origOctave:
            editor.insertText(pitch.octaveCursor, ly.pitch.octaveToString(pitch.octave))
        if pitch.origOctaveCheck is not None:
            if pitch.octaveCheck is None:
                editor.removeSelectedText(pitch.octaveCheckCursor)
            else:
                octaveCheck = '=' + ly.pitch.octaveToString(pitch.octaveCheck)
                editor.insertText(pitch.octaveCheckCursor, octaveCheck)


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


