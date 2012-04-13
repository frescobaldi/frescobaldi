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

"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *


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
        for block in self.visible_blocks(edit, ev.rect()):
            n = block.next()
            if n.isValid() and not n.isVisible():
                # draw a line
                y = edit.blockBoundingGeometry(block).translated(offset).bottom() - 1
                x1 = ev.rect().left()
                x2 = ev.rect().right()
                painter.drawLine(x1, y, x2, y)
        return True


    @staticmethod
    def visible_blocks(edit, rect=None):
        """Yield the visible blocks in the specified rectangle.
        
        If no rectangle is given, the edit's viewport() is used.
        
        """
        if rect is None:
            rect = edit.viewport().rect()
        block = edit.firstVisibleBlock()
        while block.isValid():
            if not block.isVisible():
                continue
            if not edit.blockBoundingGeometry(block).toRect() & rect:
                return
            yield block
            block = block.next()


