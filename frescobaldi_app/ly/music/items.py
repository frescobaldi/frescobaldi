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

from fractions import Fraction
import re

import node

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
            # end pos of Item or Token instances in attributes, such as duration etc
            for i in vars(self).values():
                if isinstance(i, Item):
                    yield i.end_position()
                elif isinstance(i, lex.Token):
                    yield i.end
        return max(ends())
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        return time
    
    def length(self):
        """Return the musical duration."""
        return 0
    
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
    
    def music_parent(self):
        """Walk up the parent tree until Music is found; return the outermost Music node.
        
        Returns None is the node does not belong to any music expression (e.g.
        a toplevel Markup or Scheme object).
        
        """
        node = self
        mus = isinstance(node, Music)
        for p in self.ancestors():
            pmus = isinstance(p, Music)
            if mus and not pmus:
                return node
            mus = pmus
            node = p
    
    def music_children(self, depth=-1):
        """Yield all the children that are new music expressions
        
        (i.e. that are inside other constructions).
        
        """
        def find(node, depth):
            if depth != 0:
                if isinstance(node, Music):
                    for i in node:
                        for i in find(i, depth-1):
                            yield i
                else:
                    for i in node:
                        if isinstance(i, Music):
                            yield i
                        else:
                            for i in find(i, depth-1):
                                yield i
        return find(self, depth)
    
    def has_output(self, _seen_docs=None):
        """Return True if this node has toplevel music, markup, book etc.
        
        I.e. returns True when LilyPond would likely generate output. Usually
        you'll call this method on a Document, Score, BookPart or Book node.
        
        You should not supply the _seen_docs argument; it is used internally 
        to avoid traversing recursively nested include files.
        
        """
        if _seen_docs is None:
            _seen_docs = set()
        _seen_docs.add(self)
        for n in self:
            if isinstance(n, (Music, Markup)):
                return True
            elif isinstance(n, (Book, BookPart, Score)):
                if n.has_output(_seen_docs):
                    return True
            elif isinstance(n, Include):
                doc = self.toplevel().get_included_document_node(n)
                if doc and doc not in _seen_docs and doc.has_output(_seen_docs):
                    return True


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
        from .read import Reader
        r = Reader(s)
        self.extend(r.read())
    
    def node(self, position, depth=-1):
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
        return bisect(self, depth)
    
    def music_events_til_position(self, position):
        """Return a list of tuples.
        
        Every tuple is a (parent, nodes, scaling). If an empty list is 
        returned, there is no music expression at this position.
        
        """
        node = self.node(position)
        # be nice and allow including an assignment
        if (isinstance(node, Assignment) and node.parent() is self
            and isinstance(node.value(), Music)):
            return [(node, [], 1)]
        
        if isinstance(node.parent(), Chord):
            node = node.parent()
        
        l = []
        mus = isinstance(node, (Music, Durable))
        if mus:
            l.append((node, [], 1))
        for p in node.ancestors():
            pmus = isinstance(p, Music)
            end = node.end_position()
            if pmus:
                if position > end:
                    preceding, s = p.preceding(node.next_sibling())
                    l = [(p, preceding, s)]
                elif position == end:
                    preceding, s = p.preceding(node)
                    l = [(p, preceding + [node], s)]
                else:
                    preceding, s = p.preceding(node)
                    l.append((p, preceding, s))
            elif mus:
                # we are at the musical top
                if position > end:
                    return []
                elif position == end:
                    l = [(p, [node], 1)]
                else:
                    l.append((p, [], 1))
                break
            node = p
            mus = pmus
        l.reverse()
        return l
    
    def time_position(self, position):
        """Return the time position in the music at the specified cursor position.
        
        The value is a fraction. If None is returned, we are not in a music 
        expression.
        
        """
        events = self.music_events_til_position(position)
        if events:
            from . import event
            e = event.Events()
            time = 0
            scaling = 1
            for parent, nodes, s in events:
                scaling *= s
                for n in nodes:
                    time = e.traverse(n, time, scaling)
            return time
    
    def time_length(self, start, end):
        """Return the length of the music between start and end positions.
        
        Returns None if start and end are not in the same expression.
        
        """
        def mk_list(evts):
            """Make a flat list of all the events."""
            l = []
            scaling = 1
            for p, nodes, s in evts:
                scaling *= s
                for n in nodes:
                    l.append((n, scaling))
            return l
        
        if start > end:
            start, end = end, start
        
        start_evts = self.music_events_til_position(start)
        if start_evts:
            end_evts = self.music_events_til_position(end)
            if end_evts and start_evts[0][0] is end_evts[0][0]:
                # yes, we have the same toplevel expression.
                start_evts = mk_list(start_evts)
                end_evts = mk_list(end_evts)
                from . import event
                e = event.Events()
                time = 0
                i = 0
                # traverse the common events only once
                for i, ((evt, s), (end_evt, end_s)) in enumerate(zip(start_evts, end_evts)):
                    if evt is end_evt:
                        time = e.traverse(evt, time, s)
                    else:
                        break
                end_time = time
                # handle the remaining events for the start position
                for evt, s in start_evts[i::]:
                    time = e.traverse(evt, time, s)
                # handle the remaining events for the end position
                for evt, s in end_evts[i::]:
                    end_time = e.traverse(evt, end_time, s)
                return end_time - time
        
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
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        if self.duration:
            time += self.duration.fraction() * scaling
        return time
    
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
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        for node in self:
            time = e.traverse(node, time, scaling)
        return time
    
    def length(self):
        """Return the musical duration."""
        from . import event
        return event.Events().read(self)
    
    def preceding(self, node=None):
        """Return a two-tuple (nodes, scaling).
        
        The nodes are the nodes in time before the node (which must be a
        child), and the scaling is the scaling this node applies (normally 1).
        
        If node is None, all nodes that would precede a fictive node at the
        end are returned.
        
        """
        i = self.index(node) if node else None
        return self[:i:], 1


