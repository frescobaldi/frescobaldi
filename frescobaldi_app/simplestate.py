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

r"""
Represents a ly.lex.State as a simplified list of strings.

    \book {
      \header {
        title = \markup { #"

e.g. yields:

    ['lilypond', 'book', 'header', 'markup', 'scheme', 'string']

This is done by examining the state's parsers.
It can be used in snippets or plugin scripts.

The first word is always the mode of the file (e.g. 'lilypond', 'html', etc.).

"""

from __future__ import print_function

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

    return names


parserClasses = {
    # lilypond
    ly.lex.lilypond.ParseMusic: "music",
    ly.lex.lilypond.ParseChord: "chord",
    ly.lex.lilypond.ParseLyricMode: "lyricmode",
    ly.lex.lilypond.ParseChordMode: "chordmode",
    ly.lex.lilypond.ParseFigureMode: "figuremode",
    ly.lex.lilypond.ParseDrumMode: "drummode",
    ly.lex.lilypond.ParsePaper: "paper",
    ly.lex.lilypond.ParseHeader: "header",
    ly.lex.lilypond.ParseLayout: "layout",
    ly.lex.lilypond.ParseBook: "book",
    ly.lex.lilypond.ParseBookPart: "bookpart",
    ly.lex.lilypond.ParseScore: "score",
    ly.lex.lilypond.ParseMidi: "midi",
    ly.lex.lilypond.ParseContext: "context",
    ly.lex.lilypond.ParseWith: "with",
    ly.lex.lilypond.ParseTranslator: "translator",
    ly.lex.lilypond.ParseMarkup: "markup",
    ly.lex.lilypond.ParseOverride: "override",
    ly.lex.lilypond.ParseString: "string",

    # scheme
    ly.lex.scheme.ParseScheme: "scheme",
    ly.lex.scheme.ParseString: "string",

    # html
    ly.lex.html.ParseAttr: "htmlattribute",
    ly.lex.html.ParseStringSQ: "single-quoted-string",
    ly.lex.html.ParseStringDQ: "double-quoted-string",
    ly.lex.html.ParseComment: "comment",
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
    print(state(s))



