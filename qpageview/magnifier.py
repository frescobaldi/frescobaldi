# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2010 - 2019 by Wilbert Berendsen
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

from PyQt5.QtCore import QEvent, QPoint, QRect, Qt
from PyQt5.QtGui import (
    QColor, QCursor, QPainter, QPalette, QPen, QRegion, QTransform)
from PyQt5.QtWidgets import QWidget


DRAG_SHORT = 1      # visible only while keeping the mouse button pressed
DRAG_LONG  = 2      # remain visible and drag when picked up with the mouse



class Magnifier(QWidget):
    """A Magnifier is added to a View with view.setMagnifier().

    It is shown when a mouse button is pressed together with a modifier
    (by default Ctrl). It can then be resized by moving the mouse is with
    two buttons pressed, or by wheeling with resizemodifier pressed.

    Its size can be changed with resize() and the scale (defaulting to 3.0)
    with setScale().

    If can also be shown programatically with the show() method. In this case
    it can be dragged with the left mouse button.

    Wheel zooming with the modifier (by default Ctrl) zooms the magnifier.

    Instance attributes:

    ``showmodifier``:
        the modifier to popup (Qt.ControlModifier)

    ``zoommodifier``:
        the modifier to wheel zoom (Qt.ControlModifier)

    ``resizemodifier``:
        the key to press for wheel resizing (Qt.ShiftModifier)

    ``showbutton``:
        the mouse button causing the magnifier to popup (by default
        Qt.LeftButton)

    ``resizebutton``:
        the extra mouse button to be pressed when resizing the
        magnifier (by default Qt.RightButton)

    ``MAX_EXTRA_ZOOM``:
        the maximum zoom (relative to the View's maximum zoom
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
    MIN_SIZE = 50

    # Maximal size
    MAX_SIZE = 640

    def __init__(self):
        super().__init__()
        self._dragging = False
        self._resizepos = None
        self._resizewidth = 0
        self._scale = 3.0
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Dark)
        self.resize(350, 350)
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

    def startShortDrag(self, pos):
        """Start a short drag (e.g. on ctrl+click)."""
        viewport = self.parent()
        self._dragging = DRAG_SHORT
        self.moveCenter(pos)
        self.raise_()
        self.show()
        viewport.setCursor(Qt.BlankCursor)

    def endShortDrag(self):
        """End a short drag."""
        viewport = self.parent()
        view = viewport.parent()
        viewport.unsetCursor()
        self.hide()
        self._resizepos = None
        self._dragging = False
        view.stopScrolling() # just if needed

    def startLongDrag(self, pos):
        """Start a long drag (when we are already visible and then dragged)."""
        self._dragging = DRAG_LONG
        self._dragpos = pos
        self.setCursor(Qt.ClosedHandCursor)

    def endLongDrag(self):
        """End a long drag."""
        self._dragging = False
        self.unsetCursor()
        view = self.parent().parent()
        view.stopScrolling() # just if needed

    def resizeEvent(self, ev):
        """Called on resize, sets our circular mask."""
        self.setMask(QRegion(self.rect(), QRegion.Ellipse))

    def moveEvent(self, ev):
        """Called on move, updates the contents."""
        # we also update on paint events, but they are not generated if the
        # magnifiers fully covers the viewport
        self.update()

    def eventFilter(self, viewport, ev):
        """Handle events on the viewport of the View."""
        view = viewport.parent()
        if not self.isVisible():
            if (ev.type() == QEvent.MouseButtonPress and
                ev.modifiers() == self.showmodifier and
                ev.button() == self.showbutton):
                # show and drag while button pressed: DRAG_SHORT
                self.startShortDrag(ev.pos())
                return True
        elif ev.type() == QEvent.Paint:
            # if the viewport is painted, also update
            self.update()
        elif self._dragging == DRAG_SHORT:
            if ev.type() == QEvent.MouseButtonPress:
                if ev.button() == self.resizebutton:
                    return True
            elif ev.type() == QEvent.MouseMove:
                if ev.buttons() == self.showbutton | self.resizebutton:
                    # DRAG_SHORT is busy, both buttons are pressed: resize!
                    if self._resizepos == None:
                        self._resizepos = ev.pos()
                        self._resizewidth = self.width()
                        dy = 0
                    else:
                        dy = (ev.pos() - self._resizepos).y()
                    g = self.geometry()
                    w = min(max(self.MIN_SIZE, self._resizewidth + 2 * dy), self.MAX_SIZE)
                    self.resize(w, w)
                    self.moveCenter(g.center())
                else:
                    # just drag our center
                    self.moveCenter(ev.pos())
                    view.scrollForDragging(ev.pos())
                return True
            elif ev.type() == QEvent.MouseButtonRelease:
                if ev.button() == self.showbutton:
                    # left button is released, stop dragging and/or resizing, hide
                    self.endShortDrag()
                elif ev.button() == self.resizebutton:
                    # right button is released, stop resizing, warp cursor to center
                    self._resizepos = None
                    QCursor.setPos(viewport.mapToGlobal(self.geometry().center()))
                    ev.accept()
                return True
            elif ev.type() == QEvent.ContextMenu:
                self.endShortDrag()
        return False

    def mousePressEvent(self, ev):
        """Start dragging the magnifier."""
        if self._dragging == DRAG_SHORT:
            ev.ignore()
        elif not self._dragging and ev.button() == Qt.LeftButton:
            self.startLongDrag(ev.pos())

    def mouseMoveEvent(self, ev):
        """Move the magnifier if we were dragging it."""
        ev.ignore()
        if self._dragging == DRAG_LONG:
            ev.accept()
            pos = self.mapToParent(ev.pos())
            self.move(pos - self._dragpos)
            view = self.parent().parent()
            view.scrollForDragging(pos)

    def mouseReleaseEvent(self, ev):
        """The button is released, stop moving ourselves."""
        ev.ignore()
        if self._dragging == DRAG_LONG and ev.button() == Qt.LeftButton:
            self.endLongDrag()

    def wheelEvent(self, ev):
        """Implement zooming the magnifying glass."""
        if ev.modifiers() & self.zoommodifier:
            ev.accept()
            if ev.modifiers() & self.resizemodifier:
                factor = 1.1 ** (ev.angleDelta().y() / 120)
                g = self.geometry()
                c = g.center()
                g.setWidth(int(min(max(g.width() * factor, self.MIN_SIZE), self.MAX_SIZE)))
                g.setHeight(int(min(max(g.height() * factor, self.MIN_SIZE), self.MAX_SIZE)))
                g.moveCenter(c)
                self.setGeometry(g)
            else:
                factor = 1.1 ** (ev.angleDelta().y() / 120)
                scale = self._scale * factor
                view = self.parent().parent()
                layout = view.pageLayout()
                scale = max(min(scale, view.MAX_ZOOM * self.MAX_EXTRA_ZOOM / layout.zoomFactor),
                            view.MIN_ZOOM / layout.zoomFactor)
                self.setScale(scale)
        else:
            super().wheelEvent(ev)

    def paintEvent(self, ev):
        """Called when paint is needed, finds out which page to magnify."""
        view = self.parent().parent()
        layout = view.pageLayout()

        scale = max(min(self._scale, view.MAX_ZOOM * self.MAX_EXTRA_ZOOM / layout.zoomFactor),
                    view.MIN_ZOOM / layout.zoomFactor)
        matrix = QTransform().scale(scale, scale)

        # the position of our center on the layout
        c = self.geometry().center() - view.layoutPosition()

        # make a region scaling back to the view scale
        rect = matrix.inverted()[0].mapRect(self.rect())
        rect.moveCenter(c)
        region = QRegion(rect, QRegion.Ellipse) # touches the Pages we need to draw

        # our rect on the enlarged pages
        our_rect = self.rect()
        our_rect.moveCenter(matrix.map(c))

        # the virtual position of the whole scaled-up layout
        ev_rect = ev.rect().translated(our_rect.topLeft())

        # draw shadow border?
        shadow = False
        if hasattr(view, "drawDropShadow") and view.dropShadowEnabled:
            shadow = True
            shadow_width = layout.spacing * scale // 2

        painter = QPainter(self)
        for p in layout.pagesAt(region.boundingRect()):
            # get a (reused) the copy of the page
            page = p.copy(self, matrix)
            # now paint it
            rect = (page.geometry() & ev_rect).translated(-page.pos())
            painter.save()
            painter.translate(page.pos() - our_rect.topLeft())
            if shadow:
                view.drawDropShadow(page, painter, shadow_width)
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


