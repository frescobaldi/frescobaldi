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
Rubberband selection in a View.
"""


from PyQt5.QtCore import QEvent, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QPainter, QPalette, QPen, QRegion
from PyQt5.QtWidgets import QWidget


# dragging/moving selection:
_OUTSIDE = 0
_LEFT    = 1
_TOP     = 2
_RIGHT   = 4
_BOTTOM  = 8
_INSIDE  = 15


class Rubberband(QWidget):
    """A Rubberband to select a rectangular region.

    A Rubberband is added to a View with view.setRubberband().
    
    Instance variables:

        showbutton (Qt.RightButton), the button used to drag a new rectangle

        dragbutton (Qt.LeftButton), the button to alter an existing rectangle
        
        trackSelection (False), whether to continuously emit selectionChanged().
                When True, selectionChanged() is emitted on every change, when
                False, the signal is only emitted when the mouse button is
                released.

    """
    selectionChanged = pyqtSignal(QRect)

    # the button used to drag a new rectangle
    showbutton = Qt.RightButton

    # the button to alter an existing rectangle
    dragbutton = Qt.LeftButton

    # whether to continuously track the selection
    trackSelection = False

    def __init__(self):
        super().__init__()
        self._dragging = False
        self._dragedge = 0
        self._dragpos = None
        self._selection = QRect()
        self._layoutOffset = QPoint()   # used to keep on spot during resize
        self._offsetOnPage = None       # used to keep on spot during zoom
        self._pageIndex = -1            # id.
        self.setMouseTracking(True)

    def paintEvent(self, ev):
        ### Paint code contributed by Richard Cognot Jun 2012
        color = self.palette().color(QPalette.Highlight)
        painter = QPainter(self)

        # Filled rectangle.
        painter.setClipRect(self.rect())
        color.setAlpha(50)
        painter.fillRect(self.rect().adjusted(2,2,-2,-2), color)

        # Thin rectangle outside.
        color.setAlpha(150)
        painter.setPen(color)
        # XXX can this adjustment be done smarter?
        adjust = -1 / self.devicePixelRatioF()
        painter.drawRect(self.rect().adjusted(0, 0, adjust, adjust))

        # Pseudo-handles at the corners and sides
        color.setAlpha(100)
        pen = QPen(color)
        pen.setWidth(8)
        painter.setPen(pen)
        painter.setBackgroundMode(Qt.OpaqueMode)
        # Clip at 4 corners
        region = QRegion(QRect(0,0,20,20))
        region += QRect(self.rect().width()-20, 0, 20, 20)
        region += QRect(self.rect().width()-20, self.rect().height()-20, 20, 20)
        region += QRect(0, self.rect().height()-20, 20, 20)
        # Clip middles
        region += QRect(0, self.rect().height() // 2 - 10, self.rect().width(), 20)
        region += QRect(self.rect().width() // 2 - 10, 0, 20, self.rect().height())

        # Draw thicker rectangles, clipped at corners and sides.
        painter.setClipRegion(region)
        painter.drawRect(self.rect())

    def edge(self, point):
        """Return the edge where the point touches our geometry."""
        rect = self.geometry()
        if point not in rect:
            return _OUTSIDE
        edge = 0
        if point.x() <= rect.left() + 4:
            edge |= _LEFT
        elif point.x() >= rect.right() - 4:
            edge |= _RIGHT
        if point.y() <= rect.top() + 4:
            edge |= _TOP
        elif point.y() >= rect.bottom() - 4:
            edge |= _BOTTOM
        return edge or _INSIDE

    def adjustCursor(self, edge):
        """Sets the cursor shape when we are at edge."""
        cursor = None
        if edge in (_TOP, _BOTTOM):
            cursor = Qt.SizeVerCursor
        elif edge in (_LEFT, _RIGHT):
            cursor = Qt.SizeHorCursor
        elif edge in (_LEFT | _TOP, _RIGHT | _BOTTOM):
            cursor = Qt.SizeFDiagCursor
        elif edge in (_TOP | _RIGHT, _BOTTOM | _LEFT):
            cursor = Qt.SizeBDiagCursor
        elif edge is _INSIDE:
            cursor = Qt.SizeAllCursor
        if cursor and cursor != self.cursor():
            self.setCursor(cursor)
        else:
            self.unsetCursor()
    
    def hasSelection(self):
        """Return True when there is a selection."""
        return bool(self._selection)
    
    def selection(self):
        """Return our selection rectangle, relative to the view's layout position."""
        return self._selection
    
    def selectedPages(self):
        """Yield tuples (page, rect) describing the selection.
        
        Every rect is intersected with the page rect and translated to the
        page's position.
        
        """
        rect = self.selection()
        if rect:
            view = self.parent().parent()
            layout = view.pageLayout()
            for page in layout.pagesAt(rect):
                yield page, rect.intersected(page.geometry()).translated(-page.pos())
    
    def selectedText(self):
        """Return the text found in the selection, as far as the pages support it."""
        result = []
        for page, rect in self.selectedPages():
            result.append(page.text(rect))
        return '\n'.join(result)

    def selectedLinks(self):
        """Yield tuples (page, links) for every page in the selection.
        
        links is a non-empty set() of Link instances on that page that intersect
        with the selection.
        
        """
        for page, rect in self.selectedPages():
            links = page.linksIn(rect)
            if links:
                yield page, links

    def setSelection(self, rect):
        """Sets the selection, the rectangle should be relative to the view's layout position."""
        if rect:
            view = self.parent().parent()
            geom = rect.translated(view.layoutPosition())
            self.setGeometry(geom)
            self._setLayoutOffset(rect.topLeft())
            self._oldZoom = view.zoomFactor()
            self.show()
            self._emitSelectionChanged(geom)
        else:
            self.hide()
            self._emitSelectionChanged(QRect())
    
    def clearSelection(self):
        """Hide ourselves and clear the selection."""
        self.hide()
        self._emitSelectionChanged(QRect())
        
    def _emitSelectionChanged(self, rect):
        """(Internal) Called to emit the selectionChanged signal.
        
        Only emits the signal when the selection really changed.
        The rect should be our geometry or an empty QRect().
        
        """
        if rect:
            view = self.parent().parent()
            rect = rect.translated(-view.layoutPosition())
        old, self._selection = self._selection, rect
        if rect != old:
            self.selectionChanged.emit(rect)
    
    def _setLayoutOffset(self, pos):
        """Store the position as offset from the layout, and also from the page
        at that position. Used for keeping the same spot on zoom change.
        
        """
        layout = self.parent().parent().pageLayout()
        self._layoutOffset = pos
        page = layout.pageAt(pos)
        if page:
            self._pageIndex = layout.index(page)
            self._offsetOnPage = pos - page.pos()
        else:
            self._pageIndex = -1
            self._offsetOnPage = None

    def scrollBy(self, diff):
        """Called by the View when scrolling."""
        if not self._dragging:
            self.move(self.pos() + diff)
            # adjust the cursor
            self.adjustCursor(self.edge(self.parent().mapFromGlobal(QCursor.pos())))
        elif self._dragedge != _INSIDE:
            self._draggeom.moveTo(self._draggeom.topLeft() + diff)
            self.dragBy(-diff)
        elif self.isVisible() and self.trackSelection:
            self._emitSelectionChanged(self.geometry())

    def startDrag(self, pos, button):
        """Start dragging the rubberband."""
        self._dragging = True
        self._dragpos = pos
        self._dragedge = self.edge(pos)
        self._draggeom = self.geometry()
        self._dragbutton = button

    def drag(self, pos):
        """Continue dragging the rubberband, scrolling the View if necessary."""
        diff = pos - self._dragpos
        self._dragpos = pos
        self.dragBy(diff)
        # check if we are dragging close to the edge of the view, scroll if needed
        view = self.parent().parent()
        view.scrollForDragging(pos)

    def dragBy(self, diff):
        """Drag by diff (QPoint)."""
        edge = self._dragedge
        self._draggeom.adjust(
            diff.x() if edge & _LEFT   else 0,
            diff.y() if edge & _TOP    else 0,
            diff.x() if edge & _RIGHT  else 0,
            diff.y() if edge & _BOTTOM else 0)
        geom = self._draggeom.normalized()
        if geom.isValid():
            self.setGeometry(geom)
            self._setLayoutOffset(geom.topLeft() - self.parent().parent().layoutPosition())
            if self.trackSelection:
                self._emitSelectionChanged(geom)
        if self.cursor().shape() in (Qt.SizeBDiagCursor, Qt.SizeFDiagCursor):
            # we're dragging a corner, use correct diagonal cursor
            bdiag = (edge in (3, 12)) ^ (self._draggeom.width() * self._draggeom.height() >= 0)
            self.setCursor(Qt.SizeBDiagCursor if bdiag else Qt.SizeFDiagCursor)

    def stopDrag(self):
        """Stop dragging the rubberband."""
        self._dragging = False
        # TODO: use the kinetic scroller if implemented
        view = self.parent().parent()
        view.stopScrolling()

        if self.width() < 8 and self.height() < 8:
            self.unsetCursor()
            self._emitSelectionChanged(QRect())
        else:
            self._emitSelectionChanged(self.geometry())

    def slotZoomChanged(self, zoom):
        """Called when the zooming in the view changes, resizes ourselves."""
        if self.hasSelection():
            view = self.parent().parent()
            factor =  zoom / self._oldZoom
            self._oldZoom = zoom
            # compute offset
            if self._pageIndex >=0 and self._pageIndex < view.pageLayout().count():
                offset = view.pageLayout()[self._pageIndex].pos() + self._offsetOnPage * factor
            else:
                offset = self._layoutOffset * factor
            size = self.size() * factor
            geom = QRect(view.layoutPosition() + offset, size)
            self.setGeometry(geom)
            self._setLayoutOffset(offset)
            self._emitSelectionChanged(geom)
    
    def eventFilter(self, viewport, ev):
        if ev.type() == QEvent.Resize and self.isVisible():
            view = self.parent().parent()
            if not view.viewMode():
                # fixed scale, try to keep ourselves in the same position on resize
                self.move(self._layoutOffset + view.layoutPosition())
        elif not self._dragging:
            if ev.type() == QEvent.MouseButtonPress and ev.button() == self.showbutton:
                if self.isVisible():
                    # this cancels a previous selection if we were visible
                    self._emitSelectionChanged(QRect())
                self.setGeometry(QRect(ev.pos(), QSize(0, 0)))
                self._setLayoutOffset(ev.pos() - viewport.parent().layoutPosition())
                self._oldZoom = viewport.parent().zoomFactor()
                self.startDrag(ev.pos(), ev.button())
                self._dragedge = _RIGHT | _BOTTOM
                self.adjustCursor(self._dragedge)
                self.show()
                return True
        elif self._dragging:
            if ev.type() == QEvent.MouseMove:
                self.drag(ev.pos())
                return True
            elif ev.type() == QEvent.MouseButtonRelease and ev.button() == self._dragbutton:
                self.stopDrag()
                # don't consume event when the right button was used
                return self._dragbutton != Qt.RightButton
        return False

    def mousePressEvent(self, ev):
        pos = self.mapToParent(ev.pos())
        if not self._dragging:
            if ev.button() == self.dragbutton:
                self.startDrag(pos, ev.button())
            elif ev.button() == self.showbutton:
                if self.showbutton != Qt.RightButton or self.edge(pos) != _INSIDE:
                    self.startDrag(pos, ev.button())

    def mouseMoveEvent(self, ev):
        pos = self.mapToParent(ev.pos())
        if self._dragging:
            self.drag(pos)
        else:
            edge = self.edge(pos)
            self.adjustCursor(edge)

    def mouseReleaseEvent(self, ev):
        if self._dragging and ev.button() == self._dragbutton:
            self.stopDrag()


