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
re_dynamic = r"\\(f{1,5}|p{1,5}|mf|mp|fp|spp?|sff?|sfz|rfz)\b|\\[<!>]"

re_duration = r"(\\(maxima|longa|breve)\b|(1|2|4|8|16|32|64|128|256|512|1024|2048)(?!\d))"
re_dot = r"\."
re_scaling = r"\*[\t ]*\d+(/\d+)?"


class Variable(Token):
    pass


class UserVariable(Token):
    pass


class Value(Item, NumericBase):
    pass


class DecimalValue(Value):
    rx = r"-?\d+(\.\d+)?"


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


class OpenBracketBook(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserBook)


class CloseBracketBook(CloseBracket):
    pass


class OpenBracketBookPart(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserBookPart)


class CloseBracketBookPart(CloseBracket):
    pass


class OpenBracketPaper(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserPaper)


class CloseBracketPaper(CloseBracket):
    pass


class OpenBracketHeader(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserHeader)


class CloseBracketHeader(CloseBracket):
    pass


class OpenBracketLayout(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserLayout)


class CloseBracketLayout(CloseBracket):
    pass


class OpenBracketMidi(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserMidi)


class CloseBracketMidi(CloseBracket):
    pass


class OpenBracketWith(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserWith)


class CloseBracketWith(CloseBracket):
    pass


class OpenBracketContext(OpenBracket):
    def changeState(self, state):
        state.enter(LilyPondParserContext)


class CloseBracketContext(CloseBracket):
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
    

class Specifier(Token):
    # a specifier of a command e.g. the name of clef or repeat style.
    pass


class Score(Keyword):
    rx = r"\\score\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectScore)
        

class Book(Keyword):
    rx = r"\\book\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectBook)
        
        
class BookPart(Keyword):
    rx = r"\\bookpart\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectBookPart)


class Paper(Keyword):
    rx = r"\\paper\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectPaper)


class Header(Keyword):
    rx = r"\\header\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectHeader)


class Layout(Keyword):
    rx = r"\\layout\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectLayout)


class Midi(Keyword):
    rx = r"\\midi\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectMidi)


class With(Keyword):
    rx = r"\\with\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectWith)


class LayoutContext(Keyword):
    rx = r"\\context\b"
    def changeState(self, state):
        state.enter(LilyPondParserExpectContext)


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
    
    
class RepeatSpecifier(Specifier):
    rx = r"\b({0})(?![A-Za-z])".format("|".join(words.repeat_types))
    

class RepeatStringSpecifier(String, Specifier):
    rx = r'"({0})"'.format("|".join(words.repeat_types))
    

class RepeatCount(Value, Leaver):
    rx = r"\d+"


class Override(Keyword):
    rx = r"\\override\b"
    def changeState(self, state):
        state.enter(LilyPondParserOverride)


class Set(Override):
    rx = r"\\set\b"
    def changeState(self, state):
        state.enter(LilyPondParserSet)
    

class DotSetOverride(Delimiter):
    rx = r"\."


class Unset(Keyword):
    rx = r"\\unset\b"
    def changeState(self, state):
        state.enter(LilyPondParserUnset)


class New(Command):
    rx = r"\\new\b"
    def changeState(self, state):
        state.enter(LilyPondParserNewContext)
        
        
class Context(New):
    rx = r"\\context\b"
    

class Change(New):
    rx = r"\\change\b"
    
    
class Clef(Command):
    rx = r"\\clef"
    def changeState(self, state):
        state.enter(LilyPondParserClef)


class ClefSpecifier(Specifier):
    rx = r"\b({0})\b".format("|".join(words.clefs_plain))
    

class Unit(Command):
    rx = r"\\(mm|cm|in|pt)\b"
    
    
class UserCommand(Token):
    rx = r"\\[A-Za-z]+(?![A-Za-z])"
    
    
class SchemeStart(Item):
    rx = "#"
    def changeState(self, state):
        import scheme
        state.enter(scheme.SchemeParser, 1)


class ContextName(Token):
    rx = r"\b({0})\b".format("|".join(words.contexts))
    

class BackSlashedContextName(ContextName):
    rx = r"\\({0})\b".format("|".join(words.contexts))
    
    
class GrobName(Token):
    rx = r"\b({0})\b".format("|".join(words.grobs))


class ContextProperty(Token):
    rx = r"\b({0})\b".format("|".join(words.contextproperties))


class PaperVariable(Variable):
    rx = r"\b({0})\b".format("|".join(words.papervariables))


class HeaderVariable(Variable):
    rx = r"\b({0})\b".format("|".join(words.headervariables))


class LayoutVariable(Variable):
    rx = r"\b({0})\b".format("|".join(words.layoutvariables))


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
    

class Name(UserVariable):
    """A variable name without \\ prefix."""
    rx = r"[a-zA-Z]+(?![a-zA-Z])"
    

class NameLower(Name):
    """A lowercase name."""
    rx = r"[a-z]+(?![a-zA-Z])"
    
    
class NameHyphenLower(Name):
    """A lowercase name that may contain hyphens."""
    rx = r"[a-z]+(-[a-z]+)*(!?[-a-zA-Z])"
    

class EqualSign(Token):
    rx = r"="
    

class EqualSignSetOverride(EqualSign):
    """An equal sign in a set/override construct."""
    def changeState(self, state):
        # wait for one more expression, then leave
        state.parser().argcount = 1



# Parsers
class LilyPondParser(Parser):
    pass

