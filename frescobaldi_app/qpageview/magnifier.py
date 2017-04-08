# This file is part of the qpageview package.
#
# Copyright (c) 2010 - 2016 by Wilbert Berendsen
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
The Magnifier magnifies a part of the displayed document.
"""

import weakref

from PyQt5.QtCore import QEvent, QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QCursor, QPainter, QPalette, QPen, QRegion
from PyQt5.QtWidgets import QWidget


DRAG_SHORT = 1      # visible only while keeping the mouse button pressed
DRAG_LONG  = 2      # remain visible and drag when picked up with the mouse



class Magnifier(QWidget):
    """A Magnifier is added to a View with surface.setMagnifier().

    It is shown when a mouse button is pressed together with a modifier
    (by default Ctrl). It can then be resized by moving the mouse is with
    two buttons pressed, or by wheeling with resizemodifier pressed.

    Its size can be changed with resize() and the scale (defaulting to 3.0)
    with setScale().

    If can also be shown programatically with the show() method. In this case
    it can be dragged with the left mouse button.

    Wheel zooming with the modifier (by default Ctrl) zooms the magnifier.

    Instance attributes:

        showmodifier: the modifier to popup (Qt.ControlModifier)

        zoommodifier: the modifier to wheel zoom (Qt.ControlModifier)

        resizemodifier: the key to press for wheel resizing (Qt.ShiftModifier)

        showbutton: the mouse button causing the magnifier to popup (by default
                    Qt.LeftButton)

        resizebutton: the extra mouse button to be pressed when resizing the
                    magnifier (by default Qt.RightButton)

        MAX_EXTRA_ZOOM: the maximum zoom (relative to the View's maximum zoom
                    level)


    """

    # modifier for show
    showmodifier = Qt.ControlModifier

    # modifier for wheel zoom
    zoommodifier = Qt.ControlModifier

    # extra modifier for wheel resize
    resizemodifier = Qt.ShiftModifier

    # button for show
    showbutton = Qt.LeftButton

    # extra button for resizing
    resizebutton = Qt.RightButton

    # Maximum extra zoom above the View.MAX_ZOOM
    MAX_EXTRA_ZOOM = 1.25

    # Minimal size
    MIN_SIZE = 20


    def __init__(self):
        super().__init__()
        self._dragging = False
        self._resizepos = None
        self._resizewidth = 0
        self._pages = weakref.WeakKeyDictionary()
        self._scale = 3.0
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Dark)
        self.resize(250, 250)
        self.hide()

    def moveCenter(self, pos):
        """Called by the View, centers the widget on the given QPoint."""
        r = self.geometry()
        r.moveCenter(pos)
        self.setGeometry(r)

    def setScale(self, scale):
        """Sets the scale, relative to the dislayed size in the View."""
        self._scale = scale
        self.update()

    def scale(self):
        """Returns the scale, defaulting to 3.0 (=300%)."""
        return self._scale

    def resizeEvent(self, ev):
        """Called on resize, sets our circular mask."""
        self.setMask(QRegion(self.rect(), QRegion.Ellipse))

    def eventFilter(self, viewport, ev):
        """Handles multiple events from the viewport.

        * update on View scroll
        * show the magnifier on left click+modifier

        """
        if ev.type() == QEvent.UpdateRequest:
            self.update()
        elif (not self.isVisible() and
              ev.type() == QEvent.MouseButtonPress and
              ev.modifiers() == self.showmodifier and
              ev.button() == self.showbutton):
            # show and drag while button pressed: DRAG_SHORT
            self._dragging = DRAG_SHORT
            self.moveCenter(ev.pos())
            self.show()
            viewport.setCursor(Qt.BlankCursor)
            return True
        elif self._dragging == DRAG_SHORT:
            if ev.type() == QEvent.MouseMove:
                if ev.buttons() == self.showbutton | self.resizebutton:
                    # DRAG_SHORT is busy, both buttons are pressed: resize!
                    if self._resizepos == None:
                        self._resizepos = ev.pos()
                        self._resizewidth = self.width()
                        dy = 0
                    else:
                        dy = (ev.pos() - self._resizepos).y()
                    g = self.geometry()
                    w = max(self.MIN_SIZE, self._resizewidth + 2 * dy)
                    self.resize(w, w)
                    self.moveCenter(g.center())
                else:
                    # just drag our center
                    self.moveCenter(ev.pos())
                    view = self.parent().parent()
                    view.scrollForDragging(ev.pos())
                return True
            elif ev.type() == QEvent.MouseButtonRelease:
                if ev.button() == self.showbutton:
                    # left button is released, stop dragging and/or resizing, hide
                    viewport.unsetCursor()
                    self.hide()
                    self._resizepos = None
                    self._dragging = False
                    view = self.parent().parent()
                    view.stopScrolling() # just if needed
                elif ev.button() == self.resizebutton:
                    # right button is released, stop resizing, warp cursor to center
                    self._resizepos = None
                    QCursor.setPos(viewport.mapToGlobal(self.geometry().center()))
                return True
        return False

    def mousePressEvent(self, ev):
        """Start dragging the magnifier."""
        ev.ignore() # don't propagate to view
        if self._dragging != DRAG_SHORT and ev.button() == Qt.LeftButton:
            self._dragging = DRAG_LONG
            self._dragpos = ev.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        """Move the magnifier if we were dragging it."""
        ev.ignore() # don't propagate to view
        if self._dragging == DRAG_LONG:
            pos = self.mapToParent(ev.pos())
            self.move(pos - self._dragpos)
            view = self.parent().parent()
            view.scrollForDragging(pos)

    def mouseReleaseEvent(self, ev):
        """The button is released, stop moving ourselves."""
        ev.ignore() # don't propagate to view
        if ev.button() == Qt.LeftButton and self._dragging == DRAG_LONG:
            self._dragging = False
            self.unsetCursor()
            view = self.parent().parent()
            view.stopScrolling() # just if needed

    def wheelEvent(self, ev):
        """Implement zooming the magnifying glass."""
        if ev.modifiers() & self.zoommodifier:
            ev.accept()
            if ev.modifiers() & self.resizemodifier:
                factor = 1.1 ** (ev.angleDelta().y() / 120)
                g = self.geometry()
                c = g.center()
                g.setWidth(max(g.width() * factor, self.MIN_SIZE))
                g.setHeight(max(g.height() * factor, self.MIN_SIZE))
                g.moveCenter(c)
                self.setGeometry(g)
            else:
                factor = 1.1 ** (ev.angleDelta().y() / 120)
                self.setScale(self._scale * factor)
        else:
            super().wheelEvent(ev)

    def paintEvent(self, ev):
        """Called when paint is needed, finds out which page to magnify."""
        view = self.parent().parent()
        layout = view.pageLayout()

        scale = max(min(self._scale, view.MAX_ZOOM * self.MAX_EXTRA_ZOOM / layout.zoomFactor), view.MIN_ZOOM / layout.zoomFactor)

        # the position of our center on the layout
        c = self.rect().center() + self.pos() - view.layoutPosition()

        # make a region scaling back to the view scale
        rect = QRect(0, 0, self.width() / scale, self.height() / scale)
        rect.moveCenter(c)
        region = QRegion(rect, QRegion.Ellipse) # touches the Pages we need to draw

        # our rect on the enlarged pages
        our_rect = self.rect()
        our_rect.moveCenter(QPoint(c.x() * scale, c.y() * scale))

        # the virtual position of the whole scaled-up layout
        ev_rect = ev.rect().translated(our_rect.topLeft())

        painter = QPainter(self)
        for p in layout.pagesAt(region):
            # reuse the copy of the page if still existing
            try:
                page = self._pages[p]
            except KeyError:
                page = self._pages[p] = p.copy()
            page.x = p.x * scale
            page.y = p.y * scale
            page.width = p.width * scale
            page.height = p.height * scale
            # now paint it
            rect = (page.rect() & ev_rect).translated(-page.pos())
            painter.save()
            painter.translate(page.pos() - our_rect.topLeft())
            page.paint(painter, rect, self.repaintPage)
            painter.restore()

        self.drawBorder(painter)

    def drawBorder(self, painter):
        """Draw a nice looking glass border."""
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(192, 192, 192, 128), 6))
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

    def repaintPage(self, page):
        """Called when a Page was rendered in the background."""
        ## TODO: smarter determination which part to update
        self.update()


