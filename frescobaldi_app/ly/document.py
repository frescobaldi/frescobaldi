# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
DocumentBase and Document
=========================

Represents a lilypond source document (the text contents).

The Document implementation keeps the document in a (unicode) text string, 
but you can inherit from the DocumentBase class to support other 
representations of the text content.

Modifying is done inside a context (the with statement), e.g.:

d = Document('some string')
with d:
    d[5:5] = 'different '
d.plaintext()  --> 'some different string'

Changes are applied when the context is exited, also the modified part of the
document is re-tokenized. Changes may not overlap.

The tokens(block) method returns a tuple of tokens for the specified block. 
Depending on the implementation, a block describes a line in the LilyPond 
source document. It is not expected to have any methods, except that the 
'==' operator is supported between two blocks, and returns True if both 
refer to the same line of text in the source document.


Cursor
======

Defines a range or position in a Document.


Runner
======

A Runner allows iterating back and forth over the tokens of a document.


Source
======

Iterate over tokens in a (part of a) Document, with or without state.


"""

from __future__ import unicode_literals
from __future__ import absolute_import

import io
import sys
import operator
import collections
import weakref

import ly.lex


class DocumentBase(object):
    """Abstract base class for Document instances.
    
    You should inherit the following methods:
    
    setplaintext
    __len__
    __getitem__
    block
    index
    position
    text
    tokens
    isvalid
    initial_state
    state_end
    apply_changes
    
    You may inherit (e.g. to get speed improvements):
    
    plaintext
    next_block
    previous_block
    blocks_forward
    blocks_backward
    state
    
    You may use the following attributes:
    
    filename (None)   # can represent the filename of the document on disk
    encoding (None)   # can represent the encoding of the document when reading/writing to disk
    
    """
    
    filename = None
    encoding = None
    
    
    def __init__(self):
        """Constructor"""
        self._writing = 0
        self._changes = collections.defaultdict(list)
        # to keep compatible with 2.6 (else we'd use a WeakSet)
        self._cursors = weakref.WeakKeyDictionary()
    
    def __nonzero__(self):
        return True
    
    def __iter__(self):
        """Iter over all blocks."""
        return self.blocks_forward(self[0])
    
    def __len__(self):
        """Return the number of blocks"""
        raise NotImplementedError()
    
    def __getitem__(self, index):
        """Return the block at the specified index."""
        raise NotImplementedError()
        
    def plaintext(self):
        """The document contents as a plain text string."""
        return '\n'.join(map(self.text, self))

    def setplaintext(self, text):
        """Sets the document contents to the text string."""
        raise NotImplementedError()

    def size(self):
        """Return the number of characters in the document."""
        last_block = self[len(self) - 1]
        return self.position(last_block) + len(self.text(last_block))

    def block(self, position):
        """Return the text block at the specified character position.
        
        The text block itself has no methods, but it can be used as an
        argument to other methods of this class.
        
        (Blocks do have to support the '==' operator.)
        
        """
        raise NotImplementedError()
    
    def index(self, block):
        """Return the linenumber of the block (starting with 0)."""
        raise NotImplementedError()
         
    def blocks_forward(self, block):
        """Iter forward starting with the specified block."""
        while self.isvalid(block):
            yield block
            block = self.next_block(block)

    def blocks_backward(self, block):
        """Iter backwards starting with the specified block."""
        while self.isvalid(block):
            yield block
            block = self.previous_block(block)

    def position(self, block):
        """Return the position of the specified block."""
        raise NotImplementedError()

    def text(self, block):
        """Return the text of the specified block."""
        raise NotImplementedError()
    
    def next_block(self, block):
        """Return the next block, which may be invalid."""
        index = self.index(block)
        if index < len(self) - 1:
            return self[index + 1]
    
    def previous_block(self, block):
        """Return the previous block, which may be invalid."""
        index = self.index(block)
        if index > 0:
            return self[index - 1]
    
    def isvalid(self, block):
        """Return True if the block is a valid block."""
        raise NotImplementedError()
    
    def isblank(self, block):
        """Return True if the block is empty or blank."""
        t = self.text(block)
        return not t or t.isspace()

    def __enter__(self):
        """Start the context for modifying the document."""
        self._writing += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context for modifying."""
        if exc_type is not None:
            # cancel all edits when an exception occurred
            self._writing = 0
            self._changes.clear()
        elif self._writing == 1:
            if self._changes:
                self._changes_list = [(start, end, text)
                    for start, items in sorted(self._changes.items(), reverse=True)
                    for end, text in reversed(sorted(items,
                        key=lambda i: (i[0] is None, i[0])))]
                self._changes.clear()
                self.update_cursors()
                self.apply_changes()
                del self._changes_list
            self._writing = 0
        elif self._writing > 1:
            self._writing -= 1
    
    def _register_cursor(self, cursor):
        """Make a weak reference to the cursor.
        
        This is called by the constructor of the Cursor.
        The Cursor gets updated when the document is changed.
        
        """
        self._cursors[cursor] = True
        
    def check_changes(self):
        """Debugging method that checks for overlapping edits."""
        pos = self.size()
        for start, end, text in self._changes_list:
            if end > pos:
                if len(text) > 12:
                    text = text[:10] + '...'
                raise ValueError("overlapping edit: {0}-{1}: {2}".format(start, end, text))
            pos = start
    
    def update_cursors(self):
        """Updates the position of the registered Cursor instances."""
        for start, end, text in self._changes_list:
            for c in self._cursors:
                if c.start > start:
                    if end is None or end >= c.start:
                        c.start = start
                    else:
                        c.start += start + len(text) - end
                if c.end is not None and c.end >= start:
                    if end is None or end >= c.end:
                        c.end = start + len(text)
                    else:
                        c.end += start + len(text) - end
    
    def apply_changes(self):
        """Apply the changes and update the tokens."""
        raise NotImplementedError()
        
    def tokens(self, block):
        """Return the tuple of tokens of the specified block.
        
        The pos and end attributes of every token point to the position
        of the token in the block. 
        
        """
        raise NotImplementedError()
    
    def tokens_with_position(self, block):
        """Return a tuple of tokens of the specified block.
        
        The pos and end attributes of every token point to the position
        in the Document, instead of to the position in the current block.
        
        This makes it easier to iterate over tokens and change the document.
        
        """
        pos = self.position(block)
        return tuple(type(t)(t, pos + t.pos) for t in self.tokens(block))
        
    def initial_state(self):
        """Return the state at the beginning of the document."""
        raise NotImplementedError()
        
    def state(self, block):
        """Return the state at the start of the specified block."""
        prev = self.previous_block(block)
        if self.isvalid(prev):
            return self.state_end(prev)
        return self.initial_state()
            
    def state_end(self, block):
        """Return the state at the end of the specified block."""
        raise NotImplementedError()
    
    def __setitem__(self, key, text):
        """Change the text pointed to in key (integer or slice).
        
        If start > stop in the slice (and stop is not None), start and stop
        are swapped. (This is different than usual Python behaviour, where
        stop is set to start if it was lower.)
        
        """
        if isinstance(key, slice):
            start = key.start or 0
            end = key.stop
            if end is not None and start > end:
                start, end = end, start
        else:
            start = key
            end = start + 1
        text = text.replace('\r', '')
        if text or start != end:
            self._changes[start].append((end, text))

    def __delitem__(self, key):
        """Remove the range of text."""
        self[key] = ""


