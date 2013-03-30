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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import tokeniter
import documentstructure


class Widget(QTreeWidget):
    def __init__(self, tool):
        super(Widget, self).__init__(tool,
            headerHidden=True)
        self._timer = QTimer(singleShot=True, timeout=self.updateView)
        tool.mainwindow().currentDocumentChanged.connect(self.slotCurrentDocumentChanged)
        doc = tool.mainwindow().currentDocument()
        if doc:
            self.slotCurrentDocumentChanged(doc)
    
    def slotCurrentDocumentChanged(self, doc, old):
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
            if last_block is None or depth == 1:
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
            item.setExpanded(True)
            item.depth = depth
            item.position = position
            last_block = block


