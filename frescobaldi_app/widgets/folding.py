# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 - 2012 by Wilbert Berendsen
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
(which are simply integers) in the order they occur on the line.

Then you should subclass FoldingArea, just to provide your Folder subclass
as a class attribute. Then add the FoldingArea to the left of your text edit.

Folding is handled automatically and needs no further data structures or state
information.

"""

from __future__ import unicode_literals

import collections

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import cursortools

START = 1
STOP = -1

Region = collections.namedtuple('Region', 'start end')


class LinePainter(QObject):
    """Paints a line below a block is the next block is invisible.
    
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
    
    You should inherit from this class to provide folding events,
    by implementing the fold_events() method.
    
    """
    def __init__(self, doc):
        QObject.__init__(self, doc)
    
    @classmethod
    def find(cls, doc):
        for c in doc.children():
            if type(c) is cls:
                return c
    
    @classmethod
    def get(cls, doc):
        return cls.find(doc) or cls(doc)
    
    def document(self):
        """Return our document."""
        return self.parent()
        
    def fold_events(self, block):
        """Return an iterable of fold events for the block.
        
        An event is simply an integer constant START or END.
        It is expected that END events come before START events!
        The default implementation returns nothing.
        
        """
        for c in block.text():
            if c == '{':
                yield START
            elif c == '}':
                yield STOP
    
    def fold_events_backwards(self, block):
        """Yield fold events in reverse order."""
        return list(self.fold_events(block))[::-1]
    
    def depth(self, block):
        """Return the number of active regions at the start of this block.
        
        The default implementation simply counts all the fold_events from
        the beginning of the document.
        
        """
        count = 0
        for block in cursortools.backwards(block.previous()):
            count += sum(self.fold_events(block))
        return count

    def is_active(self, block):
        """Return whether there is a fold active at the start of this block.
        
        The default implementation just looks backward until a START is found.
        
        """
        count = 0
        for block in cursortools.backwards(block.previous()):
            for ev in self.fold_events_backwards(block):
                count += ev
                if count > 0:
                    return True
        return False
    
    def region(self, block, depth=0):
        """Return as Region (start, end) the region of the specified block.
        
        start is the block the region starts, end the block the region ends.
        When collapsing the block, dont hide the last block if it starts a new
        fold region.
        
        The depth argument specifies how deep a region may be nested.
        The default value 0 searches the first containing region, 1 tries to
        find one more above that, etc. Use -1 to get the top-most region.
        
        """
        count = 0
        start = None
        for b in cursortools.backwards(block):
            s = sum(self.fold_events(b))
            if s > 0:
                start = b
            count += s
            if count > depth > -1:
                break
        if start:
            for end in cursortools.forwards(block.next()):
                for ev in self.fold_events(end):
                    count += ev
                    if count <= 0:
                        return Region(start, end)
            return Region(start, end)
        
    def fold(self, block, depth=0):
        """Folds the region the block is in."""
        r = self.region(block, depth)
        if not r:
            return
        # if the last block starts a new region, don't hide it
        count = 0
        end = r.end
        for ev in self.fold_events_backwards(r.end):
            count += ev
            if count > 0:
                end = r.end.previous()
                break
        # don't hide the first block of the region
        for block in cursortools.forwards(r.start.next(), end):
            block.setVisible(False)
        self.mark(r.start, True)
        self.document().markContentsDirty(r.start.position(), end.position())

    def unfold(self, block, depth=0, full=False):
        """Unfolds the region the block is in.
        
        (Most times the block will be the first block of the region.)
        If multiple regions start at the same starting block, they will unfold
        all.
        
        If full is False (the default) sub-regions that were collapsed remain
        collapsed (provided that the mark() method is implemented).
        
        """
        r = self.region(block, depth)
        if not r:
            return
        blocks = cursortools.forwards(r.start, r.end)
        if full:
            for block in blocks:
                block.setVisible(True)
        else:
            for block in blocks:
                # is there a sub-region? then skip if marked as collapsed
                if block not in r:
                    count = sum(self.fold_events(block))
                    if count > 0:
                        if full:
                            self.mark(block, False)
                        elif self.mark(block):
                            for block in blocks:
                                count += sum(self.fold_events(block))
                                if count <= 0:
                                    break
                            continue
                block.setVisible(True)
        self.mark(r.start, False)
        self.document().markContentsDirty(r.start.position(), r.end.position())
        
    def fold_all(self):
        """Folds all toplevel regions."""
        for block in cursortools.all_blocks(self.document()):
            if not block.isVisible():
                continue
            else:
                evs = list(self.fold_events(block))
                if any(evs) and sum(evs) >= 0:
                    self.fold(block)
    
    def unfold_all(self):
        """Fully unfolds the document."""
        first = None
        for block in cursortools.all_blocks(self.document()):
            evs = list(self.fold_events(block))
            if any(evs) and sum(evs) >= 0:
                self.mark(block, False)
            if not block.isVisible():
                if first is None:
                    first = block
                last = block
        if first:
            self.document().markContentsDirty(first.position(), last.position())
        
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
        for d in range(self.depth(block) - 1, -1, -1):
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
        
        def draw(self, rect, icon, depth, new_depth):
            p = self.p
            if depth:
                p.drawLine(rect.center(), QPoint(rect.center().x(), rect.y()))
            if new_depth:
                p.drawLine(rect.center(), QPoint(rect.center().x(), rect.bottom()))
            if new_depth < depth and not icon:
                p.drawLine(rect.center(), QPoint(rect.right(), rect.center().y()))
            if icon:
                square = QRect(0, 0, 8, 8)
                square.moveCenter(rect.center() - QPoint(1, 1))
                p.fillRect(square, self.w.palette().color(QPalette.Base))
                p.drawRect(square)
                x = rect.center().x()
                y = rect.center().y()
                p.drawLine(QPoint(x-2, y), QPoint(x+2, y))
                if icon == "open":
                    p.drawLine(QPoint(x, y-2), QPoint(x, y+2))
    
    def __init__(self, textedit=None):
        super(FoldingArea, self).__init__(textedit)
        self._textedit = None
        self.setAutoFillBackground(True)
        self.setTextEdit(textedit)
    
    def setTextEdit(self, edit):
        """Set a QPlainTextEdit instance to show linenumbers for, or None."""
        if self._textedit:
            self._textedit.updateRequest.disconnect(self.slotUpdateRequest)
        self._textedit = edit
        if edit:
            edit.updateRequest.connect(self.slotUpdateRequest)
        self.update()
        
    def textEdit(self):
        """Return our QPlainTextEdit."""
        return self._textedit
        
    def sizeHint(self):
        return QSize(12, 50)
    
    def folder(self):
        """Return the Folder instance for our document."""
        return self.Folder.get(self.textEdit().document())
        
    def slotUpdateRequest(self, rect, dy):
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

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
            if not block.isVisible():
                depth += sum(folder.fold_events(block))
                block = next_block
                continue
            rect = edit.blockBoundingGeometry(block).translated(offset).toRect()
            if rect.top() >= ev.rect().bottom():
                break
            rect.setX(0)
            rect.setWidth(self.width())
            # draw a folder icon, even if a fold ends and a new starts
            count = 0
            icon = None
            for e in folder.fold_events(block):
                count += e
                if count < 0:
                    icon = True
            if count < 0:
                icon = None
            elif count > 0:
                icon = True
            
            if icon:
                folded = next_block.isValid() and not next_block.isVisible()
                if folded:
                    icon = "open"
                    while next_block.isValid() and not next_block.isVisible():
                        count += sum(folder.fold_events(next_block))
                        next_block = next_block.next()
                else:
                    icon = "close"
            new_depth = depth + count
            painter.draw(rect, icon, depth, new_depth)
            depth = new_depth
            block = next_block



def visible_blocks(edit, rect=None):
    """Yield the visible blocks in the specified rectangle.
    
    If no rectangle is given, the edit's viewport() is used.
    
    """
    if rect is None:
        rect = edit.viewport().rect()
    for block in cursortools.forwards(edit.firstVisibleBlock()):
        if not block.isVisible():
            continue
        if not edit.blockBoundingGeometry(block).toRect() & rect:
            return
        yield block