class Document(DocumentBase):
    """A plain text LilyPond source document that auto-updates the tokens.
    
    The modified attribute is set to True as soon as the document is changed,
    but the setplaintext() method sets it to False.
    
    """
    modified = False
    
    def __init__(self, text='', mode=None):
        super(Document, self).__init__()
        self._fridge = ly.lex.Fridge()
        self._mode = mode
        self._guessed_mode = None
        self.setplaintext(text)
    
    @classmethod
    def load(cls, filename, encoding='utf-8', mode=None):
        """Load the document from a file, using the specified encoding and mode."""
        with io.open(filename, encoding=encoding) as f:
            doc = cls(f.read(), mode)
        doc.filename = filename
        return doc
    
    def __len__(self):
        """Return the number of blocks"""
        return len(self._blocks)
    
    def __getitem__(self, index):
        """Return the block at the specified index."""
        return self._blocks[index]
    
    def setmode(self, mode):
        """Sets the mode to one of the ly.lex modes.
        
        Use None to auto-determine the mode.
        
        """
        if mode not in ly.lex.modes:
            mode = None
        if mode == self._mode:
            return
        self._mode, old_mode = mode, self._mode
        if not mode:
            self._guessed_mode = ly.lex.guessMode(self.plaintext())
            if self._guessed_mode == old_mode:
                return
        elif not old_mode:
            if mode == self._guessed_mode:
                return
        self._update_all_tokens()
    
    def mode(self):
        """Return the mode (lilypond, html, etc). None means automatic mode."""
        return self._mode
    
    def setplaintext(self, text):
        """Set the text of the document, sets modified to False."""
        text = text.replace('\r', '')
        lines = text.split('\n')
        self._blocks = [_Block(t, n) for n, t in enumerate(lines)]
        pos = 0
        for b in self._blocks:
            b.position = pos
            pos += len(b.text) + 1
        if not self._mode:
            self._guessed_mode = ly.lex.guessMode(text)
        self._update_all_tokens()
        self.modified = False
    
    def _update_all_tokens(self):
        state = self.initial_state()
        for b in self._blocks:
            b.tokens = tuple(state.tokens(b.text))
            b.state = self._fridge.freeze(state)
    
    def initial_state(self):
        """Return the state at the beginning of the document."""
        return ly.lex.state(self._mode or self._guessed_mode)
        
    def state_end(self, block):
        """Return the state at the end of the specified block."""
        return self._fridge.thaw(block.state)
    
    def block(self, position):
        """Return the text block at the specified character position."""
        if 0 <= position <= self._blocks[-1].position + len(self._blocks[-1].text):
            lo = 0
            hi = len(self._blocks)
            while lo < hi:
                mid = (lo + hi) // 2
                if position < self._blocks[mid].position:
                    hi = mid
                else:
                    lo = mid + 1
            return self._blocks[lo-1]
     
    def index(self, block):
        """Return the linenumber of the block (starting with 0)."""
        return block.index

    def position(self, block):
        """Return the position of the specified block."""
        return block.position

    def text(self, block):
        """Return the text of the specified block."""
        return block.text
    
    def isvalid(self, block):
        """Return True if the block is a valid block."""
        return bool(block)
    
    def tokens(self, block):
        """Return the tuple of tokens of the specified block."""
        return block.tokens
    
    def apply_changes(self):
        for start, end, text in self._changes_list:
            s = self.block(start)
            # first remove the old contents
            if end is None:
                # all text to the end should be removed
                s.text = s.text[:start - s.position]
                del self._blocks[s.index+1:]
            else:
                # remove til end position
                e = self.block(end)
                s.text = s.text[:start - s.position] + e.text[end - e.position:]
                del self._blocks[s.index+1:e.index+1]
            # now insert the new stuff
            if text:
                lines = text.split('\n')
                lines[-1] += s.text[start - s.position:]
                s.text = s.text[:start - s.position] + lines[0]
                self._blocks[s.index+1:s.index+1] = map(_Block, lines[1:])
            # make sure this line gets reparsed
            s.tokens = None
        
        # update the position of all the new blocks
        pos = s.position
        for i, b in enumerate(self._blocks[s.index:], s.index):
            b.index = i
            b.position = pos
            pos += len(b.text) + 1
        
        self.modified = True
        
        # if the initial state has changed, reparse everything
        if not self._mode:
            mode = ly.lex.guessMode(self.plaintext())
            if mode != self._guessed_mode:
                self._guessed_mode = mode
                self._update_all_tokens()
                return
        
        # update the tokens starting at block s
        state = self.state(s)
        reparse = False
        for block in self._blocks[s.index:]:
            if reparse or block.tokens is None:
                block.tokens = tuple(state.tokens(block.text))
                frozen = self._fridge.freeze(state)
                reparse = block.state != frozen
                block.state = frozen
            else:
                state = self._fridge.thaw(block.state)


