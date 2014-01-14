# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Translating the language of pitch names
"""

from __future__ import unicode_literals

import ly.document
import ly.pitch


def translate(cursor, language):
    """Changes the language of the pitch names.
    
    May raise ly.pitch.PitchNameNotAvailable if the current pitch language
    has no quarter tones.
    
    Returns True if there also was a \language or \include language command 
    that was changed. If not and the cursor specified only a part of the 
    document, you could warn the user that a langauge or include command 
    should be added to the document. Or you could call insert_language to 
    add a language command to the top of the document.
    
    """
    start = cursor.start
    cursor.start = 0
    
    source = ly.document.Source(cursor, tokens_with_position=True)

    pitches = ly.pitch.PitchIterator(source)
    tokens = pitches.tokens()
    writer = ly.pitch.pitchWriter(language)
    
    if start > 0:
        # consume tokens before the selection, following the language
        source.consume(tokens, start)
        cursor.start = start
    
    changed = False # track change of \language or \include language command
    with cursor.document as d:
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Note):
                # translate the pitch name
                p = pitches.read(t)
                if p:
                    n = writer(*p)
                    if n != t:
                        d[t.pos:t.end] = n
            elif isinstance(t, ly.pitch.LanguageName):
                if t != language:
                    # change the language name in a command
                    d[t.pos:t.end] = language
                changed = True
    return changed


def insert_language(document, language, version=None):
    """Inserts a language command in the document.
    
    The command is inserted at the top or just below the version line.
    
    If the LilyPond version specified < (2, 13, 38), the \\include command 
    is used, otherwise the newer \\language command.
    
    """
    # maybe TODO: determine version automatically from document
    if version and version < (2, 13, 38):
        text = '\\include "{0}.ly"\n'
    else:
        text = '\\language "{0}"\n'
    text = text.format(language)
    # insert language command on top of file, but below version
    with document:
        for b in document:
            if '\\version' not in document.tokens(b):
                pos = document.position(b)
                document[pos:pos] = text
                break
        else:
            pos = document.size()
            document[pos:pos] = '\n\n' + text


