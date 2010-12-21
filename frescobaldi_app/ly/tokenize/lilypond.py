# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Parses and tokenizes LilyPond input.
"""

from . import (
    Token,
    Item,
    Leaver,
    Increaser,
    Decreaser,
    Space,
    
    ErrorBase,
    CommentBase,
    StringBase,
    EscapeBase,
    NumericBase,
    
    MatchStart,
    MatchEnd,
    Parser,
    StringParserBase,
    FallthroughParser,
)

from .. import words


re_articulation = r"[-_^][_.>|+^-]"
re_dynamic = r"\\(f{1,5}|p{1,5}|mf|mp|fp|spp?|sff?|sfz|rfz)\b"

re_duration = r"(\\(maxima|longa|breve)\b|(1|2|4|8|16|32|64|128|256|512|1024|2048)(?!\d))"
re_dot = r"\."
re_scaling = r"\*[\t ]*\d+(/\d+)?"


class Value(Item, NumericBase):
    pass


class Fraction(Value):
    rx = r"\d+/\d+"
    
    
class Error(ErrorBase):
    pass


class Comment(CommentBase):
    pass


class BlockCommentStart(Comment):
    rx = r"%{"
    def changeState(self, state):
        state.enter(BlockCommentParser)


class BlockCommentEnd(Comment, Leaver):
    rx = r"%}"


class LineComment(Comment):
    rx = r"%.*$"
    

class String(StringBase):
    pass


class StringQuotedStart(String):
    rx = r'"'
    def changeState(self, state):
        state.enter(StringParser)
        

class StringQuotedEnd(String):
    rx = r'"'
    def changeState(self, state):
        state.leave()
        state.endArgument()


class StringQuoteEscape(String, EscapeBase):
    rx = r'\\[\\"]'


class Duration(Token):
    pass


class DurationStart(Duration):
    rx = re_duration
    def changeState(self, state):
        state.enter(DurationParser)


class Dot(Duration):
    rx = re_dot
    
    
class Scaling(Duration):
    rx = re_scaling
    
    
class Delimiter(Token):
    pass


class OpenBracket(Delimiter, Increaser, MatchStart):
    rx = r"\{"
    matchname = "bracket"
    def changeState(self, state):
        if isinstance(state.parser(), LilyPondToplevelParser):
            state.enter(LilyPondMusicParser)
        else:
            super(OpenBracket, self).changeState(state)


class CloseBracket(Delimiter, Decreaser, MatchEnd):
    rx = r"\}"
    matchname = "bracket"


class OpenSimultaneous(Delimiter, Increaser, MatchStart):
    rx = r"<<"
    matchname = "simultaneous"
    def changeState(self, state):
        if isinstance(state.parser(), LilyPondToplevelParser):
            state.enter(LilyPondMusicParser)
        else:
            super(OpenSimultaneous, self).changeState(state)


class CloseSimultaneous(Delimiter, Decreaser, MatchEnd):
    rx = r">>"
    matchname = "simultaneous"
    

class Slur(Token):
    pass


class SlurStart(Slur, MatchStart):
    rx = r"\("
    matchname = "slur"
    

class SlurEnd(Slur, MatchEnd):
    rx = r"\)"
    matchname = "slur"
    

class PhrasingSlurStart(SlurStart):
    rx = r"\\\("
    matchname = "phrasingslur"
    
    
class PhrasingSlurEnd(SlurEnd):
    rx = r"\\\)"
    matchname = "phrasingslur"
    

class Tie(Slur):
    rx = r"~"


class Beam(Token):
    pass


class BeamStart(Beam, MatchStart):
    rx = r"\["
    matchname = "beam"


class BeamEnd(Beam, MatchEnd):
    rx = r"\]"
    matchname = "beam"


class Ligature(Token):
    pass


class LigatureStart(Ligature, MatchStart):
    rx = r"\\\["
    matchname = "ligature"
    
    
class LigatureEnd(Ligature, MatchEnd):
    rx = r"\\\]"
    matchname = "ligature"
    
    
class Keyword(Item):
    rx = r"\\({0})\b".format("|".join(words.lilypond_keywords))


class VoiceSeparator(Keyword):
    rx = r"\\\\"
    

class Articulation(Token):
    rx = re_articulation
    
    
class Dynamic(Token):
    rx = re_dynamic


class Command(Item):
    rx = r"\\({0})\b".format("|".join(words.lilypond_music_commands))
    

class Markup(Command):
    rx = r"\\markup\b"
    def changeState(self, state):
        state.enter(MarkupParser)


class MarkupLines(Markup):
    rx = r"\\markuplines\b"
    def changeState(self, state):
        state.enter(MarkupParser)


class MarkupCommand(Markup):
    rx = r"\\[A-Za-z]+(-[A-Za-z]+)*"
    def changeState(self, state):
        command = self[1:]
        if command in words.markupcommands_nargs[0]:
            state.endArgument()
        else:
            for argcount in 2, 3, 4:
                if command in words.markupcommands_nargs[argcount]:
                    break
            else:
                argcount = 1
            state.enter(MarkupParser, argcount)


class MarkupWord(Item):
    rx = r'[^{}"\\\s#%]+'


class Repeat(Command):
    rx = r"\\repeat\b"
    def changeState(self, state):
        state.enter(RepeatParser)
    
    
class RepeatSpecifier(Repeat):
    rx = r"\b(volta|unfold|percent|tremolo)\b"
    

class RepeatStringSpecifier(String, Repeat):
    rx = r'"(volta|unfold|percent|tremolo)"'
    

class RepeatCount(Value, Leaver):
    rx = r"\d+"


class UserCommand(Token):
    rx = r"\\[A-Za-z]+"
    
    
class SchemeStart(Item):
    rx = "#"
    def changeState(self, state):
        import scheme
        state.enter(scheme.SchemeParser)


class Context(Token):
    rx = r"\b({0})\b".format("|".join(words.contexts))
    
    
class Grob(Token):
    rx = r"\b({0})\b".format("|".join(words.grobs))


class Chord(Token):
    """Base class for Chord delimiters."""
    pass


class ChordStart(Chord):
    rx = r"<"
    def changeState(self, state):
        state.enter(LilyPondChordParser)


class ChordEnd(Chord, Leaver):
    rx = r">"
    

class ErrorInChord(Error):
    rx = "|".join((
        re_articulation, # articulation
        r"<<|>>", # double french quotes
        r"\\[\\\]\[\(\)()]", # slurs beams
    ))
    
# Parsers

class LilyPondParser(Parser):
    """Base class for all LilyPond parsers (toplevel, music, markup etc)"""
    items = (
        Space,
        BlockCommentStart,
        LineComment,
        SchemeStart,
        StringQuotedStart,
    )


class LilyPondToplevelParser(LilyPondParser):
    """Parses LilyPond from the toplevel of a file."""
    items = LilyPondParser.items + (
        Keyword,
        Markup,
        MarkupLines,
        Repeat,
        Fraction,
        Command,
        UserCommand,
        OpenBracket,
        OpenSimultaneous,
        Context,
        Grob,
    )


class LilyPondMusicParser(LilyPondParser):
    """Parses LilyPond music expressions."""
    items = LilyPondParser.items + (
        Keyword,
        Markup,
        MarkupLines,
        Repeat,
        Dynamic,
        Fraction,
        DurationStart,
        Command,
        UserCommand,
        VoiceSeparator,
        OpenBracket, CloseBracket,
        OpenSimultaneous, CloseSimultaneous,
        ChordStart,
        Context,
        Grob,
        SlurStart, SlurEnd,
        PhrasingSlurStart, PhrasingSlurEnd,
        Tie,
        BeamStart, BeamEnd,
        LigatureStart, LigatureEnd,
        Articulation,
    )
    

class LilyPondChordParser(LilyPondMusicParser):
    """LilyPond inside chords < >"""
    items = (
        ErrorInChord,
        ChordEnd,
    ) + LilyPondMusicParser.items


class StringParser(StringParserBase):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class BlockCommentParser(Parser):
    default = Comment
    items = (
        BlockCommentEnd,
    )


class MarkupParser(Parser):
    argcount = 1
    items =  (
#        MarkupScore,
        MarkupCommand,
        OpenBracket,
        CloseBracket,
        MarkupWord,
    ) + LilyPondParser.items


class RepeatParser(FallthroughParser):
    items = (
        Space,
        RepeatSpecifier,
        RepeatStringSpecifier,
        RepeatCount,
    )
    
    def fallthrough(self, state):
        state.leave()


class DurationParser(FallthroughParser):
    items = (
        Space,
        Dot,
    )
    def fallthrough(self, state):
        state.replace(DurationScalingParser)
        
        
class DurationScalingParser(DurationParser):
    items = (
        Space,
        Scaling,
    )
    def fallthrough(self, state):
        state.leave()


    
    