class _Block(object):
    """A line of text.
    
    This class is only used by the Document implementation.
    
    """
    
    position = sys.maxsize  # prevent picking those blocks before updating pos
    state    = None
    tokens   = None
    
    def __init__(self, text="", index=-1):
        self.text = text
        self.index = index


class Cursor(object):
    """Defines a certain range (selection) in a Document.
    
    You may change the start and end attributes yourself. Both must be an 
    integer, end may also be None, denoting the end of the document.
    
    As long as you keep a reference to the Cursor, its positions are updated 
    when the document changes. When text is inserted at the start position, 
    it remains the same. But when text is inserted at the end of a cursor, 
    the end position moves along with the new text. E.g.:
    
    d = Document('hi there, folks!')
    c = Cursor(d, 8, 8)
    with d:
        d[8:8] = 'new text'
    c.start, c.end --> (8, 16)
    
    Many tools in the ly module use this object to describe (part of) a
    document.
    
    """
    def __init__(self, doc, start=0, end=None):
        self._d = doc
        self.start = start
        self.end = end
        doc._register_cursor(self)
    
    @property
    def document(self):
        return self._d
    
    def start_block(self):
        """Return the block the start attribute points at."""
        return self._d.block(self.start)
    
    def end_block(self):
        """Return the block the end attribute points at."""
        if self.end is None:
            return self._d[len(self._d)-1]
        return self._d.block(self.end)
    
    def blocks(self):
        """Iterate over the selected blocks.
        
        If there are multiple blocks and the cursor ends on the first 
        position of the last selected block, that block is not included.
        
        """
        if self.end == self.start:
            yield self.start_block()
        else:
            for b in self._d.blocks_forward(self.start_block()):
                if self.end is not None and self._d.position(b) >= self.end:
                    break
                yield b
    
    def text(self):
        """Convenience method to return the selected text."""
        return self._d.plaintext()[self.start:self.end]
    
    def text_before(self):
        """Return text before the cursor in it's start block."""
        b = self.start_block()
        pos = self.start - self._d.position(b)
        return self._d.text(b)[:pos]
        
    def text_after(self):
        """Return text after the cursor in it's end block."""
        if self.end is None:
            return ""
        b = self.end_block()
        pos = self.end - self._d.position(b)
        return self._d.text(b)[pos:]
        
    def has_selection(self):
        """Return True when there is some text selected."""
        end = self.end
        if end is None:
            end = self._d.size()
        return self.start != end
    
    def select_all(self):
        """Select all text."""
        self.start, self.end = 0, None
    
    def select_end_of_block(self):
        """Move end to the end of the block."""
        if self.end is not None:
            end = self.end_block()
            self.end = self._d.position(end) + len(self._d.text(end))
    
    def select_start_of_block(self):
        """Move start to the start of the block."""
        start = self.start_block()
        self.start = self._d.position(start)
    
    def lstrip(self, chars=None):
        """Move start to the right, like Python's lstrip() string method."""
        if self.has_selection():
            text = self.text()
            self.start += len(text) - len(text.lstrip(chars))
    
    def rstrip(self, chars=None):
        """Move end to the left, like Python's lstrip() string method."""
        if self.has_selection():
            text = self.text()
            end = self._d.size() if self.end is None else self.end
            end -= len(text) - len(text.rstrip(chars))
            if end < self._d.size():
                self.end = end
    
    def strip(self, chars=None):
        """Strip chars from the selection, like Python's strip() method."""
        self.rstrip(chars)
        self.lstrip(chars)


