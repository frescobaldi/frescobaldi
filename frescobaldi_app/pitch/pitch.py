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

from PyQt4.QtGui import QTextCursor

import slexer
import ly.pitch
import ly.lex.lilypond
import cursortools
import tokeniter


def changeLanguage(cursor, language):
    """Changes the language of the pitch names."""
    if cursor.hasSelection():
        start = cursor.document().findBlock(cursor.selectionStart())
        startpos = cursor.selectionStart() - start.position()
        cursor.setPosition(cursor.selectionEnd())
        cursor.setPosition(0, QTextCursor.KeepAnchor)
    else:
        start = cursor.document().firstBlock()
        startpos = 0
        cursor.select(QTextCursor.Document)
    source = tokeniter.Source.selection(cursor)
    reader = PitchReader(source)
    writer = ly.pitch.pitchWriter(language)
    # follow the language names
    changed = False
    for t in reader:
        if source.block == start and t.end >= startpos:
            break
        if not changed and isinstance(t, LanguageName):
            changed = True
    # translate the pitches
    with cursortools.Editor() as e:
        for t in reader:
            if isinstance(t, ly.lex.lilypond.Note):
                p = reader.read(t)
                if p:
                    e.insertText(source.cursor(t), writer(*p))
            elif isinstance(t, LanguageName) and t != language:
                e.insertText(source.cursor(t), language)


def rel2abs(cursor):
    """Converts pitches from relative to absolute."""


def abs2rel(cursor):
    """Converts pitches from absolute to relative."""


def transpose(cursor, mainwindow):
    """Transposes pitches."""




class PitchReader(object):
    """Reads a token source and yields all tokens and LanguageName tokens."""
    def __init__(self, iterable):
        self.setLanguage("nederlands")
        self.iterable = iter(iterable)
    
    def __iter__(self):
        for t in self.iterable:
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
    
    def setLanguage(self, lang):
        """Changes the pitch name language to use.
        
        Called internally when \language or \include tokens are encoutered
        with a valid language name/file.
        
        Sets the language attribute to the language name and the read attribute
        to an instance of ly.pitch.PitchReader.
        
        """
        if lang in ly.pitch.pitchInfo.keys():
            self.language = lang
            self.read = ly.pitch.pitchReader(lang)
            return True


class LanguageName(ly.lex.Token):
    def __new__(cls, value, pos):
        token = super(ly.lex.Token, cls).__new__(cls, value)
        token.pos = pos
        token.end = pos + len(token)
        return token

