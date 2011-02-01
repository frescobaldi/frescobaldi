# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
Surface is the widget everything is drawn on.
"""

import weakref


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4

from . import layout


class Surface(QWidget):
    def __init__(self, view):
        super(Surface, self).__init__(view)
        self.setBackgroundRole(QPalette.Dark)
        self._view = weakref.ref(view)
        self._pageLayout = None
        self.setPageLayout(layout.Layout())
        self.setMouseTracking(True)
        self._currentLinkRect = QRect()
        
    def pageLayout(self):
        return self._pageLayout
        
    def setPageLayout(self, layout):
        old, self._pageLayout = self._pageLayout, layout
        if old:
            old.redraw.disconnect(self.update)
        layout.redraw.connect(self.update)
        
    def updateLayout(self):
        """Conforms ourselves to our layout (that must already be updated.)"""
        self.resize(self._pageLayout.size())
        self.update()
        
    def paintEvent(self, ev):
        painter = QPainter(self)
        for page in self.pageLayout().pagesAt(ev.rect()):
            page.paint(painter, ev.rect())
    
    def mouseMoveEvent(self, ev):
        if ev.pos() in self._currentLinkRect:
            return
        link = None
        p = self.pageLayout().pageAt(ev.pos())
        if p:
            links = p.linksAt(ev.pos())
            if links:
                link = links[0]
        if link:
            self._currentLinkRect = p.linkRect(link)
            self.setCursor(Qt.PointingHandCursor)
        else:
            self._currentLinkRect = QRect()
            self.unsetCursor()
    
    def event(self, ev):
        if isinstance(ev, QHelpEvent):
            p = self.pageLayout().pageAt(ev.pos())
            if p:
                links = p.linksAt(ev.pos())
                if links:
                    link = links[0]
                    QToolTip.showText(ev.globalPos(), link.url(), self, p.linkRect(link))
            return True
        return super(Surface, self).event(ev)


