# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Parses and tokenizes LilyPond input.
"""

from __future__ import unicode_literals

import itertools

from . import _token
from . import Parser, FallthroughParser


re_articulation = r"[-_^][_.>|+^-]"
re_dynamic = (
    r"\\[<!>]|"
    r"\\(f{1,5}|p{1,5}"
    r"|mf|mp|fp|spp?|sff?|sfz|rfz"
    r"|cresc|decresc|dim|cr|decr"
    r")(?![A-Za-z])")

re_duration = r"(\\(maxima|longa|breve)\b|(1|2|4|8|16|32|64|128|256|512|1024|2048)(?!\d))"
re_dot = r"\."
re_scaling = r"\*[\t ]*\d+(/\d+)?"


class Variable(_token.Token):
    pass


class UserVariable(_token.Token):
    pass


class Value(_token.Item, _token.Numeric):
    pass


class DecimalValue(Value):
    rx = r"-?\d+(\.\d+)?"


class Fraction(Value):
    rx = r"\d+/\d+"
    
    
class Error(_token.Error):
    pass


class Comment(_token.Comment):
    pass


class BlockCommentStart(Comment, _token.BlockCommentStart, _token.Indent):
    rx = r"%{"
    def update_state(self, state):
        state.enter(ParseBlockComment())


class BlockCommentEnd(Comment, _token.BlockCommentEnd, _token.Leaver, _token.Dedent):
    rx = r"%}"


class BlockCommentSpace(Comment, _token.BlockComment, _token.Space):
    pass


class LineComment(Comment, _token.LineComment):
    rx = r"%.*$"
    

class String(_token.String):
    pass


class StringQuotedStart(String, _token.StringStart):
    rx = r'"'
    def update_state(self, state):
        state.enter(ParseString())
        

class StringQuotedEnd(String, _token.StringEnd):
    rx = r'"'
    def update_state(self, state):
        state.leave()
        state.endArgument()


class StringQuoteEscape(_token.Character):
    rx = r'\\[\\"]'


class Skip(_token.Token):
    rx = r"s(?![A-Za-z])"
    
    
class Rest(_token.Token):
    rx = r"[Rr](?![A-Za-z])"
    
    
class Note(_token.Token):
    rx = r"[a-x]+(?![A-Za-z])"
    

class Octave(_token.Token):
    rx = r",+|'+"


class OctaveCheck(_token.Token):
    rx = r"=(,+|'+)?"


class Accidental(_token.Token):
    pass


class AccidentalReminder(Accidental):
    rx = r"!"


class AccidentalCautionary(Accidental):
    rx = r"\?"


class Duration(_token.Token):
    pass


class Length(Duration):
    rx = re_duration
    def update_state(self, state):
        state.enter(ParseDuration())


class Dot(Duration):
    rx = re_dot
    
    
class Scaling(Duration):
    rx = re_scaling
    
    
class Delimiter(_token.Token):
    pass


class OpenBracket(Delimiter, _token.MatchStart, _token.Indent):
    """An open bracket, does not enter different parser, subclass or reimplement Parser.update_state()."""
    rx = r"\{"
    matchname = "bracket"


class CloseBracket(Delimiter, _token.MatchEnd, _token.Dedent):
    rx = r"\}"
    matchname = "bracket"
    def update_state(self, state):
        state.leave()
        state.endArgument()    
    

class OpenSimultaneous(Delimiter, _token.MatchStart, _token.Indent):
    """An open double French quote, does not enter different parser, subclass or reimplement Parser.update_state()."""
    rx = r"<<"
    matchname = "simultaneous"


class CloseSimultaneous(Delimiter, _token.MatchEnd, _token.Dedent):
    rx = r">>"
    matchname = "simultaneous"
    def update_state(self, state):
        state.leave()
        state.endArgument()
    

class SequentialStart(OpenBracket):
    def update_state(self, state):
        state.enter(ParseMusic())


class SequentialEnd(CloseBracket):
    pass


class SimultaneousStart(OpenSimultaneous):
    def update_state(self, state):
        state.enter(ParseMusic())


class SimultaneousEnd(CloseSimultaneous):
    pass


class PipeSymbol(Delimiter):
    rx = r"\|"


class IntegerValue(Value):
    rx = r"\d+"


class Articulation(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})(?![A-Za-z])".format("|".join(itertools.chain(
            words.articulations,
            words.ornaments,
            words.fermatas,
            words.instrument_scripts,
            words.repeat_scripts,
            words.ancient_scripts,
        )))
    
    
class Direction(Articulation):
    rx = r"[-_^]"
    def update_state(self, state):
        state.enter(ParseScriptAbbreviationOrFingering())


class ScriptAbbreviation(Articulation, _token.Leaver):
    rx = r"[+|>._^-]"


class Fingering(Articulation, _token.Leaver):
    rx = r"\d"


class StringNumber(Articulation):
    rx = r"\\\d+"


class Slur(_token.Token):
    pass


class SlurStart(Slur, _token.MatchStart):
    rx = r"\("
    matchname = "slur"
    

class SlurEnd(Slur, _token.MatchEnd):
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


class Beam(_token.Token):
    pass


class BeamStart(Beam, _token.MatchStart):
    rx = r"\["
    matchname = "beam"


class BeamEnd(Beam, _token.MatchEnd):
    rx = r"\]"
    matchname = "beam"


class Ligature(_token.Token):
    pass


class LigatureStart(Ligature, _token.MatchStart):
    rx = r"\\\["
    matchname = "ligature"
    
    
class LigatureEnd(Ligature, _token.MatchEnd):
    rx = r"\\\]"
    matchname = "ligature"
    
    
class Tremolo(_token.Token):
    pass


class TremoloColon(Tremolo):
    rx = r":"
    def update_state(self, state):
        state.enter(ParseTremolo())


class TremoloDuration(Tremolo, _token.Leaver):
    rx = r"\b(8|16|32|64|128|256|512|1024|2048)(?!\d)"


class ChordItem(_token.Token):
    """Base class for chordmode items."""


class ChordModifier(ChordItem):
    rx = r"((?<![a-z])|^)(aug|dim|sus|min|maj|m)(?![a-z])"


class ChordSeparator(ChordItem):
    rx = r":|\^|/\+?"


class ChordStepNumber(ChordItem):
    rx = r"\d+[-+]?"


class ChordDot(ChordItem):
    rx = r"\."


class Keyword(_token.Item):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})(?![A-Za-z])".format("|".join(words.lilypond_keywords))


class VoiceSeparator(Delimiter):
    rx = r"\\\\"
    

class Dynamic(_token.Token):
    rx = re_dynamic


class Command(_token.Item):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})(?![A-Za-z])".format("|".join(words.lilypond_music_commands))
    

class Specifier(_token.Token):
    # a specifier of a command e.g. the name of clef or repeat style.
    pass


class Score(Keyword):
    rx = r"\\score\b"
    def update_state(self, state):
        state.enter(ExpectScore())
        

class Book(Keyword):
    rx = r"\\book\b"
    def update_state(self, state):
        state.enter(ExpectBook())
        
        
class BookPart(Keyword):
    rx = r"\\bookpart\b"
    def update_state(self, state):
        state.enter(ExpectBookPart())


class Paper(Keyword):
    rx = r"\\paper\b"
    def update_state(self, state):
        state.enter(ExpectPaper())


class Header(Keyword):
    rx = r"\\header\b"
    def update_state(self, state):
        state.enter(ExpectHeader())


class Layout(Keyword):
    rx = r"\\layout\b"
    def update_state(self, state):
        state.enter(ExpectLayout())


class Midi(Keyword):
    rx = r"\\midi\b"
    def update_state(self, state):
        state.enter(ExpectMidi())


class With(Keyword):
    rx = r"\\with\b"
    def update_state(self, state):
        state.enter(ExpectWith())


class LayoutContext(Keyword):
    rx = r"\\context\b"
    def update_state(self, state):
        state.enter(ExpectContext())


class Markup(Command):
    rx = r"\\markup(?![A-Za-z])"
    def update_state(self, state):
        state.enter(ParseMarkup(1))


class MarkupLines(Markup):
    rx = r"\\markuplines(?![A-Za-z])"
    def update_state(self, state):
        state.enter(ParseMarkup(1))


class MarkupList(Markup):
    rx = r"\\markuplist(?![A-Za-z])"
    def update_state(self, state):
        state.enter(ParseMarkup(1))


class MarkupCommand(Markup):
    rx = r"\\[A-Za-z]+(-[A-Za-z]+)*(?![A-Za-z])"
    def update_state(self, state):
        import ly.words
        command = self[1:]
        if command in ly.words.markupcommands_nargs[0]:
            state.endArgument()
        else:
            for argcount in 2, 3, 4, 5:
                if command in ly.words.markupcommands_nargs[argcount]:
                    break
            else:
                argcount = 1
            state.enter(ParseMarkup(argcount))


class MarkupScore(Markup):
    rx = r"\\score\b"
    def update_state(self, state):
        state.enter(ExpectScore())


class MarkupWord(_token.Item):
    rx = r'[^{}"\\\s#%]+'


class OpenBracketMarkup(OpenBracket):
    def update_state(self, state):
        state.enter(ParseMarkup())


class CloseBracketMarkup(CloseBracket):
    def update_state(self, state):
        # go back to the opening bracket, this is the ParseMarkup
        # parser with the 0 argcount
        while state.parser().argcount > 0:
            state.leave()
        state.leave()
        state.endArgument()    


class Repeat(Command):
    rx = r"\\repeat(?![A-Za-z])"
    def update_state(self, state):
        state.enter(ParseRepeat())
    
    
class RepeatSpecifier(Specifier):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})(?![A-Za-z])".format("|".join(words.repeat_types))
    

class RepeatStringSpecifier(String, Specifier):
    @_token.patternproperty
    def rx():
        from .. import words
        return r'"({0})"'.format("|".join(words.repeat_types))
    

class RepeatCount(IntegerValue, _token.Leaver):
    pass


class Override(Keyword):
    rx = r"\\override\b"
    def update_state(self, state):
        state.enter(ParseOverride())


class Set(Override):
    rx = r"\\set\b"
    def update_state(self, state):
        state.enter(ParseSet())
    

class Revert(Override):
    rx = r"\\revert\b"
    def update_state(self, state):
        state.enter(ParseRevert())
    

class DotSetOverride(Delimiter):
    rx = r"\."


class Unset(Keyword):
    rx = r"\\unset\b"
    def update_state(self, state):
        state.enter(ParseUnset())


class Translator(Command):
    def update_state(self, state):
        state.enter(ParseTranslator())


class New(Translator):
    rx = r"\\new\b"


class Context(Translator):
    rx = r"\\context\b"


class Change(Translator):
    rx = r"\\change\b"


class Clef(Command):
    rx = r"\\clef\b"
    def update_state(self, state):
        state.enter(ParseClef())


class ClefSpecifier(Specifier):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.clefs_plain))
    
    def update_state(self, state):
        state.leave()


class PitchCommand(Command):
    rx = r"\\(relative|transpose|transposition|key|octaveCheck)\b"
    def update_state(self, state):
        argcount = 2 if self == '\\transpose' else 1
        state.enter(ParsePitchCommand(argcount))


class Unit(Command):
    rx = r"\\(mm|cm|in|pt)\b"
    

class InputMode(Command):
    pass


class LyricMode(InputMode):
    rx = r"\\(lyricmode|((old)?add)?lyrics|lyricsto)\b"
    def update_state(self, state):
        state.enter(ExpectLyricMode())


class Lyric(_token.Item):
    """Base class for Lyric items."""


class LyricText(Lyric):
    rx = r"[^\\\s\d~\"]+"


class LyricHyphen(Lyric):
    rx = r"--"
    
    
class LyricExtender(Lyric):
    rx = r"__"
    
    
class LyricSkip(Lyric):
    rx = r"_"
    

class LyricTie(Lyric):
    rx = r"~"


class NoteMode(InputMode):
    rx = r"\\(notes|notemode)\b"
    def update_state(self, state):
        state.enter(ExpectNoteMode())


class ChordMode(InputMode):
    rx = r"\\(chords|chordmode)\b"
    def update_state(self, state):
        state.enter(ExpectChordMode())


class DrumMode(InputMode):
    rx = r"\\(drums|drummode)\b"
    def update_state(self, state):
        state.enter(ExpectDrumMode())


class FigureMode(InputMode):
    rx = r"\\(figures|figuremode)\b"
    def update_state(self, state):
        state.enter(ExpectFigureMode())


class UserCommand(_token.Token):
    rx = r"\\[A-Za-z]+(?![A-Za-z])"
    
    
class SchemeStart(_token.Item):
    rx = "[#$](?![{}])"
    def update_state(self, state):
        import scheme
        state.enter(scheme.ParseScheme(1))


class ContextName(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.contexts))
    

class BackSlashedContextName(ContextName):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\\({0})\b".format("|".join(words.contexts))
    
    
class GrobName(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import data
        return r"\b({0})\b".format("|".join(data.grobs()))


class ContextProperty(_token.Token):
    @_token.patternproperty
    def rx():
        from .. import data
        return r"\b({0})\b".format("|".join(data.context_properties()))


class PaperVariable(Variable):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.papervariables))


class HeaderVariable(Variable):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.headervariables))


class LayoutVariable(Variable):
    @_token.patternproperty
    def rx():
        from .. import words
        return r"\b({0})\b".format("|".join(words.layoutvariables))


class Chord(_token.Token):
    """Base class for Chord delimiters."""
    pass


class ChordStart(Chord):
    rx = r"<"
    def update_state(self, state):
        state.enter(ParseChord())


class ChordEnd(Chord, _token.Leaver):
    rx = r">"
    

class ErrorInChord(Error):
    rx = "|".join((
        re_articulation, # articulation
        r"<<|>>", # double french quotes
        r"\\[\\\]\[\(\)()]", # slurs beams
        re_duration, # duration
        re_scaling, # scaling
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
    

class EqualSign(_token.Token):
    rx = r"="
    

class EqualSignSetOverride(EqualSign):
    """An equal sign in a set/override construct."""
    def update_state(self, state):
        state.leave()



# Parsers
class ParseLilyPond(Parser):
    mode = 'lilypond'

# basic stuff that can appear everywhere
space_items = (
    _token.Space,
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
    PitchCommand,
    Override, Revert,
    Set, Unset,
    New, Context, Change,
    With,
    Clef,
    ChordMode, DrumMode, FigureMode, LyricMode, NoteMode,
    Markup, MarkupLines, MarkupList,
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
    Dynamic,
    Skip,
    Rest,
    Note,
    Fraction,
    Length,
    Octave,
    OctaveCheck,
    AccidentalCautionary,
    AccidentalReminder,
    PipeSymbol,
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
    Direction,
    Articulation,
    StringNumber,
    IntegerValue,
) + command_items
    

# items that occur inside chords
music_chord_items = (
    ErrorInChord,
    ChordEnd,
) + music_items



class ParseGlobal(ParseLilyPond):
    """Parses LilyPond from the toplevel of a file."""
    # TODO: implement assignments
    items = (
        Book,
        BookPart,
        Score,
        Markup, MarkupLines, MarkupList,
        Paper, Header, Layout,
    ) + toplevel_base_items + (
        Name,
        EqualSign,
    )


class ExpectOpenBracket(FallthroughParser, ParseLilyPond):
    """Waits for an OpenBracket and then replaces the parser with the class set in the replace attribute.
    
    Subclass this to set the destination for the OpenBracket.
    
    """
    default = Error
    items = space_items + (
        OpenBracket,
    )
    def update_state(self, state, token):
        if isinstance(token, OpenBracket):
            state.replace(self.replace())
        

class ExpectOpenBracketOrSimultaneous(ParseLilyPond):
    """Waits for an OpenBracket or << and then replaces the parser with the class set in the replace attribute.
    
    Subclass this to set the destination for the OpenBracket.
    
    """
    default = Error
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(self.replace())
        

class ParseScore(ParseLilyPond):
    """Parses the expression after \score {, leaving at } """
    items = (
        CloseBracket,
        Header, Layout, Midi, With,
    ) + toplevel_base_items


class ExpectScore(ExpectOpenBracket):
    replace = ParseScore
            

class ParseBook(ParseLilyPond):
    """Parses the expression after \book {, leaving at } """
    items = (
        CloseBracket,
        Markup, MarkupLines, MarkupList,
        BookPart,
        Score,
        Paper, Header, Layout,
    ) + toplevel_base_items



class ExpectBook(ExpectOpenBracket):
    replace = ParseBook


class ParseBookPart(ParseLilyPond):
    """Parses the expression after \bookpart {, leaving at } """
    items = (
        CloseBracket,
        Markup, MarkupLines, MarkupList,
        Score,
        Paper, Header, Layout,
    ) + toplevel_base_items


class ExpectBookPart(ExpectOpenBracket):
    replace = ParseBookPart


class ParsePaper(ParseLilyPond):
    """Parses the expression after \paper {, leaving at } """
    items = base_items + (
        CloseBracket,
        Markup, MarkupLines, MarkupList,
        PaperVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class ExpectPaper(ExpectOpenBracket):
    replace = ParsePaper


class ParseHeader(ParseLilyPond):
    """Parses the expression after \header {, leaving at } """
    items = (
        CloseBracket,
        Markup, MarkupLines, MarkupList,
        HeaderVariable,
        EqualSign,
    ) + toplevel_base_items


class ExpectHeader(ExpectOpenBracket):
    replace = ParseHeader
        

class ParseLayout(ParseLilyPond):
    """Parses the expression after \layout {, leaving at } """
    items = base_items + (
        CloseBracket,
        LayoutContext,
        LayoutVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class ExpectLayout(ExpectOpenBracket):
    replace = ParseLayout
        

class ParseMidi(ParseLilyPond):
    """Parses the expression after \midi {, leaving at } """
    items = base_items + (
        CloseBracket,
        LayoutContext,
        LayoutVariable,
        EqualSign,
        DecimalValue,
        Unit,
    )


class ExpectMidi(ExpectOpenBracket):
    replace = ParseMidi


class ParseWith(ParseLilyPond):
    """Parses the expression after \with {, leaving at } """
    items = (
        CloseBracket,
        ContextProperty,
        EqualSign,
    ) + toplevel_base_items


class ExpectWith(ExpectOpenBracket):
    replace = ParseWith
        

class ParseContext(ParseLilyPond):
    """Parses the expression after (\layout {) \context {, leaving at } """
    items = (
        CloseBracket,
        BackSlashedContextName,
        ContextProperty,
        EqualSign,
    ) + toplevel_base_items


class ExpectContext(ExpectOpenBracket):
    replace = ParseContext
        

class ParseMusic(ParseLilyPond):
    """Parses LilyPond music expressions."""
    items = music_items + (
        TremoloColon,
    )
    

class ParseChord(ParseMusic):
    """LilyPond inside chords < >"""
    items = music_chord_items


class ParseString(Parser):
    default = String
    items = (
        StringQuotedEnd,
        StringQuoteEscape,
    )
    

class ParseBlockComment(Parser):
    default = Comment
    items = (
        BlockCommentSpace,
        BlockCommentEnd,
    )


class ParseMarkup(Parser):
    items =  (
        MarkupScore,
        MarkupCommand,
        OpenBracketMarkup,
        CloseBracketMarkup,
        MarkupWord,
    ) + base_items


class ParseRepeat(FallthroughParser):
    items = space_items + (
        RepeatSpecifier,
        RepeatStringSpecifier,
        RepeatCount,
    )


class ParseDuration(FallthroughParser):
    items = space_items + (
        Dot,
    )
    def fallthrough(self, state):
        state.replace(ParseDurationScaling())
        
        
class ParseDurationScaling(ParseDuration):
    items = space_items + (
        Scaling,
    )
    def fallthrough(self, state):
        state.leave()


class ParseOverride(ParseLilyPond):
    argcount = 0
    items = (
        ContextName,
        DotSetOverride,
        GrobName,
        EqualSignSetOverride,
        Name,
    ) + base_items
    

class ParseRevert(FallthroughParser):
    items = space_items + (
        ContextName,
        DotSetOverride,
        GrobName,
        Name,
        SchemeStart,
    )

    
class ParseSet(ParseLilyPond):
    argcount = 0
    items = (
        ContextName,
        DotSetOverride,
        ContextProperty,
        EqualSignSetOverride,
        Name,
    ) + base_items
    
    
class ParseUnset(FallthroughParser):
    items = space_items + (
        ContextName,
        DotSetOverride,
        ContextProperty,
        Name,
    )
    def update_state(self, state, token):
        if isinstance(token, ContextProperty) or token[:1].islower():
            state.leave()


class ParseTranslator(FallthroughParser):
    items = space_items + (
        ContextName,
        Name,
    )
    
    def update_state(self, state, token):
        if isinstance(token, (Name, ContextName)):
            state.replace(ExpectTranslatorId())


class ExpectTranslatorId(FallthroughParser):
    items = space_items + (
        EqualSign,
    )
    
    def update_state(self, state, token):
        if token == '=':
            state.replace(ParseTranslatorId())


class ParseTranslatorId(FallthroughParser):
    argcount = 1
    items = space_items + (
        Name,
        StringQuotedStart,
    )
    
    def update_state(self, state, token):
        if isinstance(token, Name):
            state.leave()


class ParseClef(FallthroughParser):
    argcount = 1
    items = space_items + (
        ClefSpecifier,
        StringQuotedStart,
    )


class ParseScriptAbbreviationOrFingering(FallthroughParser):
    argcount = 1
    items = space_items + (
        ScriptAbbreviation,
        Fingering,
    )


class ParseInputMode(ParseLilyPond):
    """Base class for parser for mode-changing music commands."""
    
    
class ExpectLyricMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
        SchemeStart,
        StringQuotedStart,
        Name,
    )
    
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(ParseLyricMode())
        

class ParseLyricMode(ParseInputMode):
    """Parser for \\lyrics, \\lyricmode, \\addlyrics, etc."""
    items = base_items + (
        CloseBracket,
        CloseSimultaneous,
        OpenBracket,
        OpenSimultaneous,
        PipeSymbol,
        LyricHyphen,
        LyricExtender,
        LyricSkip,
        LyricTie,
        LyricText,
        Dynamic,
        Skip,
        Length,
        Markup, MarkupLines, MarkupList,
    ) + command_items
    
    def update_state(self, state, token):
        if isinstance(token, (OpenSimultaneous, OpenBracket)):
            state.enter(ParseLyricMode())


class ExpectChordMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(ParseChordMode())
        

class ParseChordMode(ParseInputMode, ParseMusic):
    """Parser for \\chords and \\chordmode."""
    items = (
        OpenBracket,
        OpenSimultaneous,
    ) + music_items + ( # TODO: specify items exactly, e.g. < > is not allowed
        ChordSeparator,
    )
    def update_state(self, state, token):
        if isinstance(token, ChordSeparator):
            state.enter(ParseChordItems())
        elif isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(ParseChordMode())


class ExpectNoteMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(ParseNoteMode())
        

class ParseNoteMode(ParseInputMode, ParseMusic):
    """Parser for \\notes and \\notemode. Same as Music itself."""


class ExpectDrumMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(ParseDrumMode())
        

class ParseDrumMode(ParseInputMode, ParseMusic):
    """Parser for \\drums and \\drummode."""
    # TODO: implement items (see ParseChordMode)
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(ParseDrumMode())


class ExpectFigureMode(FallthroughParser):
    items = space_items + (
        OpenBracket,
        OpenSimultaneous,
    )
    
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.replace(ParseFigureMode())
        

class ParseFigureMode(ParseInputMode, ParseMusic):
    """Parser for \\figures and \\figuremode."""
    # TODO: implement items (see ParseChordMode)
    def update_state(self, state, token):
        if isinstance(token, (OpenBracket, OpenSimultaneous)):
            state.enter(ParseFigureMode())


class ParsePitchCommand(FallthroughParser):
    argcount = 1
    items = space_items + (
        Note,
        Octave,
    )
    def update_state(self, state, token):
        if isinstance(token, Note):
            self.argcount -= 1
        elif isinstance(token, _token.Space) and self.argcount <= 0:
            state.leave()


class ParseTremolo(FallthroughParser):
    items = (TremoloDuration,)


class ParseChordItems(FallthroughParser):
    items = (
        ChordSeparator,
        ChordModifier,
        ChordStepNumber,
        ChordDot,
        Note,
    )


