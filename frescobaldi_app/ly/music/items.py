# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2014 - 2014 by Wilbert Berendsen
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
The items a read music expression is constructed with.

Whitespace and comments are left out.

"""

from __future__ import unicode_literals

import itertools
from fractions import Fraction
import re

import node

import ly.duration
import ly.pitch
import ly.lex.lilypond
import ly.lex.scheme


class Item(node.WeakNode):
    """Represents any item in the music of a document.
    
    This can be just a token, or an interpreted construct such as a note,
    rest or sequential or simultaneous construct , etc.
    
    Some Item instances just have one responsible token, but others have a
    list or tuple to tokens.
    
    An Item also has a pointer to the Document it originates from.
    
    """
    document = None
    tokens = ()
    token = None


class Root(Item):
    """The root node of a tree of Items.
    
    This is returned by the tree() method.
    
    """


class Token(Item):
    """Any token that is not otherwise recognized""" 


class Container(Item):
    """An item having a list of child items."""


class Duration(Item):
    """A duration"""
    base_scaling = None, None   # two Fractions
    
    def fraction(self):
        """Returns base and scaling multiplied, as one Fraction."""
        base, scaling = self.base_scaling
        return base * scaling


class Durable(Item):
    """An Item that has a Duration attribute."""
    duration = None
    
    def length(self):
        """Return the duration or None (no duration)."""
        if self.duration:
            base, scaling = self.duration.base_scaling
            return base * scaling

    def base_scaling(self):
        """Return the base and scaling fractions (if set, else None)."""
        if self.duration:
            return self.duration.base_scaling


class Chord(Durable, Container):
    pass


class Note(Durable):
    """A Note that has a ly.pitch.Pitch"""
    pitch = None


class Skip(Durable):
    pass


class Rest(Durable):
    pass


class Q(Durable):
    pass


class Music(Container):
    """Any music expression, to be inherited of."""
    def child_length_iter(self, children=None):
        """Yield the length() of all the children, if Music or Durable.
        
        If children is not given, self is iterated over.
        
        """
        return (c.length() or 0 for c in children or self if isinstance(c, (Music, Durable)))
        
    def length(self):
        return sum(self.child_length_iter())


class MusicList(Music):
    """A music expression, either << >> or { }."""
    simultaneous = False
    
    def length(self):
        gen = self.child_length_iter()
        return max(gen) if self.simultaneous else sum(gen)


class Scaler(Music):
    """A music construct that scales the duration of its contents."""
    scaling = 1
    
    def length(self):
        return super(Scaler, self).length() * self.scaling


class Grace(Music):
    """Music that has grace timing, i.e. 0 as far as computation is concerned."""
    def length(self):
        return 0


class AfterGrace(Music):
    """The \afterGrace function with its two arguments.
    
    Only the duration of the first is counted.
    
    """
    def length(self):
        for length in self.child_length_iter():
            return length


class Relative(Music):
    """A \\relative music expression. Has one or two children (Note, Music)."""
    pass


class Absolute(Music):
    """An \\absolute music expression. Has one child (normally Music)."""
    pass


class Transpose(Music):
    """A \\transpose music expression. Has normally three children (Note, Note, Music)."""


class Repeat(Music):
    """A \\repeat expression."""
    def specifier(self):
        if isinstance(self._specifier, Scheme):
            return self._specifier.get_string()
        elif isinstance(self._specifier, String):
            return self._specifier.value()
        return self._specifier
    
    def repeat_count(self):
        if isinstance(self._repeat_count, Scheme):
            return self._repeat_count.get_int() or 1
        return int(self._repeat_count or '1') or 1

    def length(self):
        """Return the length of this music expression.
        
        If the specifier is not "volta", the length is multiplied 
        by the repeat_count value.
        
        If the last child is an Alternative item, its contents are taken
        into account.
        
        """
        unfold = self.specifier() != "volta"
        count = self.repeat_count()
        own_length_iter = self
        alt_length = 0
        if len(self) > 0:
            alt = self[-1]
            if isinstance(alt, Alternative):
                own_length_iter = self[:-1]
                alt_lengths = alt.lengths()
                if alt_lengths:
                    if unfold:
                        alt_lengths[0:0] = [alt_lengths[0]] * (count - len(alt_lengths))
                    alt_length = sum(alt_lengths[:count])
        own_length = sum(self.child_length_iter(own_length_iter))
        if unfold:
            length *= count
        return own_length + alt_length


class Alternative(Music):
    """An \\alternative expression."""
    def length(self):
        """Return the maximum length of the child music lists."""
        return max(self.lengths() or [0])
    
    def lengths(self):
        """A list of length Fractions for every child music item."""
        for item in self:
            if isinstance(item, MusicList):
                return list(item.child_length_iter())
        return []


class InputMode(Music):
    """Base class for inputmode-changing commands."""


class NoteMode(InputMode):
    """A \\notemode or \\notes expression."""


class ChordMode(InputMode):
    """A \\chordmode or \\chords expression."""


class DrumMode(InputMode):
    """A \\drummode or \\drums expression."""


class FigureMode(InputMode):
    """A \\figuremode or \\figures expression."""


class LyricMode(InputMode):
    """A \\lyricmode, \\lyrics or \\addlyrics expression."""


class LyricsTo(InputMode):
    """A \\lyricsto expression."""
    _context_id = None
    
    def context_id(self):
        if isinstance(self._context_id, String):
            return self._context_id.value()
        elif isinstance(self._context_id, Scheme):
            return self._context_id.get_string()
        return self._context_id


class LyricText(Durable):
    """A lyric text (word, markup or string), with a Duration."""


class LyricItem(Item):
    """Another lyric item (skip, extender, hyphen or tie)."""


class ChordSpecifier(Item):
    """Chord specifications after a note in chord mode.
    
    Has children of Note or ChordItem class.
    
    """


class ChordItem(Item):
    """An item inside a ChordSpecifier, e.g. a number or modifier."""


class Tremolo(Item):
    """A tremolo item ":". The duration attribute may be a Duration or None."""
    duration = None


class Translator(Item):
    """Base class for a \\change, \\new, or \\context music expression."""
    _context = None
    _context_id = None
    
    def context(self):
        return self._context
    
    def context_id(self):
        """The context id, if specified after an equal sign."""
        if isinstance(self._context_id, String):
            return self._context_id.value()
        return self._context_id


class Context(Translator, Music):
    """A \\new or \\context music expression."""


class Change(Translator):
    """A \\change music expression."""


class Tempo(Item):
    duration = None
    _text = None
    _tempo = ()
    
    def fraction(self):
        """Return the note value as a fraction given before the equal sign."""
        if self.duration:
            return self.duration.base_scaling[0]
            
    def text(self):
        """Return the text, if set. Can be Markup, Scheme, or String."""
        return self._text
    
    def tempo(self):
        """Return a list of integer values describing the tempo or range."""
        result = []
        for i in self._tempo:
            if isinstance(i, Scheme):
                v = i.get_int()
                if v is not None:
                    result.append(v)
            else:
                result.append(int(i))
        return result


class TimeSignature(Item):
    """A \\time command."""
    _num = 4
    _fraction = Fraction(1, 4)

    def measure_length(self):
        """The length of one measure in this time signature as a Fraction."""
        return self._num * self._fraction
    
    def numerator(self):
        """The upper number (e.g. for 3/2 it returns 3)."""
        return self._num
    
    def fraction(self):
        """The lower number as a Fraction (e.g. for 3/2 it returns 1/2)."""
        return self._fraction


class Partial(Item):
    """A \\partial command."""
    duration = None

    def length(self):
        """Return the duration given as argument as a Fraction."""
        if self.duration:
            base, scaling = self.duration.base_scaling
            return base * scaling


class Clef(Item):
    """A \\clef item."""
    _specifier = None
    
    def specifier(self):
        if isinstance(self._specifier, String):
            return self._specifier.value()
        return self._specifier

        
class KeySignature(Item):
    """A \\key pitch \\mode command."""
    def pitch(self):
        """The ly.pitch.Pitch that denotes the pitch."""
        for i in self.find(Note):
            return i.pitch
    
    def mode(self):
        """The mode, e.g. "major", "minor", etc."""
        for i in self.find(Command):
            return i.token[1:]


class StringTuning(Item):
    """A \\stringTuning command (with a chord as argument)."""


class Keyword(Item):
    """A LilyPond keyword."""


class Command(Item):
    """A LilyPond command."""


class UserCommand(Music):
    """A user command, most probably referring to music."""
    def name(self):
        """Return the name of this user command (without the \\)."""
        return self.token[1:]


class Version(Item):
    """A \\version command."""
    def version_string(self):
        """The version as a string."""
        for i in self:
            if isinstance(i, String):
                return i.value()
            elif isinstance(i, Scheme):
                return i.get_string()
        return ''

    def version(self):
        """The version as a tuple of ints."""
        return tuple(map(int, re.findall(r'\d+', self.version_string())))


class Include(Item):
    """An \\include command (not changing the language)."""
    def filename(self):
        """Returns the filename."""
        for i in self:
            if isinstance(i, String):
                return i.value()
            elif isinstance(i, Scheme):
                return i.get_string()


class Language(Item):
    """A command (\\language or certain \\include commands) that changes the pitch language."""
    language = None


class Markup(Item):
    """A command starting markup (\markup, -lines and -list)."""


class MarkupCommand(Item):
    """A markup command, such as \italic etc."""


class MarkupScore(Item):
    """A \sore inside Markup."""


class MarkupList(Item):
    """The group of markup items inside { and }. NOTE: *not* a \markuplist."""


class MarkupWord(Item):
    """A MarkupWord token."""


class Assignment(Item):
    """A variable = value construct."""
    def name(self):
        """The variable name."""
        return self.token
    
    def value(self):
        """The assigned value."""
        return self[-1]


class Book(Container):
    """A \\book { ... } construct."""


class BookPart(Container):
    """A \\bookpart { ... } construct."""


class Score(Container):
    """A \\score { ... } construct."""


class Header(Container):
    """A \\header { ... } construct."""


class Paper(Container):
    """A \\paper { ... } construct."""


class Layout(Container):
    """A \\layout { ... } construct."""


class Midi(Container):
    """A \\midi { ... } construct."""


class LayoutContext(Container):
    """A \\context { ... } construct within Layout or Midi."""


class With(Container):
    """A \\with ... construct."""


class Set(Item):
    """A \\set command."""
    def context(self):
        """The context, if specified."""
        for t in self.tokens:
            if isinstance(t, ly.lex.lilypond.ContextName):
                return t
    
    def property(self):
        """The property."""
        for t in self.tokens:
            if isinstance(t, ly.lex.lilypond.ContextProperty):
                return t
        for t in self.tokens[::-1]:
            if isinstance(t, ly.lex.lilypond.Name):
                return t
        
    def value(self):
        """The value, given as argument. This is simply the child element."""
        for i in self:
            return i


class Unset(Item):
    """An \\unset command."""
    def context(self):
        """The context, if specified."""
        for t in self.tokens:
            if isinstance(t, ly.lex.lilypond.ContextName):
                return t
    
    def property(self):
        """The property."""
        for t in self.tokens:
            if isinstance(t, ly.lex.lilypond.ContextProperty):
                return t
        for t in self.tokens[::-1]:
            if isinstance(t, ly.lex.lilypond.Name):
                return t


class Override(Item):
    """An \\override command."""
    def context(self):
        for i in self:
            if isinstance(i.token, ly.lex.lilypond.ContextName):
                return i.token
    
    def grob(self):
        for i in self:
            if isinstance(i.token, ly.lex.lilypond.GrobName):
                return i.token


class Revert(Item):
    """A \\revert command."""
    def context(self):
        for i in self:
            if isinstance(i.token, ly.lex.lilypond.ContextName):
                return i.token
    
    def grob(self):
        for i in self:
            if isinstance(i.token, ly.lex.lilypond.GrobName):
                return i.token


class PathItem(Item):
    """An item in the path of an \\override or \\revert command."""


class String(Item):
    """A double-quoted string."""
    
    def value(self):
        return ''.join(
            t[1:] if isinstance(t, ly.lex.Character) and t.startswith('\\') else t
            for t in self.tokens[:-1])


class Number(Item):
    """A numerical value, directly entered."""
    def value(self):
        if isinstance(self.token, ly.lex.lilypond.IntegerValue):
            return int(self.token)
        elif isinstance(self.token, ly.lex.lilypond.DecimalValue):
            return float(self.token)
        elif isinstance(self.token, ly.lex.lilypond.Fraction):
            return Fraction(self.token)
        elif self.token.isdigit():
            return int(self.token)


class Scheme(Item):
    """A Scheme expression inside LilyPond."""
    def get_pair_ints(self):
        """Very basic way to get two integers specified as a pair."""
        result = [int(i.token) for i in self.find(SchemeItem) if i.token.isdigit()]
        if len(result) >= 2:
            return tuple(result[:2])
    
    def get_int(self):
        """A basic way to get one integer value."""
        for i in self.find(SchemeItem):
            if i.token.isdigit():
                return int(i.token)

    def get_string(self):
        """A basic way to get a quoted string value (without the quotes)."""
        return ''.join(i.value() for i in self.find(String))


class SchemeItem(Item):
    """Any scheme token."""


class SchemeList(Container):
    """A ( ... ) expression."""


class SchemeQuote(Item):
    """A ' in scheme."""


