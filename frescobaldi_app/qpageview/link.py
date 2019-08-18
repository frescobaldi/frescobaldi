# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
Generic Link class and handling of links (clickable areas on a Page).

The link area is in coordinates between 0.0 and 1.0, like Poppler does it.
This way we can easily compute where the link area is on a page in different
sizes or rotations.

"""

import collections

from PyQt5.QtCore import pyqtSignal, QEvent, QRectF, Qt

from . import page
from . import rectangles

linkarea = collections.namedtuple("linkarea", "left top right bottom")


class Link:
    url = ""
    tooltip = ""
    area = linkarea(0, 0, 0, 0)

    def __init__(self, left, top, right, bottom, url=None, tooltip=None):
        self.area = linkarea(left, top, right, bottom)
        if url:
            self.url = url
        if tooltip:
            self.tooltip = tooltip

    def rect(self):
        """Return the area attribute as a QRectF()."""
        r = QRectF()
        r.setCoords(*self.area)
        return r


class Links(rectangles.Rectangles):
    """Manages a list of Link objects.
    
    See the rectangles documentation for how to access the links.
    
    """
    def get_coords(self, link):
        return link.area


class LinkViewMixin:
    """Mixin class to enhance view.View with link capabilities."""
    
    linkHovered = pyqtSignal(page.AbstractPage, Link)
    linkLeft = pyqtSignal()
    linkClicked = pyqtSignal(QEvent, page.AbstractPage, Link)

    linksEnabled = True

    def __init__(self, parent=None, **kwds):
        self._currentLinkId = None
        self._linkHighlighter = None
        super().__init__(parent, **kwds)
    
    def setLinkHighlighter(self, highlighter):
        """Sets a Highlighter (see highlight.py) to highlight a link on hover.
        
        Use None to remove an active Highlighter. By default no highlighter is
        set to highlight links on hover.
        
        To be able to actually *use* highlighting, be sure to also mix in the
        HighlightViewMixin class from the highlight module.
        
        """
        self._linkHighlighter = highlighter
    
    def linkHighlighter(self):
        """Return the currently set Highlighter, if any.
        
        By default no highlighter is set to highlight links on hover, and None
        is returned in that case.
        
        """
        return self._linkHighlighter

    def adjustCursor(self, pos):
        """Sets the correct mouse cursor for the position on the page.
        
        If `linksEnabled` is True, calls handleLinks()
        
        """
        if self.isDragging():
            return # Dragging the background is busy, see scrollarea.py.
        if self.linksEnabled:
            self.handleLinks(pos)
    
    def linkAt(self, pos):
        """If the pos (in the viewport) is over a link, return a (page, link) tuple.
        
        Otherwise returns (None, None).
        
        """
        pos = pos - self.layoutPosition()
        page = self._pageLayout.pageAt(pos)
        if page:
            links = page.linksAt(pos - page.pos())
            if links:
                return page, links[0]
        return None, None
        
    def handleLinks(self, pos):
        """Adjust the cursor for possible links at the specified position.
        
        Also emits signals when the cursor enters or leaves a link.
        
        """
        page, link = self.linkAt(pos)
        if link:
            lid = id(link)
        else:
            lid = None
        if lid != self._currentLinkId:
            if self._currentLinkId is not None:
                self.linkHoverLeave()
            self._currentLinkId = lid
            if lid is not None:
                self.linkHoverEnter(page, link)

    def linkHoverEnter(self, page, link):
        """Called when the mouse hovers over a link.

        The default implementation emits the linkHovered(page, link) signal,
        sets a pointing hand mouse cursor, and, if a Highlighter was set using
        setLinkHighlighter(), highlights the link. You can reimplement this
        method to do something different.
        
        """
        self.setCursor(Qt.PointingHandCursor)
        self.linkHovered.emit(page, link)
        if self._linkHighlighter:
            self.highlight(self._linkHighlighter, [(page, link.rect())], 3000)

    def linkHoverLeave(self):
        """Called when the mouse does not hover a link anymore.

        The default implementation emits the linkLeft() signal, sets a default
        mouse cursor, and, if a Highlighter was set using setLinkHighlighter(),
        removes the highlighting of the current link. You can reimplement this
        method to do something different.

        """
        self.unsetCursor()
        self.linkLeft.emit()
        if self._linkHighlighter:
            self.clearHighlight(self._linkHighlighter)

    def linkClickEvent(self, ev, page, link):
        """Called when a link is clicked.

        The default implementation emits the linkClicked(event, page, link)
        signal. The event can be used for thinks like determining which button
        was used, and which keyboard modifiers were in effect.

        """
        self.linkClicked.emit(ev, page, link)

    def mousePressEvent(self, ev):
        """Implemented to detect clicking a link and calling linkClickEvent()."""
        if self.handleLinks:
            page, link = self.linkAt(ev.pos())
            if link:
                self.linkClickEvent(ev, page, link)
                return
        super().mousePressEvent(ev)

    def leaveEvent(self, ev):
        """Implemented to leave a link, might there still be one hovered."""
        if self.handleLinks and self._currentLinkId is not None:
            self.linkHoverLeave()
            self._currentLinkId = None
 