class MusicList(Music):
    """A music expression, either << >> or { }."""
    simultaneous = False
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        if self.simultaneous:
            if len(self):
                time = max(e.traverse(node, time, scaling) for node in self)
        else:
            time = super(MusicList, self).events(e, time, scaling)
        return time

    def preceding(self, node=None):
        """Return a two-tuple (nodes, scaling).
        
        The nodes are the nodes in time before the node (which must be a
        child), and the scaling is the scaling this node applies (normally 1).
        
        If node is None, all nodes that would precede a fictive node at the
        end are returned.
        
        """
        if self.simultaneous:
            return [], 1
        return super(MusicList, self).preceding(node)


class Tag(Music):
    """A \\tag, \\keepWithTag or \\removeWithTag command."""
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        for node in self[-1:]:
            time = e.traverse(node, time, scaling)
        return time
        
    def preceding(self, node=None):
        """Return a two-tuple (nodes, scaling).
        
        The nodes are the nodes in time before the node (which must be a
        child), and the scaling is the scaling this node applies (normally 1).
        
        If node is None, all nodes that would precede a fictive node at the
        end are returned.
        
        """
        return [], 1


class Scaler(Music):
    """A music construct that scales the duration of its contents."""
    scaling = 1
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        return super(Scaler, self).events(e, time, scaling * self.scaling)
    
    def preceding(self, node=None):
        """Return a two-tuple (nodes, scaling).
        
        The nodes are the nodes in time before the node (which must be a
        child), and the scaling is the scaling this node applies.
        
        If node is None, all nodes that would precede a fictive node at the
        end are returned.
        
        """
        i = self.index(node) if node else None
        return self[:i:], self.scaling


class Grace(Music):
    """Music that has grace timing, i.e. 0 as far as computation is concerned."""
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        return super(Grace, self).events(e, time, 0)
    
    def preceding(self, node=None):
        """Return a two-tuple (nodes, scaling).
        
        The nodes are the nodes in time before the node (which must be a
        child), and the scaling is 0 for (because we have grace notes).
        
        If node is None, all nodes that would precede a fictive node at the
        end are returned.
        
        """
        i = self.index(node) if node else None
        return self[:i:], 0


class AfterGrace(Music):
    """The \afterGrace function with its two arguments.
    
    Only the duration of the first is counted.
    
    """


class PartCombine(Music):
    """The \\partcombine command with 2 music arguments."""
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        if len(self):
            time = max(e.traverse(node, time, scaling) for node in self)
        return time
    
    def preceding(self, node=None):
        """Return a two-tuple (nodes, scaling).
        
        The nodes are the nodes in time before the node (which must be a
        child), and the scaling is the scaling this node applies (normally 1).
        
        If node is None, all nodes that would precede a fictive node at the
        end are returned.
        
        """
        return [], 1


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

    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        if len(self) and isinstance(self[-1], Alternative):
            alt = self[-1]
            children = self[:-1]
        else:
            alt = None
            children = self[:]
        
        if e.unfold_repeats or self.specifier() != "volta":
            count = self.repeat_count()
            if alt and len(alt):
                alts = list(alt[0])[:count+1]
                alts[0:0] = [alts[0]] * (count - len(alts))
                for a in alts:
                    for n in children:
                        time = e.traverse(n, time, scaling)
                    time = e.traverse(a, time, scaling)
            else:
                for i in range(count):
                    for n in children:
                        time = e.traverse(n, time, scaling)
        else:
            for n in children:
                time = e.traverse(n, time, scaling)
            if alt:
                time = e.traverse(alt, time, scaling)
        return time


class Alternative(Music):
    """An \\alternative expression."""


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

    def partial_length(self):
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
    
    def events(self, e, time, scaling):
        """Let the event.Events instance handle the events. Return the time."""
        value = self.value()
        if value:
            time = e.traverse(value, time, scaling)
        return time


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


class MarkupUserCommand(Item):
    """A user-defined markup command"""
    def name(self):
        """Return the name of this user command (without the \\)."""
        return self.token[1:]
    
    def value(self):
        """Find the value assigned to this variable."""
        for i in self.iter_toplevel_items_include():
            if isinstance(i, Assignment) and i.name() == self.name():
                return i.value()
            elif isinstance(i, Scheme):
                for j in i:
                    if isinstance(j, SchemeList):
                        for k in j:
                            if isinstance(k, SchemeItem) and k.token == 'define-markup-command':
                                for l in j[1::]:
                                    if isinstance(l, SchemeList):
                                        for m in l:
                                            if isinstance(m, SchemeItem) and m.token == self.name():
                                                return i
                                            break
                                    break
                            break
                    break


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
        if len(self):
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