# basic stuff that can appear everywhere
space_items = (
    Space,
    BlockCommentStart,
    LineComment,
)    


base_items = space_items + (
    SchemeStart,
    StringQuotedStart,
)


# items that represent commands in both toplevel and music mode
command_items = (
    Repeat,
    Override,
    Set, Unset,
    New, Context,
    With,
    Clef,
    Keyword,
    Command,
    UserCommand,
)


# items that occur in toplevel, book, bookpart or score
# no Leave-tokens!
toplevel_base_items = base_items + (
    Fraction,
    SequentialStart,
    SimultaneousStart,
) + command_items


# items that occur in music expressions
music_items = base_items + (
    Markup,
    MarkupLines,
    Dynamic,
    Skip,
    Rest,
    Note,
    Fraction,
    DurationStart,
    VoiceSeparator,
    SequentialStart, SequentialEnd,
    SimultaneousStart, SimultaneousEnd,
    ChordStart,
    ContextName,
    GrobName,
    SlurStart, SlurEnd,
    PhrasingSlurStart, PhrasingSlurEnd,
    Tie,
    BeamStart, BeamEnd,
    LigatureStart, LigatureEnd,
    Articulation,
) + command_items
    

# items that occur inside chords
music_chord_items = (
    ErrorInChord,
    ChordEnd,
) + music_items



class LilyPondParserGlobal(LilyPondParser):
    """Parses LilyPond from the toplevel of a file."""
    # TODO: implement assignments
    items = (
        Book,
        BookPart,
        Score,
        Markup, MarkupLines,
        Paper, Header, Layout,
    ) + toplevel_base_items + (
        Name,
        EqualSign,
    )


class LilyPondParserExpectScore(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketScore,
    )
        

class LilyPondParserScore(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketScore,
        Header, Layout, Midi, With,
    ) + toplevel_base_items


class LilyPondParserExpectBook(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketBook,
    )
        

class LilyPondParserBook(LilyPondParser):
    """Parses the expression after \book {, leaving at } """
    items = (
        CloseBracketBook,
        Markup, MarkupLines,
        BookPart,
        Score,
        Paper, Header, Layout,
    ) + toplevel_base_items


class LilyPondParserExpectBookPart(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketBookPart,
    )
        

class LilyPondParserBookPart(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketBookPart,
        Markup, MarkupLines,
        Score,
        Header, Layout,
    ) + toplevel_base_items


class LilyPondParserExpectPaper(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketPaper,
    )


class LilyPondParserPaper(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = base_items + (
        CloseBracketPaper,
        Markup, MarkupLines,
        PaperVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class LilyPondParserExpectHeader(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketHeader,
    )
        

class LilyPondParserHeader(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketHeader,
        Markup, MarkupLines,
        HeaderVariable,
        EqualSign,
    ) + toplevel_base_items


class LilyPondParserExpectLayout(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketLayout,
    )
        

class LilyPondParserLayout(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = base_items + (
        CloseBracketLayout,
        LayoutContext,
        LayoutVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class LilyPondParserExpectMidi(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketMidi,
    )
        

class LilyPondParserMidi(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketMidi,
    ) + toplevel_base_items


class LilyPondParserExpectWith(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketWith,
    )
        

class LilyPondParserWith(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketWith,
        ContextProperty,
        EqualSign,
    ) + toplevel_base_items


class LilyPondParserExpectContext(LilyPondParser):
    argcount = 1
    default = Error
    items = space_items + (
        OpenBracketContext,
    )
        

class LilyPondParserContext(LilyPondParser):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracketContext,
        BackSlashedContextName,
        ContextProperty,
        EqualSign,
    ) + toplevel_base_items


class LilyPondParserMusic(LilyPondParser):
    """Parses LilyPond music expressions."""
    items = music_items
    

class LilyPondParserChord(LilyPondParserMusic):
    """LilyPond inside chords < >"""
    items = music_chord_items


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
    ) + base_items


class RepeatParser(FallthroughParser):
    items = space_items + (
        RepeatSpecifier,
        RepeatStringSpecifier,
        RepeatCount,
    )


class DurationParser(FallthroughParser):
    items = space_items + (
        Dot,
    )
    def fallthrough(self, state):
        state.replace(DurationScalingParser)
        
        
class DurationScalingParser(DurationParser):
    items = space_items + (
        Scaling,
    )
    def fallthrough(self, state):
        state.leave()


class LilyPondParserOverride(LilyPondParser):
    argcount = 0
    items = (
        ContextName,
        DotSetOverride,
        GrobName,
        EqualSignSetOverride,
        Name,
        Markup, MarkupLines,
    ) + base_items
    

class LilyPondParserRevert(FallthroughParser):
    items = space_items + (
        ContextName,
        DotSetOverride,
        Name,
        SchemeStart,
    )

    
class LilyPondParserSet(LilyPondParser):
    argcount = 0
    items = (
        Context,
        DotSetOverride,
        ContextProperty,
        EqualSignSetOverride,
        Name,
        Markup, MarkupLines,
    ) + base_items
    
    
class LilyPondParserUnset(FallthroughParser):
    items = space_items + (
        Context,
        DotSetOverride,
        ContextProperty,
        Name,
    )


class LilyPondParserNewContext(FallthroughParser):
    items = space_items + (
        Context,
        Name,
    )


class LilyPondParserClef(FallthroughParser):
    argcount = 1
    items = space_items + (
        ClefSpecifier,
        StringQuotedStart,
    )

