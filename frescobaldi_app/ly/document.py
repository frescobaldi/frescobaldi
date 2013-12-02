# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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

Represents a lilypond source document (the text contents).

The Document implementation keeps the document in a (unicode) text string,
but you can inherit from this class to support other representations of the
text content.

"""

from __future__ import unicode_literals
from __future__ import absolute_import

import sys
import operator
import collections


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
    
    """
    
    def __init__(self):
        """Constructor"""
        self._writing = 0
        self._changes = collections.defaultdict(list)
    
    def __nonzero__(self):
        return True
    
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
                self.apply_changes()
            self._writing = 0
            self._changes.clear()
        elif self._writing > 1:
            self._writing -= 1
    
    def check_changes(self):
        """Debugging method that checks for overlapping edits."""
        end = self.size()
        changes = sorted(self._changes.items(), reverse=True)
        for start, items in changes:
            for pos, text in items:
                if pos > end:
                    if len(text) > 12:
                        text = text[:10] + '...'
                    raise ValueError("overlapping edit: {0}-{1}: {2}".format(start, pos, text))
            end = start

    def apply_changes(self):
        """Apply the changes and update the tokens."""
        raise NotImplementedError()
        
    def tokens(self, block):
        """Return the tuple of tokens of the specified block."""
        raise NotImplementedError()

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
    
    def slice(self, block, token, start=0, end=None):
        """Return a slice describing the position of the token in the text.
        
        If start is given the slice will start at position start in the token
        (from the beginning of the token). Start defaults to 0.
        If end is given, the cursor will end at that position in the token (from
        the beginning of the token). End defaults to the length of the token.
       
        """
        pos = self.position(block) + token.pos
        start = pos + start
        end = pos + (len(token) if end is None else end)
        return slice(start, end)
    
    ##
    # text modifying methods
    ##
    
    def append(self, text):
        """Append text to the end of the document."""
        end = self.size()
        self[end:end] = text
    
    def insert(self, pos, text):
        """Insert text at position."""
        self[pos:pos] = text
    
    def remove(self, s):
        """Remove text at slice."""
        del self[s]
    
    def replace(self, s, text):
        """Replace text at slice."""
        self[s] = text
    
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
        self._changes[start].append((end, text.replace('\r', '')))

    def __delitem__(self, key):
        """Remove the range of text."""
        self[key] = ""


class Document(DocumentBase):
    """A plain text LilyPond source document
    
    that auto-updates the tokens.
    
    """
    def __init__(self):
        super(Document, self).__init__(text='')
        self.setplaintext(text)
    
    def __len__(self):
        """Return the number of blocks"""
        return len(self._blocks)
    
    def __getitem__(self, index):
        """Return the block at the specified index."""
        return self._blocks[index]
        
    def setplaintext(self, text):
        lines = text.replace('\r', '').split('\n')
        self._blocks = [Block(t, n) for n, t in enumerate(lines)]
        pos = 0
        for b in self._blocks:
            b.position = pos
            pos += len(b.text) + 1
        
        # TODO update all tokens
        
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
        changes = sorted(self._changes.items(), reverse=True)
        for start, items in changes:
            s = self.block(start)
            for end, text in items:
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
                    self._blocks[s.index+1:s.index+1] = map(Block, lines[1:])
                
        # update the position of all the new blocks
        pos = s.position
        for i, b in enumerate(self._blocks[s.index:], s.index):
            b.index = i
            b.position = pos
            pos += len(b.text) + 1
        
        # TODO update the tokens from block s



class Block(object):
    """A line of text."""
    
    position = sys.maxint  # prevent picking those blocks before updating pos
    state    = None
    tokens   = None
    
    def __init__(self, text="", index=-1):
        self.text = text
        self.index = index