class SchemeLily(Container):
    """A music expression inside #{ and #}."""



def skip(source, what=(ly.lex.Space, ly.lex.Comment)):
    """Yield tokens from source, skipping items of classes specified in what.
    
    By default, comments and whitespace are skipped.
    
    """
    for t in source:
        if not isinstance(t, what):
            yield t


def dispatch(what, *args):
    """Decorator to dispatch commands, keywords, classes, etc."""
    read_arg = (lambda c: c.__name__) if isinstance(args[0], type) else None
    def wrapper(func):
        for a in args:
            what[a] = func
        if not func.__doc__:
            func.__doc__ = "handle " + ", ".join(map(read_arg, args))
        return func
    return wrapper


class Reader(object):
    """Reads tokens from a Source and builds a meaningful tree stucture."""
    
    _commands = {}
    _keywords = {}
    _tokencls = {}
    
    def __init__(self, source):
        """Initialize with a ly.document.Source.
        
        The language is set to "nederlands".
        
        """
        self.source = source
        self.language = "nederlands"
        self.in_chord = False
        self.prev_duration = Fraction(1, 4), 1
    
    def set_language(self, lang):
        """Changes the pitch name language to use.
        
        Called internally when \language or \include tokens are encoutered
        with a valid language name/file.
        
        Sets the language attribute to the language name.
        
        """
        if lang in ly.pitch.pitchInfo:
            self.language = lang
            return True

    def add_duration(self, item, token=None, source=None):
        """Add a duration attribute to the item."""
        source = source or self.source
        d = item.duration = self.factory(Duration)
        tokens = []
        if not token or isinstance(token, ly.lex.lilypond.Duration):
            if token:
                tokens.append(token)
            for token in source:
                if isinstance(token, ly.lex.lilypond.Duration):
                    tokens.append(token)
                elif not isinstance(token, ly.lex.Space):
                    self.source.pushback()
                    break
        if tokens:
            d.tokens = tuple(tokens)
            d.base_scaling = self.prev_duration = ly.duration.base_scaling(tokens)
        else:
            d.base_scaling = self.prev_duration
    
    def consume(self, last_token=None):
        """Yield the tokens from our source until a parser is exit.
        
        If last_token is given, it is called with the last token that is read.
        
        """
        t = None
        for t in self.source.until_parser_end():
            yield t
        if last_token and t is not None:
            last_token(t)

    def factory(self, cls, token=None, consume=False):
        """Create Item instance for token.
        
        If consume is True, consume()s the source into item.tokens.
        
        """
        item = cls()
        item.document = self.source.document
        item.token = token
        if consume:
            item.tokens = tuple(self.consume())
        return item
    
    def add_bracketed(self, item, source):
        """Append the arguments between brackets to the item.
        
        Returns True if that succeeded, else False.
        
        """
        for t in source:
            if isinstance(t, ly.lex.lilypond.OpenBracket):
                tokens = [t]
                item.extend(self.read(self.consume(tokens.append)))
                item.tokens = tuple(tokens)
                return True
            elif not isinstance(t, ly.lex.Space):
                self.source.pushback()
                break
        return False
        
    def tree(self):
        """Return a Root node with all the Item instances, read from the source."""
        root = self.factory(Root)
        root.extend(i for i in self.read())
        return root

    def read(self, source=None):
        """Yield Item instances reading from source."""
        source = source or self.source
        for t in skip(source):
            item = self.read_item(t, source)
            if item:
                yield item
    
    def read_item(self, t, source=None):
        """Return one Item that starts with token t. May return None."""
        for c in t.__class__.__mro__:
            try:
                meth = self._tokencls[c]
            except KeyError:
                if c == ly.lex.Token:
                    break
                continue
            return meth(self, t, source or self.source)
    
    @dispatch(_tokencls, ly.lex.lilypond.SchemeStart)
    def handle_scheme_start(self, t, source):
        return self.read_scheme_item(t)
    
    @dispatch(_tokencls, ly.lex.StringStart)
    def handle_string_start(self, t, source):
        return self.factory(String, t, True)
    
    @dispatch(_tokencls, 
        ly.lex.lilypond.DecimalValue,
        ly.lex.lilypond.IntegerValue,
        ly.lex.lilypond.Fraction,
    )
    def handle_number_class(self, t, source):
        return self.factory(Number, t)
    
    @dispatch(_tokencls, ly.lex.lilypond.MusicItem)
    def handle_music_item(self, t, source):
        return self.read_music_item(t, source)
    
    @dispatch(_tokencls, ly.lex.lilypond.ChordStart)
    def handle_chord_start(self, t, source):
        if not self.in_chord:
            self.in_chord = True
            chord = self.factory(Chord, t)
            def last(t): chord.tokens += (t,)
            chord.extend(self.read(self.consume(last)))
            self.in_chord = False
            self.add_duration(chord, None, source)
            return chord
    
    @dispatch(_tokencls, 
        ly.lex.lilypond.OpenBracket, ly.lex.lilypond.OpenSimultaneous,
        ly.lex.lilypond.SimultaneousOrSequentialCommand,
    )
    def handle_music_list(self, t, source):
        item, it = self.test_music_list(t)
        if item:
            if it:
                item.extend(self.read(it))
            return item
    
    @dispatch(_tokencls, ly.lex.lilypond.Command)
    def read_command(self, t, source):
        """Read the rest of a command given in t from the source."""
        try:
            meth = self._commands[t]
        except KeyError:
            item = self.factory(Command, t)
            return item
        return meth(self, t, source)
    
    @dispatch(_tokencls, ly.lex.lilypond.Keyword)
    def read_keyword(self, t, source):
        """Read the rest of a keyword given in t from the source."""
        try:
            meth = self._keywords[t]
        except KeyError:
            item = self.factory(Keyword, t)
            return item
        return meth(self, t, source)
    
    @dispatch(_tokencls, ly.lex.lilypond.UserCommand)
    def read_user_command(self, t, source):
        """Read a user command, this can be a variable reference."""
        return self.factory(UserCommand, t)
    
    @dispatch(_tokencls, ly.lex.lilypond.ChordSeparator)
    def handle_chord_separator(self, t, source):
        return self.read_chord_specifier(t)
    
    @dispatch(_tokencls, ly.lex.lilypond.TremoloColon)
    def handle_tremolo_colon(self, t, source):
        return self.read_tremolo(t)
    
    @dispatch(_tokencls, ly.lex.lilypond.Name)
    def handle_name(self, t, source):
        if self.source.state.depth() < 2:
            return self.read_assignment(t)
    
    @dispatch(_tokencls, 
        ly.lex.lilypond.PaperVariable,
        ly.lex.lilypond.LayoutVariable,
        ly.lex.lilypond.HeaderVariable,
        ly.lex.lilypond.UserVariable,
    )
    def handle_variable_assignment(self, t, source):
        item = self.read_assignment(t)
        if item:
            # handle \pt, \in etc.
            for t in skip(self.source):
                if isinstance(t, ly.lex.lilypond.Unit):
                    item.append(self.factory(Command, t))
                else:
                    self.source.pushback()
                break
            return item
                
    def read_assignment(self, t):
        """Read an assignment from the variable name. May return None."""
        for t1 in skip(self.source):
            if isinstance(t1, ly.lex.lilypond.EqualSign):
                item = self.factory(Assignment, t)
                item.tokens = (t1,)
                for i in self.read():
                    item.append(i)
                    return item
            else:
                self.source.pushback()
            break
    
    def test_music_list(self, t):
        """Test whether a music list ({ ... }, << ... >>, starts here.
        
        Also handles \\simultaneous { ... } and \\sequential { ... } 
        correctly. These obscure commands are not even highlighted by 
        ly.lex, but they exist in LilyPond... \\\simultaneous { ... } is 
        like << ... >> but \\sequential << ... >> just behaves like << ... >>

        Returns a two-tuple(item; iterable), both may be None. If 
        item is not None, it can be either a UserCommand or a MusicList.  If 
        iterable is None, the item is a UserCommand (namely \\simultaneous 
        or \\sequential, but not followed by a { or <<); else the item is a 
        MusicList, and the iterable should be read fully to get all the 
        tokens inside the MusicList. If item is None, there is no MusicList 
        and no token is read.
        
        This way you can handle the { ... } and << ... >> transparently in every
        input mode.
        
        """
        def make_music_list(t, simultaneous, tokens=()):
            """Make the MusicList item."""
            item = self.factory(MusicList, t)
            item.simultaneous = simultaneous
            item.tokens = tokens
            def last(t): item.tokens += (t,)
            return item, self.consume(last)
            
        if isinstance(t, (ly.lex.lilypond.OpenBracket, ly.lex.lilypond.OpenSimultaneous)):
            return make_music_list(t, t == '<<')
        elif isinstance(t, ly.lex.lilypond.SimultaneousOrSequentialCommand):
            for t1 in skip(self.source):
                if isinstance(t1, (ly.lex.lilypond.OpenBracket, ly.lex.lilypond.OpenSimultaneous)):
                    return make_music_list(t, t == '\\simultaneous' or t1 == '<<', (t1,))
                else:
                    self.source.pushback()
                    return self.factory(Keyword, t), None
        return None, None
                    
    def read_music_item(self, t, source):
        """Read one music item (note, rest, s, \skip, or q) from t and source."""
        item = None
        in_pitch_command = isinstance(self.source.state.parser(), ly.lex.lilypond.ParsePitchCommand)
        if t.__class__ == ly.lex.lilypond.Note:
            r = ly.pitch.pitchReader(self.language)(t)
            if r:
                item = self.factory(Note, t)
                p = item.pitch = ly.pitch.Pitch(*r)
                for t in source:
                    if isinstance(t, ly.lex.lilypond.Octave):
                        p.octave = ly.pitch.octaveToNum(t)
                        item.octave_token = t
                    elif isinstance(t, ly.lex.lilypond.Accidental):
                        item.accidental_token = p.accidental = t
                    elif isinstance(t, ly.lex.lilypond.OctaveCheck):
                        p.octavecheck = ly.pitch.octaveToNum(t)
                        item.octavecheck_token = t
                        break
                    elif not isinstance(t, ly.lex.Space):
                        self.source.pushback()
                        break
        else:
            cls = {
                ly.lex.lilypond.Rest: Rest,
                ly.lex.lilypond.Skip: Skip,
                ly.lex.lilypond.Spacer: Skip,
                ly.lex.lilypond.Q: Q,
            }[t.__class__]
            item = self.factory(cls, t)
        if item:
            if not self.in_chord and not in_pitch_command:
                self.add_duration(item, None, source)
        return item
    
    def read_chord_specifier(self, t):
        """Read stuff behind notes in chordmode."""
        item = self.factory(ChordSpecifier)
        item.append(self.factory(ChordItem, t))
        for t in self.consume():
            if isinstance(t, ly.lex.lilypond.ChordItem):
                item.append(self.factory(ChordItem, t))
            elif isinstance(t, ly.lex.lilypond.Note):
                r = ly.pitch.pitchReader(self.language)(t)
                if r:
                    note = self.factory(Note, t)
                    note.pitch = ly.pitch.Pitch(*r)
                    item.append(note)
        return item

    def read_tremolo(self, t):
        """Read a tremolo."""
        item = self.factory(Tremolo, t)
        for t in self.source:
            if isinstance(t, ly.lex.lilypond.TremoloDuration):
                item.duration = self.factory(Duration)
                item.duration.token = t
                item.duration.base_scaling = ly.duration.base_scaling_string(t)
            else:
                self.source.pushback()
            break
        return item
    
    @dispatch(_commands, '\\relative')
    def handle_relative(self, t, source):
        item = self.factory(Relative, t)
        # get one pitch and exit on a non-comment
        pitch_found = False
        for i in self.read(source):
            item.append(i)
            if not pitch_found and isinstance(i, Note):
                pitch_found = True
                continue
            break
        return item
    
    @dispatch(_commands, '\\absolute')
    def handle_absolute(self, t, source):
        item = self.factory(Absolute, t)
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @dispatch(_commands, '\\transpose')
    def handle_transpose(self, t, source):
        item = self.factory(Transpose, t)
        # get two pitches
        pitches_found = 0
        for i in self.read(source):
            item.append(i)
            if pitches_found < 2 and isinstance(i, Note):
                pitches_found += 1
                continue
            break
        return item
    
    @dispatch(_commands, '\\clef')
    def handle_clef(self, t, source):
        item = self.factory(Clef, t)
        for t in skip(source):
            if isinstance(t, ly.lex.lilypond.ClefSpecifier):
                item._specifier = t
            elif isinstance(t, ly.lex.StringStart):
                item._specifier = self.factory(String, t, True)
            break
        return item
    
    @dispatch(_commands, '\\key')
    def handle_key(self, t, source):
        item = self.factory(KeySignature, t)
        item.extend(itertools.islice(self.read(source), 2))
        return item
    
    @dispatch(_commands, '\\times', '\\tuplet', '\\scaleDurations')
    def handle_scaler(self, t, source):
        item = self.factory(Scaler, t)
        item.scaling = 1
        if t == '\\scaleDurations':
            for i in self.read(source):
                item.append(i)
                if isinstance(i, Scheme):
                    pair = i.get_pair_ints()
                    if pair:
                        item.scaling = Fraction(*pair)
                break
        elif t == '\\tuplet':
            for t in source:
                if isinstance(t, ly.lex.lilypond.Fraction):
                    item.scaling = 1 / Fraction(t)
                elif isinstance(t, ly.lex.lilypond.Duration):
                    self.add_duration(item, t, source)
                    break
                elif not isinstance(t, ly.lex.Space):
                    self.source.pushback()
                    break
        else: # t == '\\times'
            for t in source:
                if isinstance(t, ly.lex.lilypond.Fraction):
                    item.scaling = Fraction(t)
                    break
                elif not isinstance(t, ly.lex.Space):
                    self.source.pushback()
                    break
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @dispatch(_commands, '\\grace', '\\acciaccatura', '\\appoggiatura', '\\slashedGrace')
    def handle_grace(self, t, source):
        item = self.factory(Grace, t)
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @dispatch(_commands, '\\afterGrace')
    def handle_after_grace(self, t, source):
        item = self.factory(AfterGrace, t)
        for i in itertools.islice(self.read(source), 2):
            item.append(i)
        return item
    
    @dispatch(_commands, '\\repeat')
    def handle_repeat(self, t, source):
        item = self.factory(Repeat, t)
        item._specifier = None
        item._repeat_count = None
        for t in skip(source):
            if isinstance(t, ly.lex.lilypond.RepeatSpecifier):
                item._specifier = t
            elif not item.specifier and isinstance(t, ly.lex.StringStart):
                item._specifier = self.factory(String, t, True)
            elif isinstance(t, ly.lex.lilypond.RepeatCount):
                item._repeat_count = t
            elif isinstance(t, ly.lex.lilypond.SchemeStart):
                # the specifier or count may be specified using scheme
                s = self.read_scheme_item(t)
                if item._specifier:
                    if item._repeat_count:
                        item.append(s)
                        break
                    item._repeat_count = s
                else:
                    item._specifier = s
            else:
                self.source.pushback()
                for i in self.read(source):
                    item.append(i)
                    break
                for t in skip(source):
                    if t == '\\alternative' and isinstance(t, ly.lex.lilypond.Command):
                        item.append(self.handle_alternative(t, source))
                    else:
                        self.source.pushback()
                    break
                break
        return item
    
    @dispatch(_commands, '\\alternative')
    def handle_alternative(self, t, source):
        item = self.factory(Alternative, t)
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @dispatch(_commands, '\\tempo')
    def handle_tempo(self, t, source):
        item = self.factory(Tempo, t)
        item._text = None
        item._tempo = []
        source = self.consume()
        equal_sign_seen = False
        for t in source:
            if not equal_sign_seen:
                if not item._text:
                    if isinstance(t, ly.lex.lilypond.SchemeStart):
                        item._text = self.read_scheme_item(t)
                    elif isinstance(t, ly.lex.StringStart):
                        item._text = self.factory(String, t, True)
                    elif isinstance(t, ly.lex.lilypond.Markup):
                        item._text = self.handle_markup(t)
                elif isinstance(t, ly.lex.lilypond.Length):
                    self.add_duration(item, t, source)
                elif isinstance(t, ly.lex.lilypond.EqualSign):
                    equal_sign_seen = True
            elif isinstance(t, ly.lex.lilypond.IntegerValue):
                item._tempo.append(t)
            elif isinstance(t, ly.lex.lilypond.SchemeStart):
                item._tempo.append(self.read_scheme_item(t))
        return item
    
    @dispatch(_commands, '\\time')
    def handle_time(self, t, source):
        item = self.factory(TimeSignature, t)
        for t in skip(source):
            if isinstance(t, ly.lex.lilypond.Fraction):
                item._num, den = map(int, t.split('/'))
                item._fraction = Fraction(1, den)
            else:
                self.source.pushback()
            break
        return item
    
    @dispatch(_commands, '\\partial')
    def handle_partial(self, t, source):
        item = self.factory(Partial, t)
        self.add_duration(item, None, source)
        return item
    
    @dispatch(_commands, '\\new', '\\context', '\\change')
    def handle_translator(self, t, source):
        cls = Change if t == '\\change' else Context 
        item = self.factory(cls, t)
        isource = self.consume()
        for t in skip(isource):
            if isinstance(t, (ly.lex.lilypond.ContextName, ly.lex.lilypond.Name)):
                item._context = t
                for t in isource:
                    if isinstance(t, ly.lex.lilypond.EqualSign):
                        for t in isource:
                            if isinstance(t, ly.lex.StringStart):
                                item._context_id = self.factory(String, t, True)
                                break
                            elif isinstance(t, ly.lex.lilypond.Name):
                                item._context_id = t
                                break
                            elif not isinstance(t, ly.lex.Space):
                                self.source.pushback()
                                break
                    elif not isinstance(t, ly.lex.Space):
                        self.source.pushback()
                        break
            else:
                self.source.pushback()
            break
        if cls is not Change:
            for i in self.read(source):
                item.append(i)
                if not isinstance(i, With):
                    break
        return item
    
    _inputmode_commands = {
        '\\notemode': NoteMode,
        '\\notes': NoteMode,
        '\\chordmode': ChordMode,
        '\\chords': ChordMode,
        '\\figuremode': FigureMode,
        '\\figures': FigureMode,
        '\\drummode': DrumMode,
        '\\drums': DrumMode,
    }
    @dispatch(_commands, *_inputmode_commands)
    def handle_inputmode(self, t, source):
        cls = self._inputmode_commands[t]
        item = self.factory(cls, t)
        for i in self.read():
            item.append(i)
            break
        return item
    
    _lyricmode_commands = {
        '\\lyricmode': LyricMode,
        '\\lyrics': LyricMode,
        '\\oldaddlyrics': LyricMode,
        '\\addlyrics': LyricMode,
        '\\lyricsto': LyricsTo,
    }
    @dispatch(_commands, *_lyricmode_commands)
    def handle_lyricmode(self, t, source):
        cls = self._lyricmode_commands[t]
        item = self.factory(cls, t)
        if cls is LyricsTo:
            for t in skip(source):
                if isinstance(t, ly.lex.lilypond.Name):
                    item._context_id = t
                elif isinstance(t, (ly.lex.String, ly.lex.lilypond.SchemeStart)):
                    item._context_id = self.read_item(t)
                else:
                    self.source.pushback()
                break
        for t in skip(self.consume()):
            i = self.read_lyric_item(t) or self.read_item(t)
            item.append(i)
            break
        return item
    
    def read_lyric_item(self, t):
        """Read one lyric item. Returns None for tokens it does not handle."""
        if isinstance(t, (ly.lex.StringStart, ly.lex.lilypond.MarkupStart)):
            item = self.factory(LyricText)
            item.append(self.read_item(t))
            self.add_duration(item)
            return item
        elif isinstance(t, ly.lex.lilypond.LyricText):
            item = self.factory(LyricText, t)
            self.add_duration(item)
            return item
        elif isinstance(t, ly.lex.lilypond.Lyric):
            return self.factory(LyricItem, t)
        else:
            item, source = self.test_music_list(t)
            if item:
                if source:
                    for t in skip(source):
                        i = self.read_lyric_item(t) or self.read_item(t)
                        if i:
                            item.append(i)
                return item
    
    @dispatch(_commands, '\\stringTuning')
    def handle_string_tuning(self, t, source):
        item = self.factory(StringTuning, t)
        for arg in self.read(source):
            item.append(arg)
            break
        return item
    
    @dispatch(_keywords, '\\language')
    def handle_language(self, t, source):
        item = self.factory(Language, t)
        for name in self.read(source):
            item.append(name)
            if isinstance(name, String):
                value = item.language = name.value()
                if value in ly.pitch.pitchInfo:
                    self.language = value
            break
        return item
    
    @dispatch(_keywords, '\\include')
    def handle_include(self, t, source):
        item = None
        name = None
        for name in self.read(source):
            if isinstance(name, String):
                value = name.value()
                if value.endswith('.ly') and value[:-3] in ly.pitch.pitchInfo:
                    item = self.factory(Language, t)
                    item.language = self.language = value[:-3]
                    item.append(name)
            break
        if not item:
            item = self.factory(Include, t)
            if name:
                item.append(name)
        return item
    
    @dispatch(_keywords, '\\version')
    def handle_version(self, t, source):
        item = self.factory(Version, t)
        for arg in self.read(source):
            item.append(arg)
            break
        return item
    
    _bracketed_keywords = {
        '\\header': Header,
        '\\score': Score,
        '\\bookpart': BookPart,
        '\\book': Book,
        '\\paper': Paper,
        '\\layout': Layout,
        '\\midi': Midi,
        '\\with': With,
        '\\context': LayoutContext,
    }
    @dispatch(_keywords, *_bracketed_keywords)
    def handle_bracketed(self, t, source):
        cls = self._bracketed_keywords[t]
        item = self.factory(cls, t)
        if not self.add_bracketed(item, source) and t == '\\with':
            # \with also supports one other argument instead of { ... }
            for i in self.read(source):
                item.append(i)
                break
        return item
    
    @dispatch(_keywords, '\\set')
    def handle_set(self, t, source):
        item = self.factory(Set, t)
        tokens = []
        for t in skip(source):
            tokens.append(t)
            if isinstance(t, ly.lex.lilypond.EqualSign):
                item.tokens = tuple(tokens)
                for i in self.read(source):
                    item.append(i)
                    break
                break
        return item
    
    @dispatch(_keywords, '\\unset')
    def handle_unset(self, t, source):
        item = self.factory(Unset, t)
        tokens = []
        for t in skip(self.consume()):
            if type(t) not in ly.lex.lilypond.ParseUnset.items:
                self.source.pushback()
                break
            tokens.append(t)
        item.tokens = tuple(tokens)
        return item
    
    @dispatch(_keywords, '\\override')
    def handle_override(self, t, source):
        item = self.factory(Override, t)
        for t in skip(self.consume()):
            if isinstance(t, (ly.lex.StringStart, ly.lex.lilypond.SchemeStart)):
                item.append(self.read_item(t))
            elif isinstance(t, ly.lex.lilypond.EqualSign):
                item.tokens = (t,)
                for i in self.read():
                    item.append(i)
                    break
                break
            else:
                item.append(self.factory(PathItem, t))
        return item
    
    @dispatch(_keywords, '\\revert')
    def handle_revert(self, t, source):
        item = self.factory(Revert, t)
        t = None
        for t in skip(self.consume()):
            if type(t) in ly.lex.lilypond.ParseRevert.items:
                item.append(self.factory(PathItem, t))
            else:
                break
        if isinstance(t, ly.lex.lilypond.SchemeStart) and not any(
                isinstance(i.token, ly.lex.lilypond.GrobProperty) for i in item):
            item.append(self.read_scheme_item(t))
        else:
            self.source.pushback()
        return item
    
    @dispatch(_commands, '\\markup', '\\markuplist', '\\markuplines')
    def handle_markup(self, t, source=None):
        item = self.factory(Markup, t)
        self.add_markup_arguments(item)
        return item
        
    def read_markup(self, t):
        """Read LilyPond markup (recursively)."""
        if isinstance(t, ly.lex.lilypond.MarkupScore):
            item = self.factory(MarkupScore, t)
            for t in self.consume():
                if isinstance(t, ly.lex.lilypond.OpenBracket):
                    item.tokens = (t,)
                    def last(t): item.tokens += (t,)
                    item.extend(self.read(self.consume(last)))
                    return item
                elif not isinstance(t, ly.lex.Space):
                    self.source.pushback()
                    break
            return item
        elif isinstance(t, ly.lex.lilypond.MarkupCommand):
            item = self.factory(MarkupCommand, t)
        elif isinstance(t, ly.lex.lilypond.OpenBracketMarkup):
            item = self.factory(MarkupList, t)
        elif isinstance(t, ly.lex.lilypond.MarkupWord):
            return self.factory(MarkupWord, t)
        elif isinstance(t, ly.lex.lilypond.SchemeStart):
            return self.read_scheme_item(t)
        elif isinstance(t, ly.lex.StringStart):
            return self.factory(String, t, True)
        else:
            return None
        self.add_markup_arguments(item)
        return item
    
    def add_markup_arguments(self, item):
        """Add markup arguments to the item."""
        for t in self.consume():
            i = self.read_markup(t)
            if i:
                item.append(i)
            elif isinstance(item, MarkupList) and isinstance(t, ly.lex.lilypond.CloseBracketMarkup):
                item.tokens = (t,)
        return item
    
    def read_scheme_item(self, t):
        """Reads a Scheme expression (just after the # in LilyPond mode)."""
        item = self.factory(Scheme, t)
        for t in self.consume():
            if not isinstance(t, ly.lex.Space):
                i = self.read_scheme(t)
                if i:
                    item.append(i)
                    break
        return item

    def read_scheme(self, t):
        """Return a Scheme item from the token t."""
        if isinstance(t, ly.lex.scheme.Quote):
            item = self.factory(SchemeQuote, t)
            for t in self.consume():
                if not isinstance(t, ly.lex.Space):
                    i = self.read_scheme(t)
                    if i:
                        item.append(i)
                        break
            return item
        elif isinstance(t, ly.lex.scheme.OpenParen):
            item = self.factory(SchemeList, t)
            def last(t): item.tokens = (t,)
            for t in self.consume(last):
                if not isinstance(t, ly.lex.Space):
                    i = self.read_scheme(t)
                    if i:
                        item.append(i)
            return item
        elif isinstance(t, ly.lex.StringStart):
            return self.factory(String, t, True)
        elif isinstance(t, (
            ly.lex.scheme.Bool,
            ly.lex.scheme.Char,
            ly.lex.scheme.Word,
            ly.lex.scheme.Number,
            ly.lex.scheme.Fraction,
            ly.lex.scheme.Float,
            )):
            return self.factory(SchemeItem, t)
        elif isinstance(t, ly.lex.scheme.LilyPondStart):
            item = self.factory(SchemeLily, t)
            def last(t): item.tokens = (t,)
            item.extend(self.read(self.consume(last)))
            return item


