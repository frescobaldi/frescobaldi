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

Whitespace is left out, but comments are retained.

"""

from __future__ import unicode_literals

from fractions import Fraction

import node

import ly.duration
import ly.pitch
import ly.lex.lilypond


class Item(node.WeakNode):
    """Represents any item in the music of a document.
    
    This can be just a token, or an interpreted construct such as a note,
    rest or sequential or simultanuous construct , etc.
    
    Some Item instances just have one responsible token, but others have a
    list or tuple to tokens.
    
    An Item also has a pointer to the Document it originates from.
    
    """
    document = None
    tokens = ()
    token = None


class Token(Item):
    """Any token that is not otherwise recognized""" 


class Container(Item):
    """An item having a list of child items."""


class Duration(Item):
    """A duration"""
    base_scaling = None, None   # two Fractions
    
class Durable(Item):
    """An Item that has a Duration attribute."""
    duration = None
    
    def length(self):
        """Return the duration or None (not set)."""
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
    """A music expression, either << >> or { }."""
    simultaneous = False
    
    def length(self):
        gen = (c.length() for c in self if isinstance(c, (Music, Durable)))
        return max(gen) if self.simultaneous else sum(gen)


class SchemeValue(Item):
    """The full list of tokens after a #."""
    

class StringValue(Item):
    """A double-quoted string."""


class Comment(Item):
    """A comment."""
    


class Reader(object):
    
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
        """Add a duration attribute to the item.
        
        Returns the last token if there were more read from the source.
        
        """
        source = source or self.source
        d = item.duration = Duration()
        d.tokens = []
        if not token or isinstance(token, ly.lex.lilypond.Duration):
            if token:
                d.tokens.append(token)
            for token in source:
                if isinstance(token, ly.lex.lilypond.Duration):
                    d.tokens.append(token)
                elif not isinstance(token, ly.lex.Space):
                    break
        if d.tokens:
            d.base_scaling = self.prev_duration = ly.duration.base_scaling(d.tokens)
        else:
            d.base_scaling = self.prev_duration
        return token
    
    def consume(self, source=None):
        """Yield the tokens until a parser is exit."""
        source = source or self.source
        depth = self.source.state.depth()
        for t in source:
            yield t
            if self.source.state.depth() < depth:
                break

    def read(self, source=None):
        """Yield Item instances reading from source."""
        
        def factory(cls, token, consume=True):
            item = cls()
            item.token = token
            if consume:
                item.tokens = tuple(self.consume(source))
            return item
        
        source = source or self.source
        for t in source:
            while isinstance(t, ly.lex.lilypond.MusicItem):
                item = None
                if t.__class__ == ly.lex.lilypond.Note:
                    r = ly.pitch.pitchReader(self.language)(t)
                    if r:
                        item = factory(Note, t, False)
                        p = item.pitch = ly.pitch.Pitch(*r)
                        t = None # prevent hang in this loop
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
                                break
                else:
                    cls = {
                        ly.lex.lilypond.Rest: Rest,
                        ly.lex.lilypond.Skip: Skip,
                        ly.lex.lilypond.Spacer: Skip,
                        ly.lex.lilypond.Q: Q,
                    }[t.__class__]
                    item = factory(cls, t, False)
                    t = None
                if item:
                    if not self.in_chord:
                        t = self.add_duration(item, t, source)
                    yield item
            if not self.in_chord and isinstance(t, ly.lex.lilypond.ChordStart):
                self.in_chord = True
                chord = factory(Chord, t, False)
                chord.extend(self.read(self.consume(source)))
                self.in_chord = False
                t = self.add_duration(chord, None, source)
                yield chord
            if isinstance(t, (ly.lex.lilypond.SequentialStart, ly.lex.lilypond.SimultaneousStart)):
                music = factory(Music, t, False)
                music.extend(self.read(self.consume(source)))
                music.simultaneous = t == '<<'  # TODO: support \simultaneous { ... }
                yield music
            elif isinstance(t, ly.lex.lilypond.SchemeStart):
                yield factory(SchemeValue, t)
            elif isinstance(t, ly.lex.BlockCommentStart):
                yield factory(Comment, t)
            elif isinstance(t, ly.lex.Comment):
                yield factory(Comment, t, False)
            elif isinstance(t, ly.lex.StringStart):
                item = factory(StringValue, t)
                item.value = ''.join(
                    t[1:] if isinstance(t, ly.lex.Character) and t.startswith('\\') else t
                    for t in item.tokens[:-1])
                yield item