class Runner(object):
    """Iterates back and forth over tokens.
    
    A Runner can stop anywhere and remembers its current token.
    
    """
    def __init__(self, doc, tokens_with_position=False):
        """Create and init with Document.
        
        If tokens_with_position is True, uses the tokens_with_position() 
        method to get the tokens, else (by default), the tokens() method is 
        used.
        
        The Runner is initialized at position 0. Alternatively, you can use 
        the 'at' classmethod to construct a Runner at a specific cursor 
        position.
        
        """
        self._doc = doc
        self._wp = tokens_with_position
        self.move_to_block(doc[0])
    
    @classmethod
    def at(cls, cursor, after_token=False, tokens_with_position=False):
        """Create and init from a Cursor.
        
        The Runner is positioned so that yielding forward starts with the
        first complete token after the cursor's start position.
        
        Set after_token to True if you want to position the cursor after the
        token, so that it gets yielded when you go backward.
        
        If tokens_with_position is True, uses the tokens_with_position() 
        method to get the tokens, else (by default), the tokens() method is 
        used.
        
        """
        runner = cls(cursor.document, tokens_with_position)
        runner.set_position(cursor.start, after_token)
        return runner
    
    @property
    def document(self):
        """Return our Document."""
        return self._doc
    
    def set_position(self, position, after_token=False):
        """Positions the Runner at the specified position.
        
        Set after_token to True if you want to position the cursor after the
        token, so that it gets yielded when you go backward.
        
        """
        block = self._doc.block(position)
        self.move_to_block(block)
        if after_token:
            for t in self.forward_line():
                if self.position() + len(t) >= position:
                    self._index += 1
                    break
        else:
            for t in self.forward_line():
                if self.position() + len(t) > position:
                    self._index -= 1
                    break
        
    def move_to_block(self, block, at_end=False):
        """Positions the Runner at the start of the given text block.
        
        If at_end == True, the iterator is positioned past the end of the block.
        
        """
        if self._doc.isvalid(block):
            self.block = block
            method = self._doc.tokens_with_position if self._wp else self._doc.tokens
            self._tokens = method(block)
            self._index = len(self._tokens) if at_end else -1
            return True
    
    def _newline(self):
        """(Internal) Create a Newline token at the end of the current block."""
        pos = len(self._doc.text(self.block))
        if self._wp:
            pos += self._doc.position(self.block)
        return ly.lex.Newline('\n', pos)
        
    def forward_line(self):
        """Yields tokens in forward direction in the current block."""
        end = len(self._tokens)
        if self._index < end:
            while True:
                self._index += 1
                if self._index == end:
                    break
                yield self._tokens[self._index]
    
    def forward(self):
        """Yields tokens in forward direction across blocks."""
        while True:
            for t in self.forward_line():
                yield t
            newline = self._newline()
            if not self.next_block():
                break
            yield newline

    def backward_line(self):
        """Yields tokens in backward direction in the current block."""
        if self._index >= 0:
            while True:
                self._index -= 1
                if self._index == -1:
                    break
                yield self._tokens[self._index]
    
    def backward(self):
        """Yields tokens in backward direction across blocks."""
        while True:
            for t in self.backward_line():
                yield t
            if not self.previous_block():
                break
            yield self._newline()
    
    def previous_block(self, at_end=True):
        """Go to the previous block, positioning the cursor at the end by default.
        
        Returns False if there was no previous block, else True.
        
        """
        return self.move_to_block(self._doc.previous_block(self.block), at_end)
    
    def next_block(self, at_end=False):
        """Go to the next block, positioning the cursor at the start by default.
        
        Returns False if there was no next block, else True.
        
        """
        return self.move_to_block(self._doc.next_block(self.block), at_end)
    
    def token(self):
        """Re-returns the last yielded token."""
        if self._tokens:
            index = self._index
            if index < 0:
                index = 0
            elif index >= len(self._tokens):
                index = len(self._tokens) - 1
            return self._tokens[index]
        
    def position(self):
        """Returns the position of the current token."""
        if self._tokens:
            pos = self.token().pos
            if not self._wp:
                pos += self._doc.position(self.block)
            return pos
        else:
            return self._d.position(self.block)
    
    def copy(self):
        """Return a new Runner at the current position."""
        obj = type(self)(self._doc, self._wp)
        obj.block = self.block
        obj._tokens = self._tokens
        obj._index = self._index
        return obj


