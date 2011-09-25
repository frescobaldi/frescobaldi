# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 by Wilbert Berendsen
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

from PyQt4.QtGui import QMessageBox, QTextCursor

import ly.pitch
import ly.lex.lilypond
import cursortools
import util
import tokeniter
import documentinfo
import lilypondinfo


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
    writer = ly.pitch.pitchWriter(language)
    
    if selection:
        # consume tokens before the selection, following the language
        source.consume(reader, start)
    
    changed = False # track change of \language or \include language command
    with cursortools.editBlock(cursor):
        try:
            with util.busyCursor():
                with cursortools.Editor() as e:
                    for t in pitches.tokens():
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
            QMessageBox.critical(None, _("Pitch Name Language"), _(
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
    QMessageBox.information(None, _("Pitch Name Language"), 
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
               or lilypondinfo.preferred().version)
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
        source = tokeniter.Source.selection(cursor)
    else:
        source = tokeniter.Source.document(cursor)
    
    pitches = PitchIterator(source)
    
    if selection:
        # consume tokens before the selection, following the language
        source.consume(reader, start)
    
    # TEMP!!! test code that simply transposes all notes one octave higher
    with cursortools.Editor() as e:
        for t in pitches.pitches():
            if isinstance(t, Pitch):
                t.octave += 2
                t.alter += 1
                pitches.write(t, e)


def abs2rel(cursor):
    """Converts pitches from absolute to relative."""


def transpose(cursor, mainwindow):
    """Transposes pitches."""




class PitchIterator(object):
    """Iterate over notes or pitches in a source.
    
    
    """
    
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
    
    def tokens(self):
        """Yield just all tokens from the source, following the language."""
        for t in self.source:
            yield t
            if isinstance(t, ly.lex.lilypond.Keyword):
                if t in ("\\include", "\\language"):
                    for t in self.iterable:
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
                if p:
                    p = Pitch(*p)
                    p.noteCursor = self.source.cursor(t)
                    p.octaveCursor = self.source.cursor(t, start=len(t))
                    for t in tokens:
                        if isinstance(t, ly.lex.lilypond.OctaveCheck):
                            p.octaveCheck = ly.pitch.octaveToNum(t)
                            p.octaveCheckCursor = self.source.cursor(t, start=1)
                            break
                        elif isinstance(t, ly.lex.lilypond.Octave):
                            p.octave = ly.pitch.octaveToNum(t)
                            p.octaveCursor = self.source.cursor(t)
                        elif not isinstance(t, (ly.lex.Space, ly.lex.lilypond.Accidental)):
                            break
                    yield p
            yield t
        
    def read(self, token):
        """Reads the token and returns (note, alter) or None."""
        return ly.pitch.pitchReader(self.language)(token)
    
    def write(self, pitch, editor, language=None):
        """Outputs a changed Pitch to the cursortools.Editor."""
        def insert(cursor, text):
            if cursor.selectedText() != text:
                editor.insertText(cursor, text)
        writer = ly.pitch.pitchWriter(language or self.language)
        insert(pitch.noteCursor, writer(pitch.note, pitch.alter))
        insert(pitch.octaveCursor, ly.pitch.octaveToString(pitch.octave))
        if pitch.octaveCheck is not None:
            insert(pitch.octaveCheckCursor, ly.pitch.octaveToString(pitch.octaveCheck))


class LanguageName(ly.lex.Token):
    pass


class Pitch(ly.pitch.Pitch):
    """A Pitch storing cursors for the note name, octave and octaveCheck."""
    noteCursor = None
    octaveCheck = None
    octaveCursor = None
    octaveCheckCursor = None

