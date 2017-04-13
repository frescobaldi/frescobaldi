# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Use this module to get the parsed tokens of a document.

The tokens are created by the syntax highlighter, see highlighter.py.
The core methods of this module are tokens() and state(). These access
the token information from the highlighter, and also run the highlighter
if it has not run yet.

If you alter the document and directly after that need the new tokens,
use update().

"""


import collections

from PyQt5.QtGui import QTextBlock, QTextCursor

import cursortools
import highlighter


def tokens(block):
    """Returns the tokens for the given block as a (possibly empty) tuple."""
    try:
        return block.userData().tokens
    except AttributeError:
        # we used to call highlighter.highlighter(block.document()).rehighlight()
        # here, but there is a bug in PyQt-4.9.6 causing QTextBlockUserData to
        # lose its Python attributes. So we only run the highlighter when the
        # previous block's userState() is -1.
        return tuple(state(block).tokens(block.text()))


def state(block):
    """Return the ly.lex.State() object at the beginning of the given QTextBlock."""
    hl = highlighter.highlighter(block.document())
    if block.previous().userState() == -1 and block.blockNumber() > 0:
        hl.rehighlight()
    return hl.state(block.previous())


def state_end(block):
    """Return the ly.lex.State() object at the end of the given QTextBlock."""
    hl = highlighter.highlighter(block.document())
    if block.userState() == -1:
        hl.rehighlight()
    return hl.state(block)


def update(block):
    """Retokenize the given block, saving the tokens in the UserData.

    You only need to call this if you immediately need the new tokens again,
    e.g. for more manipulations in the same moment. The tokens will
    automatically be updated when Qt re-enters the event loop.

    """
    highlighter.highlighter(block.document()).rehighlightBlock(block)


def cursor(block, token, start=0, end=None):
    """Returns a QTextCursor for the given token in the given block.

    If start is given the cursor will start at position start in the token
    (from the beginning of the token). Start defaults to 0.
    If end is given, the cursor will end at that position in the token (from
    the beginning of the token). End defaults to the length of the token.

    """
    if end is None:
        end = len(token)
    cursor = QTextCursor(block)
    cursor.setPosition(block.position() + token.pos + start)
    cursor.setPosition(block.position() + token.pos + end, QTextCursor.KeepAnchor)
    return cursor


def find(text, tokens):
    """Finds text in tokens.

    Consumes the tokens iterable until a token with text text is found.
    Returns the found token or None.

    """
    if isinstance(tokens, (tuple, list)):
        try:
            i = tokens.index(text)
        except ValueError:
            return
        return tokens[i]
    for t in tokens:
        if t == text:
            return t


def index(cursor):
    """Returns the index of the token at the cursor (right or overlapping).

    The index can range from 0 (if there are no tokens or the cursor is in the
    first token) to the total count of tokens in the cursor's block (if the
    cursor is at the very end of the block).

    """
    block = cursortools.block(cursor)
    tokens_ = tokens(block)
    if cursor.atBlockEnd():
        return len(tokens_)
    pos = cursor.selectionStart() - block.position()
    lo, hi = 0, len(tokens_)
    while lo < hi:
        mid = (lo + hi) // 2
        if pos < tokens_[mid].pos:
            hi = mid
        else:
            lo = mid + 1
    return lo - 1


Partition = collections.namedtuple('Partition', 'left middle right')


def partition(cursor):
    """Returns a named three-tuple (left, middle, right).

    left is a tuple of tokens left to the cursor.
    middle is the token that overlaps the cursor at both sides (or None).
    right is a tuple of tokens right to the cursor.

    """
    block = cursortools.block(cursor)
    t = tokens(block)
    i = index(cursor)
    if t:
        if i < len(t) and t[i].pos < cursor.selectionStart() - block.position():
            return Partition(t[:i], t[i], t[i+1:])
    return Partition(t[:i], None, t[i:])


def all_tokens(document):
    """Yields all tokens of a document."""
    return (token for block in cursortools.all_blocks(document) for token in tokens(block))