OUTSIDE = -1
PARTIAL = 0
INSIDE  = 1


class Source(object):
    """Helper iterator.
    
    Iterates over the (block, tokens) tuples from a Document (or a part 
    thereof). Stores the current block in the block attribute and the tokens 
    (which also is a generator) in the tokens attribute.
    
    Iterating over the source object itself just yields the tokens, while the
    block attribute contains the current block.
    
    You can also iterate over the tokens attribute, which will yield the
    remaining tokens of the current block and then stop.
    
    If you specify a state, the tokens will update the state. If you specify
    state = True, the state will be taken from the document.
    
    """
    
    def __init__(self, cursor, state=None, partial=INSIDE, tokens_with_position=False):
        """Initialize the iterator.
        
        cursor is a Cursor instance, describing a Document and a selected range
        partial is either OUTSIDE, PARTIAL, or INSIDE:
            OUTSIDE: tokens that touch the selected range are also yielded
            PARTIAL: tokens that overlap the start or end positions are yielded
            INSIDE:  (default) yield only tokens fully contained in the range
        The partial argument only makes sense if start or end are specified.
        
        If tokens_with_position is True, uses the tokens_with_position() 
        method to get the tokens, else (by default), the tokens() method is 
        used.
        
        """
        self._pushback = False
        self._last = None
        self._doc = document = cursor.document
        start_block = document.block(cursor.start)
        self._wp = tokens_with_position
        tokens_method = document.tokens_with_position if tokens_with_position else document.tokens
        
        # start, end predicates
        start_pred, end_pred = {
            OUTSIDE: (
                lambda t: t.end < start_pos,
                lambda t: t.pos > end_pos,
            ),
            PARTIAL: (
                lambda t: t.end <= start_pos,
                lambda t: t.pos >= end_pos,
            ),
            INSIDE: (
                lambda t: t.pos < start_pos,
                lambda t: t.end > end_pos,
            ),
        }[partial]
        
        # if a state is given, use it (True: pick state from doc)
        if state:
            if state is True:
                state = document.state(start_block)
            def token_source(block):
                for t in tokens_method(block):
                    state.follow(t)
                    yield t
        else:
            def token_source(block):
                return iter(tokens_method(block))
        self.state = state
        
        # where to start
        if cursor.start:
            start_pos = cursor.start
            if not tokens_with_position:
                start_pos -= document.position(start_block)
            # token source for first block
            def source_start(block):
                source = token_source(block)
                for t in source:
                    if not start_pred(t):
                        yield t
                        for t in source:
                            yield t
        else:
            source_start = token_source
        
        # where to end
        if cursor.end is not None:
            end_block = cursor.end_block()
            end_pos = cursor.end 
            if not tokens_with_position:
                end_pos -= document.position(end_block)
            def source_end(source):
                for t in source:
                    if end_pred(t):
                        break
                    yield t
        
        # generate the tokens
        def generator():
            source = source_start
            block = start_block
            if cursor.end is not None:
                while block != end_block:
                    yield block, source(block)
                    source = token_source
                    block = document.next_block(block)
                yield block, source_end(source(block))
            else:
                for block in document.blocks_forward(start_block):
                    yield block, source(block)
                    source = token_source
        gen = generator()
        
        if tokens_with_position:
            def newline():
                pos = document.position(self.block) - 1
                return ly.lex.Newline('\n', pos)
        else:
            def newline():
                pos = len(document.text(document.previous_block(self.block)))
                return ly.lex.Newline('\n', pos)
        
        # initialize block and tokens
        for self.block, self.tokens in gen:
            break
        # keep them going after the first line
        def g():
            for t in self.tokens:
                yield t
            for self.block, self.tokens in gen:
                yield newline()
                for t in self.tokens:
                    yield t
        self._gen = g()
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._pushback:
            self._pushback = False
            return self._last
        i = self._last = next(self._gen)
        return i
    
    next = __next__
    
    def pushback(self, pushback=True):
        """Yields the last yielded token again on the next request.
        
        This can be called multiple times, but only the last token will be 
        yielded again. You can also undo a call to pushback() using 
        pushback(False).
        
        """
        self._pushback = pushback
    
    def token(self):
        """Re-returns the last yielded token."""
        return self._last
    
    @property
    def document(self):
        """Return our Document."""
        return self._doc
    
    def position(self, token):
        """Returns the position of the token in the current block.
        
        If the iterator was instantiated with tokens_with_position == True, 
        this position is the same as the token.pos attribute, and the current
        block does not matter. (In that case you'll probably not use this 
        method.)
        
        """
        pos = token.pos
        if not self._wp:
            pos += self._doc.position(self.block)
        return pos
    
    def until_parser_end(self):
        """Yield the tokens until the current parser is quit.
        
        You can only use this method if you have a State enabled.
        
        """
        depth = self.state.depth()
        for t in self:
            yield t
            if self.state.depth() < depth and not self._pushback:
                break
        
    def consume(self, iterable, position):
        """Consumes iterable (supposed to be reading from us) until position.
        
        Returns the last token if that overlaps position.
        
        """
        if self._doc.position(self.block) < position:
            for t in iterable:
                pos = self.position(t)
                end = pos + len(t)
                if end == position:
                    return
                elif end > position:
                    return t


