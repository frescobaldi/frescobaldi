# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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
The View, deriving from QAbstractScrollArea.
"""



from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QAbstractScrollArea


from . import layout



class View(QAbstractScrollArea):
    
    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._pageLayout = layout.PageLayout()
        self.horizontalScrollBar().valueChanged.connect(self.update)
        self.verticalScrollBar().valueChanged.connect(self.update)        
    
    def setPageLayout(self, layout):
        """Set our current PageLayout instance."""
        self._pageLayout = layout
    
    def pageLayout(self):
        """Return our current PageLayout instance."""
        return self._pageLayout
    
    def updatePageLayout(self):
        """Update layout and adjust scrollbars."""
        self._pageLayout.update()
        self.updateScrollBars()
    
    def updateScrollBars(self):
        """Adjust the range of the scrollbars to the layout."""
        height = self._pageLayout.height() - self.viewport().height()
        self.verticalScrollBar().setRange(0, height)
        self.verticalScrollBar().setPageStep(self.viewport().height())
        width = self._pageLayout.width() - self.viewport().width()
        self.horizontalScrollBar().setRange(0, width)
        self.horizontalScrollBar().setPageStep(self.viewport().width())
    
    def resizeEvent(self, ev):
        """Reimplemented to update the scrollbars."""
        self.updateScrollBars()
    
    def paintEvent(self, ev):
        rect = self.viewport().rect().translated(
            self.horizontalScrollBar().value(),
            self.verticalScrollBar().value())
        print (rect)

