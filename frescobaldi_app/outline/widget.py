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
The document outline tool widget.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QEvent, QTimer
from PyQt4.QtGui import QTextCursor, QTreeWidget, QTreeWidgetItem

import app
import qutil
import cursortools
import tokeniter
import documentstructure


class Widget(QTreeWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool,
            headerHidden=True)
        self._timer = QTimer(singleShot=True, timeout=self.updateView)
        tool.mainwindow().currentDocumentChanged.connect(self.slotCurrentDocumentChanged)
        self.itemClicked.connect(self.slotItemClicked)
        self.itemActivated.connect(self.slotItemClicked)
        self.itemCollapsed.connect(self.slotItemCollapsed)
        self.itemExpanded.connect(self.slotItemExpanded)
        doc = tool.mainwindow().currentDocument()
        if doc:
            self.slotCurrentDocumentChanged(doc)
    
    def slotCurrentDocumentChanged(self, doc, old=None):
        """Called whenever the mainwindow changes the current document."""
        if old:
            old.contentsChange.disconnect(self.slotContentsChange)
        if doc:
            doc.contentsChange.connect(self.slotContentsChange)
            self._timer.start(100)
            
    def slotContentsChange(self, position, added, removed):
        """Updates the view on contents change."""
        if added + removed > 1000:
            self._timer.start(100)
        else:
            self._timer.start(2000)
        
    def updateView(self):
        """Recreate the items in the view."""
        with qutil.signalsBlocked(self):
            self.clear()
            doc = self.parent().mainwindow().currentDocument()
            if not doc:
                return
            structure = documentstructure.DocumentStructure.instance(doc)
            last_item = None
            last_block = None
            for i in structure.outline():
                position = i.start()
                block = doc.findBlock(position)
                depth = tokeniter.state(block).depth()
                if block == last_block:
                    parent = last_item
                elif last_block is None or depth == 1:
                    # a toplevel item anyway
                    parent = self
                else:
                    while last_item and depth <= last_item.depth:
                        last_item = last_item.parent()
                    if not last_item:
                        parent = self
                    else:
                        # the item could belong to a parent item, but see if they
                        # really are in the same (toplevel) state
                        b = last_block.next()
                        while b < block:
                            depth2 = tokeniter.state(b).depth()
                            if depth2 == 1:
                                parent = self
                                break
                            while last_item and depth2 <= last_item.depth:
                                last_item = last_item.parent()
                            if not last_item:
                                parent = self
                                break
                            b = b.next()
                        else:
                            parent = last_item
                item = last_item = QTreeWidgetItem(parent)
                item.setText(0, i.group())
                try:
                    collapsed = block.userData().collapsed
                except AttributeError:
                    collapsed = False
                item.setExpanded(not collapsed)
                item.depth = depth
                item.position = position
                last_block = block
    
    def cursorForItem(self, item):
        """Returns a cursor for the specified item.
        
        This method (as all others) assume that the item refers to the current
        Document.
        
        """
        doc = self.parent().mainwindow().currentDocument()
        cursor = QTextCursor(doc)
        cursor.setPosition(item.position)
        return cursor
        
    def slotItemClicked(self, item):
        """Called when the user clicks an item."""
        cursor = self.cursorForItem(item)
        cursor.movePosition(cursor.StartOfBlock)
        view = self.parent().mainwindow().currentView()
        view.setTextCursor(cursor)
        view.centerCursor()
        view.setFocus()

    def slotItemCollapsed(self, item):
        """Called when the user collapses an item."""
        block = self.cursorForItem(item).block()
        cursortools.data(block).collapsed = True
    
    def slotItemExpanded(self, item):
        """Called when the user expands an item."""
        block = self.cursorForItem(item).block()
        cursortools.data(block).collapsed = False

    def event(self, ev):
        """Reimplemented to show custom tool tips."""
        if ev.type() == QEvent.ToolTip:
            i = self.indexAt(ev.pos() - self.viewport().pos())
            item = self.itemFromIndex(i)
            if item:
                self.showToolTip(item)
                return True
        return super(Widget, self).event(ev)

    def showToolTip(self, item):
        """Called when a tool tip for the specified item needs to be shown."""
        import documenttooltip
        documenttooltip.show(self.cursorForItem(item))


