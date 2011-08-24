# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

r"""
Represents a ly.lex.State as a simplified string.

    \book {
      \header {
        title = \markup { #"

e.g. yields:

    'lilypond book header markup scheme string'

This is done by examining the state's parsers.
It can be used in snippets or plugin scripts.

The first word is always the mode of the file (e.g. 'lilypond', 'html', etc.).

"""

from __future__ import unicode_literals

import ly.lex.lilypond
import ly.lex.scheme
import ly.lex.html


def state(state):
    names = []
    def append(name):
        if not names or names[-1] != name:
            names.append(name)
    
    for p in state.state:
        name = parserClasses.get(p.__class__)
        if name:
            append(name)
        elif p.mode:
            append(p.mode)
        else:
            for c, name in parserTypes:
                if isinstance(p, c):
                    append(name)
                    break
    
    return ' '.join(names)
    

parserClasses = {
    # lilypond
    ly.lex.lilypond.LilyPondParserMusic: "music",
    ly.lex.lilypond.LilyPondParserChord: "chord",
    ly.lex.lilypond.LilyPondParserLyricMode: "lyricmode",
    ly.lex.lilypond.LilyPondParserChordMode: "chordmode",
    ly.lex.lilypond.LilyPondParserFigureMode: "figuremode",
    ly.lex.lilypond.LilyPondParserDrumMode: "drummode",
    ly.lex.lilypond.LilyPondParserPaper: "paper",
    ly.lex.lilypond.LilyPondParserHeader: "header",
    ly.lex.lilypond.LilyPondParserLayout: "layout",
    ly.lex.lilypond.LilyPondParserBook: "book",
    ly.lex.lilypond.LilyPondParserBookPart: "bookpart",
    ly.lex.lilypond.LilyPondParserScore: "score",
    ly.lex.lilypond.LilyPondParserMidi: "midi",
    ly.lex.lilypond.LilyPondParserContext: "context",
    ly.lex.lilypond.LilyPondParserWith: "with",
    ly.lex.lilypond.MarkupParser: "markup",
    ly.lex.lilypond.LilyPondParserOverride: "override",
    ly.lex.lilypond.StringParser: "string",
    
    # scheme
    ly.lex.scheme.SchemeParser: "scheme",
    ly.lex.scheme.StringParser: "string",
    
    # html
    ly.lex.html.AttrParser: "htmlattribute",
    ly.lex.html.StringSQParser: "single-quoted-string",
    ly.lex.html.StringDQParser: "double-quoted-string",
    ly.lex.html.CommentParser: "comment",
}

parserTypes = (

)


if __name__ == "__main__":
    # test
    text = r"""
    @title bla
    @lilypond
    \relative c' {
      c d e-\markup {
      
    """
    s = ly.lex.guessState(text)
    list(s.tokens(text))
    print state(s)



