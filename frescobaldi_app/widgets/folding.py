# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 - 2017 by Wilbert Berendsen
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
Fold regions in a QTextDocument/Q(Plain)TextEdit.

Due to Qt4's design the folding applies to a QTextDocument instead of its
Q(Plain)TextEdit.

To get foldable regions in your QPlainTextEdit, you need to subclass Folder,
and implement its fold_events() method. It should yield START or STOP events
(which are simply integers) in the order they occur in the specified text block.

Then you should subclass FoldingArea, just to provide your Folder subclass
as a class attribute. Then add the FoldingArea to the left of your text edit.
The folding area will automatically instantiate the Folder for the document
of the text edit and use it for the lifetime of the document.

Finally, install a LinePainter as event filter on the viewport() of the text-
edit. This can be one global instance. It simply draws a line below any text
block that is followed by an invisible block.

Folding is handled automatically and needs no further data structures or state
information.

"""


import collections

from PyQt5.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, QTimer
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QWidget

import cursortools

START = 1
STOP = -1

OPEN = 1
CLOSE = -1

Region = collections.namedtuple('Region', 'start end')
Level = collections.namedtuple('Level', 'stop start')


class LinePainter(QObject):
    """Paints a line below a block if the next block is invisible.

    Install this as an event filter on the viewport() of a textedit,
    it then intercepts the paint event.

    """
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Paint:
            return self.paintEvent(obj, ev)
        return False

    def paintEvent(self, obj, ev):
        """Paint a line below a block is the next block is invisible.

        Normally it calls the paintEvent of the edit, then paints its
        own stuff and returns True.

        """
        edit = obj.parent()
        edit.paintEvent(ev)
        painter = QPainter(obj)
        offset = edit.contentOffset()
        for block in visible_blocks(edit, ev.rect()):
            n = block.next()
            if n.isValid() and not n.isVisible():
                # draw a line
                y = edit.blockBoundingGeometry(block).translated(offset).bottom() - 1
                x1 = ev.rect().left()
                x2 = ev.rect().right()
                painter.drawLine(x1, y, x2, y)
        return True


class Folder(QObject):
    """Manages the folding of a QTextDocument.

    You should inherit from this class to provide folding events.
    It is enough to implement the fold_events() method.

    By default, simple caching is used to store the nesting depth every
    20 lines. This makes the depth() method faster, which would otherwise count
    the fold_events() for every block from the beginning of the document.

    The depth() caching expects that the fold_events that a text block
    generates do not depend on the contents of a text block later in the
    document.

    If your fold_events() method generates events for a text block that depend
    on a later block, you should disable caching by setting the
    cache_depth_lines instance (or class) attribute to zero.

    """
    # cache depth() for every n lines (0=disable)
    cache_depth_lines = 20

    def __init__(self, doc):
        QObject.__init__(self, doc)
        self._depth_cache = []      # cache result of depth()
        self._all_visible = None    # True when all are certainly visible
        doc.contentsChange.connect(self.slot_contents_change)
        self._timer = QTimer(singleShot=True, timeout=self.check_consistency)

    @classmethod
    def find(cls, doc):
        for c in doc.children():
            if type(c) is cls:
                return c

    @classmethod
    def get(cls, doc):
        return cls.find(doc) or cls(doc)

    def slot_contents_change(self, position, removed, added):
        """Called when the document changes.

        Provides limited support for unhiding regions when the user types
        text in it, and deletes the depth() cache for lines from position.

        """
        block = self.document().findBlock(position)
        if self.cache_depth_lines:
            chunk = block.blockNumber() // self.cache_depth_lines
            del self._depth_cache[chunk:]

        if self._all_visible:
            return

        if not block.isVisible():
            self.ensure_visible(block)
        else:
            n = block.next()
            if n.isValid() and not n.isVisible() and not self.fold_level(block).start:
                # the block is visible, but not the next. Just unfold the lines,
                # skipping sub-regions, until a visible block is encountered.
                self.mark(block, False)
                while n.isValid() and not n.isVisible():
                    n.setVisible(True)
                    if self.fold_level(n).start and self.mark(n):
                        r = self.region(n)
                        if r:
                            n = r.end
                            if self.fold_level(n).start:
                                continue
                    n = n.next()
                start = block.next().position()
                self.document().markContentsDirty(start, n.position() - start)
        self._timer.start(250 + self.document().blockCount())

    def invalidate_depth_cache(self, block):
        """Makes sure the depth is recomputed from the specified block."""
        if self.cache_depth_lines:
            chunk = block.blockNumber() // self.cache_depth_lines
            del self._depth_cache[chunk:]

    def check_consistency(self):
        """Called some time after the last document change.

        Walk through the whole document, unfolding folded lines that
        - are in the toplevel
        - are in regions that have visible lines
        - are in regions that have visible sub-regions

        """
        show_blocks = []
        self._all_visible = True    # for now at least ...

        def blocks_gen():
            """Yield depth (before block), block and fold_level per block."""
            depth = 0
            for b in cursortools.all_blocks(self.document()):
                l = self.fold_level(b)
                yield depth, b, l
                depth += sum(l)

        blocks = blocks_gen()

        def check_region(start_block, start_depth):
            """Check a region from a starting block for visible lines.

            Return a four-tuple (must_show, depth, block, level).
            must_show is True if the region contains visible lines (in that case
                the invisible lines are already made visible)
            depth, block, and level are the result of the last block_gen yield.
            If level.start is True, a new region starts on the same line the
            former one ends.

            """
            must_show = False
            invisible_blocks = []
            start_block.isVisible() or invisible_blocks.append(start_block)
            for depth, block, level in blocks:
                block.isVisible() or invisible_blocks.append(block)
                if depth + level.stop < start_depth:
                    # the region ends
                    if block.isVisible() and not level.start:
                        must_show = True
                    if must_show:
                        show_blocks.extend(invisible_blocks)
                    elif invisible_blocks:
                        self._all_visible = False
                    return must_show, depth, block, level
                elif block.isVisible():
                    must_show = True
                while level.start:
                    must_show_region, depth, block, level = check_region(block, depth + sum(level))
                    if must_show_region:
                        must_show = True
            # happens if region is not closed
            return must_show, 0, None, Level(0, 0)

        # toplevel
        for depth, block, level in blocks:
            block.isVisible() or show_blocks.append(block)
            while level.start:
                must_show, depth, block, level = check_region(block, depth + sum(level))

        if show_blocks:
            for block in show_blocks:
                block.setVisible(True)
            start = show_blocks[0].position()
            end = show_blocks[-1].position() + show_blocks[-1].length()
            self.document().markContentsDirty(start, end - start)

    def document(self):
        """Return our document."""
        return self.parent()

    def fold_events(self, block):
        """Return an iterable of fold events for the block.

        An event is simply an integer constant START or END.
        The default implementation considers '{' as a start and '}' as end.

        """
        for c in block.text():
            if c == '{':
                yield START
            elif c == '}':
                yield STOP

    def fold_level(self, block):
        """Returns a named two-tuple Level(stop, start) about the block.

        stop is the number (negative!) of fold-levels that end in that block,
        start is the number of fold-levels that start in that block.

        This methods uses fold_events() to get the information, it discards
        folding regions that start and stop on the same text line.

        """
        start, stop = 0, 0
        for e in self.fold_events(block):
            if e is START:
                start += 1
            elif start:
                start -= 1
            else:
                stop -= 1
        return Level(stop, start)

    def depth(self, block):
        """Return the number of active regions at the start of this block.

        The default implementation simply counts all the fold_events from
        the beginning of the document, using caching if the cache_depth_lines
        instance attribute is set to a value > 0.

        """
        depth = 0
        last = block.document().firstBlock()
        if self.cache_depth_lines:
            chunk = block.blockNumber() // self.cache_depth_lines
            if chunk:
                target = block.document().findBlockByNumber(chunk * self.cache_depth_lines)
                if chunk <= len(self._depth_cache):
                    depth = self._depth_cache[chunk - 1]
                    last = target
                else:
                    # some values need to be computed first
                    if self._depth_cache:
                        depth = self._depth_cache[-1]
                        last = block.document().findBlockByNumber(len(self._depth_cache) * self.cache_depth_lines)
                    while last < target:
                        depth += sum(self.fold_events(last))
                        last = last.next()
                        if last.blockNumber() % self.cache_depth_lines == 0:
                            self._depth_cache.append(depth)
        while last < block:
            depth += sum(self.fold_events(last))
            last = last.next()
        return depth

    def region(self, block, depth=0):
        """Return as Region (start, end) the region of the specified block.

        start is the block the region starts, end the block the region ends.
        When collapsing the block, don't hide the last block if it starts a new
        fold region.

        The depth argument specifies how deep a region may be nested.
        The default value 0 searches the first containing region, 1 tries to
        find one more above that, etc. Use -1 to get the top-most region.

        """
        start = None
        start_depth = 0
        count = 0
        for b in cursortools.backwards(block):
            l = self.fold_level(b)
            if l.start:
                count += l.start
                if count > start_depth:
                    start = b
                    start_depth = count
                    if count > depth > -1:
                        break
            count += l.stop
        if start:
            count = start_depth
            end = None
            for end in cursortools.forwards(block.next()):
                l = self.fold_level(end)
                if count <= -l.stop:
                    return Region(start, end)
                count += sum(l)
            if end:
                return Region(start, end)

    def fold(self, block, depth=0):
        """Fold the region the block is in.

        The depth argument specifies how deep a region may be nested.
        The default value 0 searches the first containing region, 1 tries to
        find one more above that, etc. Use -1 to get the top-most region.

        """
        r = self.region(block, depth)
        if not r:
            return
        # if the last block starts a new region, don't hide it
        count = 0
        end = r.end.previous() if self.fold_level(r.end).start else r.end
        # don't hide the first block of the region
        for block in cursortools.forwards(r.start.next(), end):
            block.setVisible(False)
        self.mark(r.start, True)
        start = r.start.next().position()
        self.document().markContentsDirty(start, end.position() - start)
        self._all_visible = False

    def unfold(self, block, depth=0, full=False):
        """Unfolds the region the block is in.

        (Most times the block will be the first block of the region.)
        If multiple regions start at the same starting block, they will unfold
        all.

        The depth argument specifies how deep a region may be nested.
        The default value 0 searches the first containing region, 1 tries to
        find one more above that, etc. Use -1 to get the top-most region.

        If full is False (the default) sub-regions that were collapsed remain
        collapsed (provided that the mark() method is implemented).

        """
        r = self.region(block, depth)
        if not r:
            return
        blocks = cursortools.forwards(r.start, r.end)
        for block in blocks:
            # is there a sub-region? then skip if marked as collapsed
            if block not in r:
                l = self.fold_level(block)
                if l.start:
                    if full:
                        self.mark(block, False)
                    elif self.mark(block):
                        count = l.start
                        for b in blocks:
                            l = self.fold_level(b)
                            if count <= -l.stop:
                                break
                            count += sum(l)
            block.setVisible(True)
        self.mark(r.start, False)
        start = r.start.position()
        self.document().markContentsDirty(start, r.end.position() - start)

    def fold_toplevel(self):
        """Folds all toplevel regions, without touching inner regions."""
        for block in cursortools.all_blocks(self.document()):
            if not block.isVisible():
                continue
            elif self.fold_level(block).start:
                self.fold(block)

    def fold_all(self):
        """Folds all regions."""
        for block in cursortools.all_blocks(self.document()):
            if self.fold_level(block).start:
                if block.isVisible():
                    self.fold(block)
                else:
                    self.mark(block, True)

    def unfold_all(self):
        """Fully unfolds the document."""
        first = None
        for block in cursortools.all_blocks(self.document()):
            if self.fold_level(block).start:
                self.mark(block, False)
            if not block.isVisible():
                block.setVisible(True)
                if first is None:
                    first = block
                last = block
        if first:
            self.document().markContentsDirty(first.position(), last.position() - first.position())
        # no need to check consistency
        self._all_visible = True
        self._timer.isActive() and self._timer.stop()

    def mark(self, block, state=None):
        """This can be used to remember the folded state of a block.

        When folding or unfolding a block, this method is called with the first
        block and state True (for fold) or False (for unfold).

        When unfolding a region, this method is called for every block without
        state value, and its return value is checked. If the value evaluates to
        True, the sub-region will remain collapsed.

        The default implementation does, and returns, nothing.

        """
        pass

    def ensure_visible(self, block):
        """Unfolds everything needed to make just the block visible."""
        if block.isVisible():
            return
        for d in range(self.depth(block), -1, -1):
            self.unfold(block, d)
            if block.isVisible():
                return


class FoldingArea(QWidget):

    Folder = Folder

    class Painter(object):
        """Used for one paint event, draws the folding area per-block."""
        def __init__(self, widget):
            self.w = widget
            self.p = QPainter(widget)

        def draw(self, rect, indicator, depth, new_depth):
            p = self.p
            if depth:
                p.drawLine(rect.center(), QPoint(rect.center().x(), rect.y()))
            if new_depth:
                p.drawLine(rect.center(), QPoint(rect.center().x(), rect.bottom()))
            if new_depth < depth and not indicator:
                p.drawLine(rect.center(), QPoint(rect.right()-1, rect.center().y()))
            if indicator:
                square = QRect(0, 0, 8, 8)
                square.moveCenter(rect.center() - QPoint(1, 1))
                p.fillRect(square, self.w.palette().color(QPalette.Base))
                p.drawRect(square)
                x = rect.center().x()
                y = rect.center().y()
                p.drawLine(QPoint(x-2, y), QPoint(x+2, y))
                if indicator == OPEN:
                    p.drawLine(QPoint(x, y-2), QPoint(x, y+2))

    def __init__(self, textedit=None):
        super(FoldingArea, self).__init__(textedit)
        self._textedit = None
        self.setAutoFillBackground(True)
        self.setTextEdit(textedit)

    def setTextEdit(self, edit):
        """Set a QPlainTextEdit instance to show folding indicators for, or None."""
        if self._textedit:
            self._textedit.updateRequest.disconnect(self.slotUpdateRequest)
            self._textedit.cursorPositionChanged.disconnect(self.slotCursorPositionChanged)
        self._textedit = edit
        if edit:
            edit.updateRequest.connect(self.slotUpdateRequest)
            edit.cursorPositionChanged.connect(self.slotCursorPositionChanged)
        self.update()

    def textEdit(self):
        """Return our QPlainTextEdit."""
        return self._textedit

    def sizeHint(self):
        return QSize(11, 50)

    def folder(self):
        """Return the Folder instance for our document."""
        return self.Folder.get(self.textEdit().document())

    def slotUpdateRequest(self, rect, dy):
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

    def slotCursorPositionChanged(self):
        """Unfold the block the cursor is in if it is invisible."""
        block = self.textEdit().textCursor().block()
        if not block.isVisible():
            self.folder().ensure_visible(block)
            self.textEdit().ensureCursorVisible()

    def paintEvent(self, ev):
        edit = self._textedit
        if not edit:
            return
        painter = self.Painter(self)
        block = edit.firstVisibleBlock()
        folder = self.folder()
        depth = folder.depth(block)
        offset = edit.contentOffset()
        while block.isValid():
            next_block = block.next()
            level = folder.fold_level(block)
            count = sum(level)
            if block.isVisible():
                rect = edit.blockBoundingGeometry(block).translated(offset).toRect()
                if rect.top() > ev.rect().bottom():
                    break
                elif rect.bottom() >= ev.rect().top():
                    rect.setX(0)
                    rect.setWidth(self.width())
                    # draw a folder indicator
                    if level.start:
                        folded = next_block.isValid() and not next_block.isVisible()
                        if folded:
                            indicator = OPEN
                            while next_block.isValid() and not next_block.isVisible():
                                count += sum(folder.fold_events(next_block))
                                next_block = next_block.next()
                        else:
                            indicator = CLOSE
                    else:
                        indicator = None
                    painter.draw(rect, indicator, depth, depth + count)
            depth += count
            block = next_block

    def mousePressEvent(self, ev):
        if ev.buttons() == Qt.LeftButton:
            block = self.textEdit().cursorForPosition(QPoint(0, ev.y())).block()
            folder = self.folder()
            if folder.fold_level(block).start:
                if block.next().isValid() and not block.next().isVisible():
                    folder.unfold(block)
                else:
                    folder.fold(block)


def visible_blocks(edit, rect=None):
    """Yield the visible blocks in the specified rectangle.

    If no rectangle is given, the edit's viewport() is used.

    """
    if rect is None:
        rect = edit.viewport().rect()
    offset = edit.contentOffset()
    for block in cursortools.forwards(edit.firstVisibleBlock()):
        if block.isVisible():
            geom = edit.blockBoundingGeometry(block).translated(offset).toRect()
            if geom.top() >= rect.bottom():
                return
            elif geom.bottom() >= rect.top():
                yield block

