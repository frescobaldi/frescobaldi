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
The items a music expression is constructed with in a tree structure.

Whitespace and comments are left out.

All nodes (instances of Item) have a 'position' attribute that indicates 
where the item starts in the source text. Almost all items have the token 
that starts the expression in the 'token' attribute and possibly other 
tokens in the 'tokens' attribute, as a tuple. 

The 'end_position()' method returns the position where the node (including 
its child nodes) ends.


"""

from __future__ import unicode_literals

import itertools
from fractions import Fraction
import re

import node

import ly.duration
import ly.pitch

from ly import lex
from ly.lex import lilypond
from ly.lex import scheme


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
    position = -1

    def __repr__(self):
        s = ' ' + repr(self.token[:]) if self.token else ''
        return '<{0}{1}>'.format(self.__class__.__name__, s)
    
    def end_position(self):
        """Return the end position of this node."""
        def ends():
            if self.tokens:
                yield self.tokens[-1].end
            elif self.token:
                yield self.token.end
            else:
                yield self.position
            if len(self):
                # end pos of the last child
                yield self[-1].end_position()
            # end pos of Item instances in attributes, such as duration etc
            for i in vars(self).values():
                if isinstance(i, Item):
                    yield i.end_position()
        return max(ends())
        
    def find_trees(self, cls, depth=-1):
        """Yield all descendants (like Node.iter_depth()) that are of cls.
        
        cls may also be a tuple of classes. If a node is yielded, it is not
        further descended into.
        
        """
        def find(node, depth):
            if depth != 0:
                for n in node:
                    if isinstance(n, cls):
                        yield n
                    else:
                        for n in find(n, depth - 1):
                            yield n
        return find(self, depth)
        
    def iter_toplevel_items(self):
        """Yield the toplevel items of our Document node in backward direction.
        
        Iteration starts with the node just before the node "self" is a 
        descendant of.
        
        """
        node = self
        for doc in self.ancestors():
            if isinstance(doc, Document):
                break
            node = doc
        else:
            return
        
        # now, doc is the Document node, and node is the child of the Document
        # node we are a (far) descendant of
        for i in node.backward():
            yield i
        
        # look in parent Document before the place we were included
        while doc.include_node:
            p = doc.include_node.parent()
            if isinstance(p, Document):
                for i in doc.include_node.backward():
                    yield i
                doc = p
            else:
                break
                
    def iter_toplevel_items_include(self):
        """Same as iter_toplevel_items(), but follows \\include commands."""
        def follow(it):
            for i in it:
                if isinstance(i, Include):
                    doc = i.parent().get_included_document_node(i)
                    if doc:
                        for i in follow(doc[::-1]):
                            yield i
                else:
                    yield i
        return follow(self.iter_toplevel_items())
    
    def music(self):
        """Walk up the parent tree until Music is found; return the outermost Music node.
        
        Returns None is the node does not belong to any music expression (e.g.
        a toplevel Markup or Scheme object).
        
        """
        it = self.ancestors()
        n = self
        if not isinstance(self, Music):
            for n in it:
                if isinstance(n, Music):
                    break
            else:
                return
        for m in it:
            if not isinstance(m, Music):
                return n
            n = m


class Document(Item):
    """A toplevel item representing a ly.document.Document."""
    
    def __init__(self, doc):
        super(Document, self).__init__()
        self.document = doc
        self.include_node = None
        self.include_path = []
        self.relative_includes = True
        import ly.document
        c = ly.document.Cursor(doc)
        s = ly.document.Source(c, True, tokens_with_position=True)
        r = Reader(s)
        self.extend(r.read())
    
    def node(self, position, maxdepth=-1):
        """Return the node at or just before the specified position."""
        def bisect(n, depth):
            end = len(n)
            if depth == 0 or end == 0:
                return n
            pos = 0
            while pos < end:
                mid = (pos + end) // 2
                if position < n[mid].position:
                    end = mid
                else:
                    pos = mid + 1
            pos -= 1
            if n[pos].position == position:
                return n[pos]
            elif n[pos].position > position:
                return n
            return bisect(n[pos], depth - 1)
        return bisect(self, maxdepth)
    
    def time_position(self, position):
        """Return a two-tuple (fraction, node).
        
        The fraction is the music time position, the node is the top node
        where the counting stopped.
        
        If the fraction is 0 and node is None, the time position makes
        no sense.
        
        You can compute the length of an expression if two time positions
        have the same top node.
        
        """
        n = self.node(position)
        # be nice and allow including an assignment
        if (isinstance(n, Assignment) and n.parent() is self
            and isinstance(n.value(), Music)):
            return 0, n.value()
        
        length = 0
        topnode = n if isinstance(n, Music) else None
        parent = n.parent()
        while parent:
            if n.position < position:
                # add length of current note, chord or user command
                if isinstance(n, Durable) and not isinstance(parent, Chord):
                    length += n.length()
                elif isinstance(n, UserCommand):
                    i = self.substitute_for_node(n)
                    if isinstance(i, (Music, Durable)):
                        length += i.length()
            # look back in the parent music list if possible
            if isinstance(parent, Music):
                topnode = parent
                if not (
                        (isinstance(parent, MusicList) and parent.simultaneous)
                        or isinstance(parent, (Relative, Transpose, Alternative))
                    ):
                    for i in n.backward():
                        if isinstance(i, UserCommand):
                            i = self.substitute_for_node(i)
                        if isinstance(i, (Music, Durable)):
                            length += i.length()
                    # adjust the current length if it is a scaling item
                    if isinstance(parent, Scaler):
                        length *= parent.scaling
            # stop outside music (in \score or assignment, etc)
            elif topnode:
                if position > topnode.end_position():
                    return 0, None
                break
            n = parent
            parent = n.parent()
        return length, topnode
    
    def time_length(self, start, end):
        """Return the length of the music between start and end positions.
        
        Returns None if start and end are not in the same expression.
        
        """
        if start > end:
            start, end = end, start
        start, n = self.time_position(start)
        if n:
            end, m = self.time_position(end)
            if n is m:
                return end - start
        
    def substitute_for_node(self, node):
        """Returns a node that replaces the specified node (e.g. in music).
        
        For example: a variable reference returns its value.
        Returns nothing if the node is not substitutable.
        Returns the node itself if it was substitutable, but the substitution
        failed.
        
        """
        if isinstance(node, UserCommand):
            value = node.value()
            if value:
                return self.substitute_for_node(value) or value
            return node
        elif isinstance(node, Include):
            return self.get_included_document_node(node) or node
        
        # maybe other substitutions
    
    def iter_music(self, node=None):
        """Iter over the music, following references to other assignments."""
        for n in node or self:
            n = self.substitute_for_node(n) or n
            yield n
            for n in self.iter_music(n):
                yield n
    
    def get_included_document_node(self, node):
        """Return a Document for the Include node."""
        try:
            return node._document
        except AttributeError:
            node._document = None
            filename = node.filename()
            if filename:
                resolved = self.resolve_filename(filename)
                if resolved:
                    docnode = self.get_music(resolved)
                    docnode.include_node = node
                    docnode.include_path = self.include_path
                    node._document = docnode
            return node._document
    
    def resolve_filename(self, filename):
        """Resolve filename against our document and include_path."""
        import os
        if os.path.isabs(filename):
            return filename
        path = list(self.include_path)
        if self.document.filename:
            basedir = os.path.dirname(self.document.filename)
            try:
                path.remove(basedir)
            except ValueError:
                pass
            path.insert(0, basedir)
        for p in path:
            fullpath = os.path.join(p, filename)
            if os.path.exists(fullpath):
                return fullpath
    
    def get_music(self, filename):
        """Return the music Document for the specified filename.
        
        This implementation loads a ly.document.Document using utf-8 
        encoding. Inherit from this class to implement other loading 
        mechanisms or caching.
        
        """
        import ly.document
        return type(self)(ly.document.Document.load(filename))


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
        """Return the duration.
        
        Returns 0 if no duration attribute was set.
        
        """
        return self.duration.fraction() if self.duration else 0
    
    def base_scaling(self):
        """Return the base and scaling fractions (if set, else None)."""
        if self.duration:
            return self.duration.base_scaling


class Chord(Durable, Container):
    pass


class Unpitched(Durable):
    """A "note" without pitch, just a standalone duration."""
    pitch = None


class Note(Durable):
    """A Note that has a ly.pitch.Pitch"""
    pitch = None
    octave_token = None
    accidental_token = None
    octavecheck_token = None


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


class Tag(Music):
    """A \\tag, \\keepWithTag or \\removeWithTag command."""
    def length(self):
        for l in self.child_length_iter(self[::-1]):
            return l


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


class PartCombine(Music):
    """The \\partcombine command with 2 music arguments."""
    def length(self):
        return max(self.child_length_iter())


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
            own_length *= count
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
    _beatstructure = None

    def measure_length(self):
        """The length of one measure in this time signature as a Fraction."""
        return self._num * self._fraction
    
    def numerator(self):
        """The upper number (e.g. for 3/2 it returns 3)."""
        return self._num
    
    def fraction(self):
        """The lower number as a Fraction (e.g. for 3/2 it returns 1/2)."""
        return self._fraction
    
    def beatstructure(self):
        """The scheme expressions denoting the beat structure, if specified."""
        return self._beatstructure


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


class PipeSymbol(Item):
    """A |."""


class VoiceSeparator(Item):
    """A \\\\."""


class Postfix(Item):
    """Any item that is prefixed with a _, - or ^ direction token."""


class Tie(Item):
    """A tie."""


class Slur(Item):
    """A ( or )."""
    event = None


class PhrasingSlur(Item):
    """A \\( or \\)."""
    event = None


class Beam(Item):
    """A [ or ]."""
    event = None


class Dynamic(Item):
    """Any dynamic symbol."""


class Articulation(Item):
    """An articulation, fingering, string number, or other symbol."""


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
    
    def value(self):
        """Find the value assigned to this variable."""
        for i in self.iter_toplevel_items_include():
            if isinstance(i, Assignment) and i.name() == self.name():
                return i.value()
    
    def child_length_iter(self):
        v = self.value()
        if isinstance(v, (Music, Durable)):
            yield v.length()


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
    """A \\score inside Markup."""


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
            if isinstance(t, lilypond.ContextName):
                return t
    
    def property(self):
        """The property."""
        for t in self.tokens:
            if isinstance(t, lilypond.ContextProperty):
                return t
        for t in self.tokens[::-1]:
            if isinstance(t, lilypond.Name):
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
            if isinstance(t, lilypond.ContextName):
                return t
    
    def property(self):
        """The property."""
        for t in self.tokens:
            if isinstance(t, lilypond.ContextProperty):
                return t
        for t in self.tokens[::-1]:
            if isinstance(t, lilypond.Name):
                return t


class Override(Item):
    """An \\override command."""
    def context(self):
        for i in self:
            if isinstance(i.token, lilypond.ContextName):
                return i.token
    
    def grob(self):
        for i in self:
            if isinstance(i.token, lilypond.GrobName):
                return i.token


class Revert(Item):
    """A \\revert command."""
    def context(self):
        for i in self:
            if isinstance(i.token, lilypond.ContextName):
                return i.token
    
    def grob(self):
        for i in self:
            if isinstance(i.token, lilypond.GrobName):
                return i.token


class Tweak(Item):
    """A \\tweak command."""


class PathItem(Item):
    """An item in the path of an \\override or \\revert command."""


class String(Item):
    """A double-quoted string."""
    
    def value(self):
        return ''.join(
            t[1:] if isinstance(t, lex.Character) and t.startswith('\\') else t
            for t in self.tokens[:-1])


class Number(Item):
    """A numerical value, directly entered."""
    def value(self):
        if isinstance(self.token, lilypond.IntegerValue):
            return int(self.token)
        elif isinstance(self.token, lilypond.DecimalValue):
            return float(self.token)
        elif isinstance(self.token, lilypond.Fraction):
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
    
    def get_list_ints(self):
        """A basic way to get a list of integer values."""
        return [int(i.token) for i in self.find(SchemeItem) if i.token.isdigit()]
    
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



def skip(source, what=(lex.Space, lex.Comment)):
    """Yield tokens from source, skipping items of classes specified in what.
    
    By default, comments and whitespace are skipped.
    
    """
    for t in source:
        if not isinstance(t, what):
            yield t


class dispatcher(object):
    """Decorator creator to dispatch commands, keywords, etc. to a method."""
    def __init__(self):
        self.d = {}
    
    def read_arg(self, a):
        return a
    
    def __call__(self, *args):
        d = self.d
        def wrapper(func):
            for a in args:
                d[a] = func
            doc = "handle " + ", ".join(map(self.read_arg, args))
            func.__doc__ = doc if not func.__doc__ else func.__doc__ + '\n\n' + doc
            return func
        return wrapper
    
    def method(self, token):
        """The registered method to call for the token. May return None."""
        return self.d.get(token)


class dispatcher_class(dispatcher):
    """Decorator creator to dispatch the class of a token to a method."""
    def read_arg(self, a):
        return a.__name__
    
    def method(self, token):
        """The registered method to call for the token's class. May return None."""
        cls = token.__class__
        d = self.d
        try:
            return d[cls]
        except KeyError:
            for c in cls.__mro__[1:]:
                try:
                    meth = d[cls] = d[c]
                except KeyError:
                    if c is not lex.Token:
                        continue
                    meth = d[cls] = None
                return meth


