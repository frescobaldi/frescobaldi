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


class Skip(Token):
    rx = r"(\\skip|s)(?![A-Za-z])"
    
    
class Rest(Token):
    rx = r"[Rr](?![A-Za-z])"
    
    
class Note(Token):
    rx = r"[a-z]+(?![A-Za-z])"
    

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


class OpenBracket(Delimiter, MatchStart):
    """An open bracket, subclass to enter different parsers."""
    rx = r"\{"
    matchname = "bracket"


class CloseBracket(Delimiter, MatchEnd):
    rx = r"\}"
    matchname = "bracket"
    def changeState(self, state):
        state.leave()
        state.endArgument()    
    

class SequentialStart(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserMusic)


class SequentialEnd(CloseBracket):
    pass


class SimultaneousStart(Delimiter, MatchStart):
    rx = r"<<"
    matchname = "simultaneous"
    def changeState(self, state):
        state.enter(LilyPondParserMusic)


class SimultaneousEnd(Delimiter, MatchEnd):
    rx = r">>"
    matchname = "simultaneous"
    def changeState(self, state):
        state.leave()
        state.endArgument()    
    

class OpenBracketScore(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserScore)


class CloseBracketScore(CloseBracket):
    pass


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
    rx = r"\\({0})(?![A-Za-z])".format("|".join(words.lilypond_keywords))


class VoiceSeparator(Delimiter):
    rx = r"\\\\"
    

class Articulation(Token):
    rx = re_articulation
    
    
class Dynamic(Token):
    rx = re_dynamic


class Command(Item):
    rx = r"\\({0})(?![A-Za-z])".format("|".join(words.lilypond_music_commands))
    

class Markup(Command):
    rx = r"\\markup(?![A-Za-z])"
    def changeState(self, state):
        state.enter(MarkupParser, 1)


class MarkupLines(Markup):
    rx = r"\\markuplines(?![A-Za-z])"
    def changeState(self, state):
        state.enter(MarkupParser, 1)


class MarkupCommand(Markup):
    rx = r"\\[A-Za-z]+(-[A-Za-z]+)*(?![A-Za-z])"
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


class MarkupScore(Markup):
    rx = r"\\score\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectScore)


class MarkupWord(Item):
    rx = r'[^{}"\\\s#%]+'


class OpenBracketMarkup(OpenBracket):
    def changeState(self, state):
        state.enter(MarkupParser)


class CloseBracketMarkup(CloseBracket):
    pass


class Repeat(Command):
    rx = r"\\repeat(?![A-Za-z])"
    def changeState(self, state):
        state.enter(RepeatParser)
    
    
class RepeatSpecifier(Repeat):
    rx = r"\b(volta|unfold|percent|tremolo)(?![A-Za-z])"
    

class RepeatStringSpecifier(String, Repeat):
    rx = r'"(volta|unfold|percent|tremolo)"'
    

class RepeatCount(Value, Leaver):
    rx = r"\d+"


class UserCommand(Token):
    rx = r"\\[A-Za-z]+(?![A-Za-z])"
    
    
class SchemeStart(Item):
    rx = "#"
    def changeState(self, state):
        import scheme
        state.enter(scheme.SchemeParser, 1)


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
        state.enter(LilyPondParserChord)


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
    pass

# basic stuff that can appear everywhere
lilypond_base_items = (
    Space,
    BlockCommentStart,
    LineComment,
    SchemeStart,
    StringQuotedStart,
)


# items that occur in toplevel, book, bookpart or score
# no Leave-tokens!
lilypond_toplevel_base_items = lilypond_base_items + (
    Keyword,
    Markup,
    MarkupLines,
    Repeat,
    Fraction,
    Command,
    UserCommand,
    SequentialStart,
    SimultaneousStart,
    Context,
    Grob,
)


# items that occur in music expressions
lilypond_music_items = lilypond_base_items + (
    Keyword,
    Markup,
    MarkupLines,
    Repeat,
    Dynamic,
    Skip,
    Rest,
    Note,
    Fraction,
    DurationStart,
    Command,
    UserCommand,
    VoiceSeparator,
    SequentialStart, SequentialEnd,
    SimultaneousStart, SimultaneousEnd,
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
    

# items that occur inside chords
lilypond_music_chord_items = (
    ErrorInChord,
    ChordEnd,
) + lilypond_music_items



class LilyPondParserGlobal(LilyPondParser):
    """Parses LilyPond from the toplevel of a file."""
    # TODO: implement assignments
    items = lilypond_toplevel_base_items


class LilyPondParserScore(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketScore,
    ) + lilypond_toplevel_base_items


class LilyPondParserExpectScore(LilyPondParser):
    argcount = 1
    default = Error
    items = (
        Space,
        OpenBracketScore,
    )
        

class LilyPondParserMusic(LilyPondParser):
    """Parses LilyPond music expressions."""
    items = lilypond_music_items
    

class LilyPondParserChord(LilyPondParserMusic):
    """LilyPond inside chords < >"""
    items = lilypond_music_chord_items


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
    items =  (
        MarkupScore,
        MarkupCommand,
        OpenBracketMarkup,
        CloseBracketMarkup,
        MarkupWord,
    ) + lilypond_base_items


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


    
    