class Reader(object):
    """Reads tokens from a Source and builds a meaningful tree stucture."""
    
    _commands = dispatcher()
    _keywords = dispatcher()
    _tokencls = dispatcher_class()
    _markup = dispatcher_class()
    _scheme = dispatcher_class()
    
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
        d = item.duration = self.factory(Duration, position=0)
        tokens = []
        if not token or isinstance(token, lilypond.Duration):
            if token:
                tokens.append(token)
            for token in source:
                if isinstance(token, lilypond.Duration):
                    if tokens and isinstance(token, lilypond.Length):
                        self.source.pushback()
                        break
                    tokens.append(token)
                elif not isinstance(token, lex.Space):
                    self.source.pushback()
                    break
        if tokens:
            d.tokens = tuple(tokens)
            d.position = tokens[0].pos
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

    def factory(self, cls, token=None, consume=False, position=None):
        """Create Item instance for token.
        
        If consume is True, consume()s the source into item.tokens.
        If you don't specify a token, you must specify the position (>= 0).
        
        """
        item = cls()
        item.document = self.source.document
        if token:
            item.token = token
            item.position = token.pos
        elif position is None:
            raise ValueError("position must be specified if no token")
        else:
            item.position = position
        if consume:
            item.tokens = tuple(self.consume())
            if not token and item.tokens:
                item.position = item.tokens[0].pos
        return item
    
    def add_bracketed(self, item, source):
        """Append the arguments between brackets to the item.
        
        Returns True if that succeeded, else False.
        
        """
        for t in source:
            if isinstance(t, lilypond.OpenBracket):
                tokens = [t]
                item.extend(self.read(self.consume(tokens.append)))
                item.tokens = tuple(tokens)
                return True
            elif not isinstance(t, lex.Space):
                self.source.pushback()
                break
        return False
        
    def read(self, source=None):
        """Yield Item instances reading from source."""
        source = source or self.source
        for t in skip(source):
            item = self.read_item(t, source)
            if item:
                yield item
    
    def read_item(self, t, source=None):
        """Return one Item that starts with token t. May return None."""
        meth = self._tokencls.method(t)
        if meth:
            return meth(self, t, source or self.source)
    
    @_tokencls(lilypond.SchemeStart)
    @_markup(lilypond.SchemeStart)
    def handle_scheme_start(self, t, source=None):
        return self.read_scheme_item(t)
    
    @_tokencls(lex.StringStart)
    @_markup(lex.StringStart)
    @_scheme(lex.StringStart)
    def handle_string_start(self, t, source=None):
        return self.factory(String, t, True)
    
    @_tokencls(
        lilypond.DecimalValue,
        lilypond.IntegerValue,
        lilypond.Fraction,
    )
    def handle_number_class(self, t, source=None):
        return self.factory(Number, t)
    
    @_tokencls(lilypond.MusicItem)
    def handle_music_item(self, t, source):
        return self.read_music_item(t, source)
    
    @_tokencls(lilypond.Length)
    def handle_length(self, t, source):
        item = self.factory(Unpitched, position=t.pos)
        self.add_duration(item, t, source)
        return item
    
    @_tokencls(lilypond.ChordStart)
    def handle_chord_start(self, t, source):
        if not self.in_chord:
            self.in_chord = True
            chord = self.factory(Chord, t)
            def last(t): chord.tokens += (t,)
            chord.extend(self.read(self.consume(last)))
            self.in_chord = False
            self.add_duration(chord, None, source)
            return chord
    
    @_tokencls(
        lilypond.OpenBracket, lilypond.OpenSimultaneous,
        lilypond.SimultaneousOrSequentialCommand,
    )
    def handle_music_list(self, t, source):
        item, it = self.test_music_list(t)
        if item:
            if it:
                item.extend(self.read(it))
            return item
    
    @_tokencls(lilypond.Command)
    def read_command(self, t, source):
        """Read the rest of a command given in t from the source."""
        meth = self._commands.method(t)
        if meth:
            return meth(self, t, source)
        return self.factory(Command, t)
    
    @_tokencls(lilypond.Keyword)
    def read_keyword(self, t, source):
        """Read the rest of a keyword given in t from the source."""
        meth = self._keywords.method(t)
        if meth:
            return meth(self, t, source)
        return self.factory(Keyword, t)
    
    @_tokencls(lilypond.UserCommand)
    def read_user_command(self, t, source):
        """Read a user command, this can be a variable reference."""
        return self.factory(UserCommand, t)
    
    @_tokencls(lilypond.ChordSeparator)
    def read_chord_specifier(self, t, source=None):
        """Read stuff behind notes in chordmode."""
        item = self.factory(ChordSpecifier)
        item.position = t.pos
        item.append(self.factory(ChordItem, t))
        for t in self.consume():
            if isinstance(t, lilypond.ChordItem):
                item.append(self.factory(ChordItem, t))
            elif isinstance(t, lilypond.Note):
                r = ly.pitch.pitchReader(self.language)(t)
                if r:
                    note = self.factory(Note, t)
                    note.pitch = ly.pitch.Pitch(*r)
                    item.append(note)
        return item
    
    @_tokencls(lilypond.TremoloColon)
    def read_tremolo(self, t, source=None):
        """Read a tremolo."""
        item = self.factory(Tremolo, t)
        for t in self.source:
            if isinstance(t, lilypond.TremoloDuration):
                item.duration = self.factory(Duration, t)
                item.duration.base_scaling = ly.duration.base_scaling_string(t)
            else:
                self.source.pushback()
            break
        return item
    
    @_tokencls(lilypond.Name)
    def handle_name(self, t, source):
        if self.source.state.depth() < 2:
            return self.read_assignment(t)
    
    @_tokencls(
        lilypond.PaperVariable,
        lilypond.LayoutVariable,
        lilypond.HeaderVariable,
        lilypond.UserVariable,
    )
    def handle_variable_assignment(self, t, source):
        item = self.read_assignment(t)
        if item:
            # handle \pt, \in etc.
            for t in skip(self.source):
                if isinstance(t, lilypond.Unit):
                    item.append(self.factory(Command, t))
                else:
                    self.source.pushback()
                break
            return item
    
    _direct_items = {
        lilypond.VoiceSeparator: VoiceSeparator,
        lilypond.PipeSymbol: PipeSymbol,
        lilypond.Dynamic: Dynamic,
        lilypond.Tie: Tie,
    }
    @_tokencls(*_direct_items)
    def handle_direct_items(self, t, source):
        """Tokens that directly translate to an Item."""
        return self.factory(self._direct_items[t.__class__], t)
    
    @_tokencls(lilypond.Direction)
    def handle_direction(self, t, source):
        item = self.factory(Postfix, t)
        item.direction = '_-^'.index(t) - 1
        for t in skip(source):
            if isinstance(t, (
                lex.StringStart,
                lilypond.MarkupStart,
                lilypond.Articulation,
                lilypond.Slur,
                lilypond.Beam,
                lilypond.Dynamic,
                )):
                item.append(self.read_item(t))
            elif isinstance(t, lilypond.Command) and t in ('\\tag'):
                item.append(self.read_item(t))
            elif isinstance(t, lilypond.Keyword) and t in ('\\tweak'):
                item.append(self.read_item(t))
            else:
                self.source.pushback()
            break
        return item
    
    @_tokencls(lilypond.Slur)
    def handle_slurs(self, t, source=None):
        cls = PhrasingSlur if t.startswith('\\') else Slur
        item = self.factory(cls, t)
        item.event = 'start' if t.endswith('(') else 'stop'
        return item
    
    @_tokencls(lilypond.Beam)
    def handle_beam(self, t, source=None):
        item = self.factory(Beam, t)
        item.event = 'start' if t == '[' else 'stop'
        return item
    
    @_tokencls(lilypond.Articulation)
    def handle_beam(self, t, source=None):
        return self.factory(Articulation, t)
    
    def read_assignment(self, t):
        """Read an assignment from the variable name. May return None."""
        item = self.factory(Assignment, t)
        for t in skip(self.source):
            if isinstance(t, (lilypond.Variable, lilypond.UserVariable, lilypond.DotPath)):
                item.append(self.factory(PathItem, t))
            elif isinstance(t, lilypond.EqualSign):
                item.tokens = (t,)
                for i in self.read():
                    item.append(i)
                    break
                return item
            elif isinstance(t, lilypond.SchemeStart):
                # accept only one scheme item, if another one is found,
                # return the first, and discard the Assignment item
                # (should not normally happen)
                for s in item.find(Scheme):
                    self.source.pushback()
                    return s
                item.append(self.read_scheme_item(t))
            else:
                self.source.pushback()
                return
    
    def test_music_list(self, t):
        """Test whether a music list ({ ... }, << ... >>, starts here.
        
        Also handles \\simultaneous { ... } and \\sequential { ... } 
        correctly. These obscure commands are not even highlighted by 
        lex, but they exist in LilyPond... \\\simultaneous { ... } is 
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
            
        if isinstance(t, (lilypond.OpenBracket, lilypond.OpenSimultaneous)):
            return make_music_list(t, t == '<<')
        elif isinstance(t, lilypond.SimultaneousOrSequentialCommand):
            for t1 in skip(self.source):
                if isinstance(t1, (lilypond.OpenBracket, lilypond.OpenSimultaneous)):
                    return make_music_list(t, t == '\\simultaneous' or t1 == '<<', (t1,))
                else:
                    self.source.pushback()
                    return self.factory(Keyword, t), None
        return None, None
                    
    def read_music_item(self, t, source):
        """Read one music item (note, rest, s, \skip, or q) from t and source."""
        item = None
        in_pitch_command = isinstance(self.source.state.parser(), lilypond.ParsePitchCommand)
        if t.__class__ == lilypond.Note:
            r = ly.pitch.pitchReader(self.language)(t)
            if r:
                item = self.factory(Note, t)
                p = item.pitch = ly.pitch.Pitch(*r)
                for t in source:
                    if isinstance(t, lilypond.Octave):
                        p.octave = ly.pitch.octaveToNum(t)
                        item.octave_token = t
                    elif isinstance(t, lilypond.Accidental):
                        item.accidental_token = p.accidental = t
                    elif isinstance(t, lilypond.OctaveCheck):
                        p.octavecheck = ly.pitch.octaveToNum(t)
                        item.octavecheck_token = t
                        break
                    elif not isinstance(t, lex.Space):
                        self.source.pushback()
                        break
        else:
            cls = {
                lilypond.Rest: Rest,
                lilypond.Skip: Skip,
                lilypond.Spacer: Skip,
                lilypond.Q: Q,
            }[t.__class__]
            item = self.factory(cls, t)
        if item:
            if not self.in_chord and not in_pitch_command:
                self.add_duration(item, None, source)
        return item
    
    @_commands('\\relative')
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
    
    @_commands('\\absolute')
    def handle_absolute(self, t, source):
        item = self.factory(Absolute, t)
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @_commands('\\transpose')
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
    
    @_commands('\\clef')
    def handle_clef(self, t, source):
        item = self.factory(Clef, t)
        for t in skip(source):
            if isinstance(t, lilypond.ClefSpecifier):
                item._specifier = t
            elif isinstance(t, lex.StringStart):
                item._specifier = self.factory(String, t, True)
            break
        return item
    
    @_commands('\\key')
    def handle_key(self, t, source):
        item = self.factory(KeySignature, t)
        item.extend(itertools.islice(self.read(source), 2))
        return item
    
    @_commands('\\times', '\\tuplet', '\\scaleDurations')
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
                if isinstance(t, lilypond.Fraction):
                    item.scaling = 1 / Fraction(t)
                elif isinstance(t, lilypond.Duration):
                    self.add_duration(item, t, source)
                    break
                elif not isinstance(t, lex.Space):
                    self.source.pushback()
                    break
        else: # t == '\\times'
            for t in source:
                if isinstance(t, lilypond.Fraction):
                    item.scaling = Fraction(t)
                    break
                elif not isinstance(t, lex.Space):
                    self.source.pushback()
                    break
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @_commands('\\tag', '\\keepWithTag', '\\removeWithTag', '\\appendToTag', '\\pushToTag')
    def handle_tag(self, t, source):
        item = self.factory(Tag, t)
        argcount = 3 if t in ('\\appendToTag', '\\pushToTag') else 2
        item.extend(itertools.islice(self.read(), argcount))
        return item
    
    @_commands('\\grace', '\\acciaccatura', '\\appoggiatura', '\\slashedGrace')
    def handle_grace(self, t, source):
        item = self.factory(Grace, t)
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @_commands('\\afterGrace')
    def handle_after_grace(self, t, source):
        item = self.factory(AfterGrace, t)
        for i in itertools.islice(self.read(source), 2):
            item.append(i)
        return item
    
    @_commands('\\repeat')
    def handle_repeat(self, t, source):
        item = self.factory(Repeat, t)
        item._specifier = None
        item._repeat_count = None
        for t in skip(source):
            if isinstance(t, lilypond.RepeatSpecifier):
                item._specifier = t
            elif not item.specifier and isinstance(t, lex.StringStart):
                item._specifier = self.factory(String, t, True)
            elif isinstance(t, lilypond.RepeatCount):
                item._repeat_count = t
            elif isinstance(t, lilypond.SchemeStart):
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
                    if t == '\\alternative' and isinstance(t, lilypond.Command):
                        item.append(self.handle_alternative(t, source))
                    else:
                        self.source.pushback()
                    break
                break
        return item
    
    @_commands('\\alternative')
    def handle_alternative(self, t, source):
        item = self.factory(Alternative, t)
        for i in self.read(source):
            item.append(i)
            break
        return item
    
    @_commands('\\tempo')
    def handle_tempo(self, t, source):
        item = self.factory(Tempo, t)
        item._text = None
        item._tempo = []
        source = self.consume()
        equal_sign_seen = False
        for t in source:
            if not equal_sign_seen:
                if not item._text:
                    if isinstance(t, lilypond.SchemeStart):
                        item._text = self.read_scheme_item(t)
                    elif isinstance(t, lex.StringStart):
                        item._text = self.factory(String, t, True)
                    elif isinstance(t, lilypond.Markup):
                        item._text = self.handle_markup(t)
                elif isinstance(t, lilypond.Length):
                    self.add_duration(item, t, source)
                elif isinstance(t, lilypond.EqualSign):
                    equal_sign_seen = True
            elif isinstance(t, lilypond.IntegerValue):
                item._tempo.append(t)
            elif isinstance(t, lilypond.SchemeStart):
                item._tempo.append(self.read_scheme_item(t))
        return item
    
    @_commands('\\time')
    def handle_time(self, t, source):
        item = self.factory(TimeSignature, t)
        for t in skip(source):
            if isinstance(t, lilypond.SchemeStart):
                item._beatstructure = self.read_scheme_item(t)
                continue
            elif isinstance(t, lilypond.Fraction):
                item._num, den = map(int, t.split('/'))
                item._fraction = Fraction(1, den)
            else:
                self.source.pushback()
            break
        return item
    
    @_commands('\\partial')
    def handle_partial(self, t, source):
        item = self.factory(Partial, t)
        self.add_duration(item, None, source)
        return item
    
    @_commands('\\new', '\\context', '\\change')
    def handle_translator(self, t, source):
        cls = Change if t == '\\change' else Context 
        item = self.factory(cls, t)
        isource = self.consume()
        for t in skip(isource):
            if isinstance(t, (lilypond.ContextName, lilypond.Name)):
                item._context = t
                for t in isource:
                    if isinstance(t, lilypond.EqualSign):
                        for t in isource:
                            if isinstance(t, lex.StringStart):
                                item._context_id = self.factory(String, t, True)
                                break
                            elif isinstance(t, lilypond.Name):
                                item._context_id = t
                                break
                            elif not isinstance(t, lex.Space):
                                self.source.pushback()
                                break
                    elif not isinstance(t, lex.Space):
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
    @_commands(*_inputmode_commands)
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
    @_commands(*_lyricmode_commands)
    def handle_lyricmode(self, t, source):
        cls = self._lyricmode_commands[t]
        item = self.factory(cls, t)
        if cls is LyricsTo:
            for t in skip(source):
                if isinstance(t, lilypond.Name):
                    item._context_id = t
                elif isinstance(t, (lex.String, lilypond.SchemeStart)):
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
        if isinstance(t, (lex.StringStart, lilypond.MarkupStart)):
            item = self.factory(LyricText, position=t.pos)
            item.append(self.read_item(t))
            self.add_duration(item)
            return item
        elif isinstance(t, lilypond.LyricText):
            item = self.factory(LyricText, t)
            self.add_duration(item)
            return item
        elif isinstance(t, lilypond.Lyric):
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
    
    @_commands('\\stringTuning')
    def handle_string_tuning(self, t, source):
        item = self.factory(StringTuning, t)
        for arg in self.read(source):
            item.append(arg)
            break
        return item
    
    @_commands('\\partcombine')
    def handle_partcombine(self, t, source=None):
        item = self.factory(PartCombine, t)
        item.extend(itertools.islice(self.read(), 2))
        return item
    
    @_keywords('\\language')
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
    
    @_keywords('\\include')
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
    
    @_keywords('\\version')
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
    @_keywords(*_bracketed_keywords)
    def handle_bracketed(self, t, source):
        cls = self._bracketed_keywords[t]
        item = self.factory(cls, t)
        if not self.add_bracketed(item, source) and t == '\\with':
            # \with also supports one other argument instead of { ... }
            for i in self.read(source):
                item.append(i)
                break
        return item
    
    @_keywords('\\set')
    def handle_set(self, t, source):
        item = self.factory(Set, t)
        tokens = []
        for t in skip(source):
            tokens.append(t)
            if isinstance(t, lilypond.EqualSign):
                item.tokens = tuple(tokens)
                for i in self.read(source):
                    item.append(i)
                    break
                break
        return item
    
    @_keywords('\\unset')
    def handle_unset(self, t, source):
        item = self.factory(Unset, t)
        tokens = []
        for t in skip(self.consume()):
            if type(t) not in lilypond.ParseUnset.items:
                self.source.pushback()
                break
            tokens.append(t)
        item.tokens = tuple(tokens)
        return item
    
    @_keywords('\\override')
    def handle_override(self, t, source):
        item = self.factory(Override, t)
        for t in skip(self.consume()):
            if isinstance(t, (lex.StringStart, lilypond.SchemeStart)):
                item.append(self.read_item(t))
            elif isinstance(t, lilypond.EqualSign):
                item.tokens = (t,)
                for i in self.read():
                    item.append(i)
                    break
                break
            else:
                item.append(self.factory(PathItem, t))
        return item
    
    @_keywords('\\revert')
    def handle_revert(self, t, source):
        item = self.factory(Revert, t)
        t = None
        for t in skip(self.consume()):
            if type(t) in lilypond.ParseRevert.items:
                item.append(self.factory(PathItem, t))
            else:
                break
        if isinstance(t, lilypond.SchemeStart) and not any(
                isinstance(i.token, lilypond.GrobProperty) for i in item):
            item.append(self.read_scheme_item(t))
        else:
            self.source.pushback()
        return item
    
    @_keywords('\\tweak')
    def handle_tweak(self, t, source):
        item = self.factory(Tweak, t)
        t = None
        for t in skip(self.consume()):
            if type(t) in lilypond.ParseTweak.items:
                item.append(self.factory(PathItem, t))
            else:
                self.source.pushback()
                break
        if len(item) == 0 and isinstance(t, lilypond.SchemeStart):
            item.append(self.read_scheme_item(t))
        for i in self.read():
            item.append(i)
            break
        return item
    
    @_commands('\\markup', '\\markuplist', '\\markuplines')
    def handle_markup(self, t, source=None):
        item = self.factory(Markup, t)
        self.add_markup_arguments(item)
        return item
        
    def read_markup(self, t):
        """Read LilyPond markup (recursively)."""
        meth = self._markup.method(t)
        if meth:
            return meth(self, t)
    
    @_markup(lilypond.MarkupScore)
    def handle_markup_score(self, t):
        item = self.factory(MarkupScore, t)
        for t in self.consume():
            if isinstance(t, lilypond.OpenBracket):
                item.tokens = (t,)
                def last(t): item.tokens += (t,)
                item.extend(self.read(self.consume(last)))
                return item
            elif not isinstance(t, lex.Space):
                self.source.pushback()
                break
        return item
    
    @_markup(lilypond.MarkupCommand)
    def handle_markup_command(self, t):
        item = self.factory(MarkupCommand, t)
        self.add_markup_arguments(item)
        return item
    
    @_markup(lilypond.OpenBracketMarkup)
    def handle_markup_open_bracket(self, t):
        item = self.factory(MarkupList, t)
        self.add_markup_arguments(item)
        return item
    
    @_markup(lilypond.MarkupWord)
    def handle_markup_word(self, t):
        return self.factory(MarkupWord, t)
    
    def add_markup_arguments(self, item):
        """Add markup arguments to the item."""
        for t in self.consume():
            i = self.read_markup(t)
            if i:
                item.append(i)
            elif isinstance(item, MarkupList) and isinstance(t, lilypond.CloseBracketMarkup):
                item.tokens = (t,)
        return item
    
    def read_scheme_item(self, t):
        """Reads a Scheme expression (just after the # in LilyPond mode)."""
        item = self.factory(Scheme, t)
        for t in self.consume():
            if not isinstance(t, lex.Space):
                i = self.read_scheme(t)
                if i:
                    item.append(i)
                    break
        return item

    def read_scheme(self, t):
        """Return a Scheme item from the token t."""
        meth = self._scheme.method(t)
        if meth:
            return meth(self, t)
        
    @_scheme(scheme.Quote)
    def handle_scheme_quote(self, t):
        item = self.factory(SchemeQuote, t)
        for t in self.consume():
            if not isinstance(t, lex.Space):
                i = self.read_scheme(t)
                if i:
                    item.append(i)
                    break
        return item
    
    @_scheme(scheme.OpenParen)
    def handle_scheme_open_parenthesis(self, t):
        item = self.factory(SchemeList, t)
        def last(t): item.tokens = (t,)
        for t in self.consume(last):
            if not isinstance(t, lex.Space):
                i = self.read_scheme(t)
                if i:
                    item.append(i)
        return item
    
    @_scheme(
        scheme.Dot,
        scheme.Bool,
        scheme.Char,
        scheme.Word,
        scheme.Number,
        scheme.Fraction,
        scheme.Float,
    )
    def handle_scheme_token(self, t):
        return self.factory(SchemeItem, t)
    
    @_scheme(scheme.LilyPondStart)
    def handle_scheme_lilypond_start(self, t):
        item = self.factory(SchemeLily, t)
        def last(t): item.tokens = (t,)
        item.extend(self.read(self.consume(last)))
        return item


