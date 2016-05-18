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

import math
import contextlib

from PyQt5.QtCore import pyqtSignal, QBasicTimer, QPoint, QSize, Qt
from PyQt5.QtGui import QPainter, QPalette
from PyQt5.QtWidgets import QAbstractScrollArea, QStyle

from . import layout

from .constants import (

    # rotation:
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,

    # viewModes:
    FixedScale,
    FitWidth,
    FitHeight,
    FitBoth,
)



class View(QAbstractScrollArea):
    
    MIN_ZOOM = 0.05
    MAX_ZOOM = 8.0
    
    viewModeChanged = pyqtSignal(int)
    rotationChanged = pyqtSignal(int)
    zoomFactorChanged = pyqtSignal(float)

    scrollupdatespersec = 50
    
    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._viewMode = FixedScale
        self._pageLayout = layout.PageLayout()
        self._magnifier = None
        self._rubberband = None
        self.viewport().setBackgroundRole(QPalette.Dark)
        self.verticalScrollBar().setSingleStep(20)
        self.horizontalScrollBar().setSingleStep(20)
        self.setMouseTracking(True)
        
        self._scroller = None
        self._scrollTimer = QBasicTimer()
    
    def loadPdf(self, filename):
        """Convenience method to load the specified PDF file."""
        import popplerqt5
        from . import poppler
        doc = popplerqt5.Poppler.Document.load(filename)
        renderer = poppler.Renderer()
        self.pageLayout()[:] = poppler.PopplerPage.createPages(doc, renderer)
        self.updatePageLayout()
    
    def loadSvgs(self, filenames):
        """Convenience method to load the specified list of SVG files.
        
        Each SVG file is loaded in one Page.
        
        """
        from . import svg
        renderer = svg.Renderer()
        self.pageLayout()[:] = (svg.SvgPage(f, renderer) for f in filenames)
        self.updatePageLayout()
    
    def setPageLayout(self, layout):
        """Set our current PageLayout instance."""
        self._pageLayout = layout
    
    def pageLayout(self):
        """Return our current PageLayout instance."""
        return self._pageLayout
    
    def updatePageLayout(self):
        """Update layout and adjust scrollbars."""
        self._pageLayout.update()
        self._updateScrollBars()
        self.viewport().update()
    
    def clear(self):
        """Convenience method to clear the current layout."""
        self._pageLayout.clear()
        self.updatePageLayout()
    
    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            self._fitLayout()
        self.viewModeChanged.emit(mode)
    
    def viewMode(self):
        """Returns the current ViewMode."""
        return self._viewMode
        
    def setRotation(self, rotation):
        """Set the current rotation."""
        layout = self._pageLayout
        if rotation != layout.rotation:
            with self._keepCentered():
                layout.rotation = rotation
                if self._viewMode:
                    self._fitLayout()
            self.rotationChanged.emit(rotation)
    
    def rotation(self):
        """Return the current rotation."""
        return self._pageLayout.rotation
    
    def rotateLeft(self):
        """Rotate the pages 270 degrees."""
        self.setRotation((self.rotation() - 1) & 3)
    
    def rotateRight(self):
        """Rotate the pages 90 degrees."""
        self.setRotation((self.rotation() + 1) & 3)
    
    def setMagnifier(self, magnifier):
        """Sets the Magnifier to use (or None to disable the magnifier).
        
        The viewport takes ownership of the Magnifier.
        
        """
        if self._magnifier:
            self.removeEventFilter(self._magnifier)
            self._magnifier.setParent(None)
        self._magnifier = magnifier
        if magnifier:
            magnifier.setParent(self.viewport())
            self.installEventFilter(magnifier)
    
    def magnifier(self):
        """Returns the currently set magnifier."""
        return self._magnifier
    
    def setRubberband(self, rubberband):
        """Sets the Rubberband to use for selections (or None to not use one)."""
        if self._rubberband:
            self.removeEventFilter(self._rubberband)
            self.zoomFactorChanged.disconnect(self._rubberband.hide)
            self._rubberband.setParent(None)
        self._rubberband = rubberband
        if rubberband:
            rubberband.setParent(self.viewport())
            self.installEventFilter(rubberband)
            self.zoomFactorChanged.connect(rubberband.hide)
    
    def scrollContentsBy(self, dx, dy):
        """Reimplemented to move the rubberband as well."""
        if self._rubberband:
            self._rubberband.scrollBy(QPoint(dx, dy))
        self.viewport().update()
    
    def _fitLayout(self):
        """(Internal). Fits the layout according to the view mode.
        
        Prevents scrollbar/resize loops by precalculating which scrollbars will appear.
        
        """
        mode = self.viewMode()
        if mode == FixedScale:
            return
        
        maxsize = self.maximumViewportSize()
        
        # can vertical or horizontal scrollbars appear?
        vcan = self.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        hcan = self.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        
        # width a scrollbar takes off the viewport size
        framewidth = 0
        if self.style().styleHint(QStyle.SH_ScrollView_FrameOnlyAroundContents, None, self):
            framewidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth) * 2
        scrollbarextent = self.style().pixelMetric(QStyle.PM_ScrollBarExtent, None, self) + framewidth
        
        # remember old factor
        zoom_factor = self.zoomFactor()
        
        # first try to fit full size
        layout = self._pageLayout
        layout.fit(maxsize, mode)
        layout.update()
        
        # minimal values
        minwidth = maxsize.width()
        minheight = maxsize.height()
        if vcan:
            minwidth -= scrollbarextent
        if hcan:
            minheight -= scrollbarextent
        
        # do width and/or height fit?
        fitw = layout.width <= maxsize.width()
        fith = layout.height <= maxsize.height()
        
        if not fitw and not fith:
            if vcan or hcan:
                layout.fit(QSize(minwidth, minheight), mode)
        elif mode & FitWidth and fitw and not fith and vcan:
            # a vertical scrollbar will appear
            w = minwidth
            layout.fit(QSize(w, maxsize.height()), mode)
            layout.update()
            if layout.height <= maxsize.height():
                # now the vert. scrollbar would disappear!
                # enlarge it as long as the vertical scrollbar would not be needed
                while True:
                    w += 1
                    layout.fit(QSize(w, maxsize.height()), mode)
                    layout.update()
                    if layout.height > maxsize.height():
                        layout.fit(QSize(w - 1, maxsize.height()), mode)
                        break
        elif mode & FitHeight and fith and not fitw and hcan:
            # a horizontal scrollbar will appear
            h = minheight
            layout.fit(QSize(maxsize.width(), h), mode)
            layout.update()
            if layout.width <= maxsize.width():
                # now the horizontal scrollbar would disappear!
                # enlarge it as long as the horizontal scrollbar would not be needed
                while True:
                    h += 1
                    layout.fit(QSize(maxsize.width(), h), mode)
                    layout.update()
                    if layout.width > maxsize.width():
                        layout.fit(QSize(maxsize.width(), h - 1), mode)
                        break
        self.updatePageLayout()
        if zoom_factor != self.zoomFactor():
            self.zoomFactorChanged.emit(self.zoomFactor())
    
    @contextlib.contextmanager
    def _keepCentered(self, pos=None, on_page=False):
        """Context manager to keep the same spot centered while changing the layout.
        
        If pos is not given, the viewport's center is used. If on_page is True, 
        a position on a page is maintained if found. Otherwise, just the 
        position on the layout is kept.
        
        """
        if pos is None:
            pos = self.viewport().rect().center()
        
        # find the spot on the page
        layout = self._pageLayout
        layout_pos = self.layoutPosition()
        pos_on_layout = pos - layout_pos
        page = layout.pageAt(pos_on_layout) if on_page else None
        if page:
            pos_on_page = pos_on_layout - page.pos()
            x = pos_on_page.x() / page.width
            y = pos_on_page.y() / page.height
        else:
            x = pos_on_layout.x() / layout.width
            y = pos_on_layout.y() / layout.height
        
        yield
        self.updatePageLayout()
        
        if page:
            new_pos_on_page = QPoint(round(x * page.width), round(y * page.height))
            new_pos_on_layout = page.pos() + new_pos_on_page
        else:
            new_pos_on_layout = QPoint(round(x * layout.width), round(y * layout.height))
        diff = new_pos_on_layout - pos
        self.verticalScrollBar().setValue(diff.y())
        self.horizontalScrollBar().setValue(diff.x())

    def setZoomFactor(self, factor, pos=None):
        """Set the zoom factor (1.0 by default).
        
        If pos is given, that position (in viewport coordinates) is kept in the
        center if possible. If None, zooming centers around the viewport center.
        
        """
        factor = max(self.MIN_ZOOM, min(self.MAX_ZOOM, factor))
        if factor != self._pageLayout.zoomFactor:
            with self._keepCentered(pos, True):
                self._pageLayout.zoomFactor = factor
            self.setViewMode(FixedScale)
            self.zoomFactorChanged.emit(factor)
    
    def zoomFactor(self):
        """Return the page layout's zoom factor."""
        return self._pageLayout.zoomFactor
    
    def zoomIn(self, pos=None, factor=1.1):
        """Zoom in.
        
        If pos is given, it is the position in the viewport to keep centered.
        Otherwise zooming centers around the viewport center.

        """
        self.setZoomFactor(self.zoomFactor() * factor, pos)
        
    def zoomOut(self, pos=None, factor=1.1):
        """Zoom out.
        
        If pos is given, it is the position in the viewport to keep centered.
        Otherwise zooming centers around the viewport center.

        """
        self.setZoomFactor(self.zoomFactor() / factor, pos)
        
    def _updateScrollBars(self):
        """Adjust the range of the scrollbars to the layout."""
        layout = self._pageLayout
        maxsize = self.maximumViewportSize()
        vbar = self.verticalScrollBar()
        hbar = self.horizontalScrollBar()
        
        if layout.width <= maxsize.width() and layout.height <= maxsize.height():
            vbar.setRange(0, 0)
            hbar.setRange(0, 0)
        else:
            viewport = self.viewport()
            vbar.setRange(0, layout.height - viewport.height())
            vbar.setPageStep(viewport.height() * .9)
            hbar.setRange(0, layout.width - viewport.width())
            hbar.setPageStep(viewport.width() * .9)
    
    def layoutPosition(self):
        """Return the position of the PageLayout relative to the viewport.
        
        This is the top-left position of the layout, relative to the
        top-left position of the viewport.
        
        If the layout is smaller than the viewport it is centered.
        
        """
        lw = self._pageLayout.width
        vw = self.viewport().width()
        left = -self.horizontalScrollBar().value() if lw > vw else (vw - lw) // 2
        lh = self._pageLayout.height
        vh = self.viewport().height()
        top = -self.verticalScrollBar().value() if lh > vh else (vh - lh) // 2
        return QPoint(left, top)

    def visibleRect(self):
        """Return the QRect of the page layout that is currently visible in the viewport."""
        return self.viewport().rect().translated(-self.layoutPosition())
    
    def visiblePages(self):
        """Yield the Page instances that are currently visible."""
        return self._pageLayout.pagesAt(self.visibleRect())
    
    def resizeEvent(self, ev):
        """Reimplemented to update the scrollbars."""
        if self._viewMode and not self._pageLayout.empty():
            self._fitLayout()
            # TODO: implement sensible repositioning
        else:
            self._updateScrollBars()
    
    def repaintPage(self, page):
        """Call this when you want to redraw the specified page."""
        rect = page.rect().translated(self.layoutPosition())
        self.viewport().update(rect)
    
    def paintEvent(self, ev):
        layout_pos = self.layoutPosition()
        painter = QPainter(self.viewport())
        # paint the pages
        ev_rect = ev.rect().translated(-layout_pos)
        for p in self._pageLayout.pagesAt(ev_rect):
            rect = (p.rect() & ev_rect).translated(-p.pos())
            painter.save()
            painter.translate(p.pos() + layout_pos)
            p.paint(painter, rect, self.repaintPage)
            painter.restore()
        # TODO paint highlighting

    def wheelEvent(self, ev):
        # TEMP
        if ev.modifiers() & Qt.CTRL:
            factor = 1.1 ** (ev.angleDelta().y() / 120)
            if ev.angleDelta().y():
                self.setZoomFactor(self.zoomFactor() * factor, ev.pos())
        else:
            super().wheelEvent(ev)
    
    def canScrollBy(self, diff):
        """Does not scroll, but return the actual distance the View would scroll.
        
        diff is a QPoint instance.
        
        """
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        
        x = min(max(0, hbar.value() + diff.x()), hbar.maximum())
        y = min(max(0, vbar.value() + diff.y()), vbar.maximum())
        return QPoint(x - hbar.value(), y - vbar.value())
    
    def scrollForDragging(self, pos):
        """Slowly scroll the View if pos is close to the edge of the View.
        
        Can be used while dragging things.
        
        """
        viewport = self.viewport().rect()
        dx = pos.x() - viewport.left() - 12
        if dx >= 0:
            dx = max(0, pos.x() - viewport.right() + 12)
        dy = pos.y() - viewport.top() - 12
        if dy >= 0:
            dy = max(0, pos.y() - viewport.bottom() + 12)
        self.steadyScroll(QPoint(dx*10, dy*10))
    
    def scrollTo(self, pos):
        """Scroll the View to get pos (QPoint) in the top left corner (if possible).
        
        Returns the actual distance moved.
        
        """
        return self.scrollBy(pos + self.layoutPosition())
    
    def scrollBy(self, diff):
        """Scroll the View diff pixels (QPoint) in x and y direction.
        
        Returns the actual distance moved.
        
        """
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        x = hbar.value()
        hbar.setValue(hbar.value() + diff.x())
        x = hbar.value() - x
        y = vbar.value()
        vbar.setValue(vbar.value() + diff.y())
        y = vbar.value() - y
        return QPoint(x, y)
    
    def kineticScrollBy(self, diff):
        """Scroll the View diff pixels (QPoint) in x and y direction.
        
        Returns the actual distance the View will move.
        
        """
        ret = self.canScrollBy(diff)
        if diff:
            scroller = KineticScroller()
            scroller.scrollBy(diff)
            self.startScrolling(scroller)
        return ret
    
    def steadyScroll(self, diff):
        """Start steadily scrolling diff (QPoint) pixels per second.
        
        Stops automatically when the end is reached.
        
        """
        if diff:
            self.startScrolling(SteadyScroller(diff, self.scrollupdatespersec))
        else:
            self.stopScrolling()
    
    def startScrolling(self, scroller):
        """Begin a scrolling operation using the specified scroller."""
        self._scroller = scroller
        if not self._scrollTimer.isActive():
            self._scrollTimer.start(1000 / self.scrollupdatespersec, self)
    
    def stopScrolling(self):
        """Stop scrolling."""
        if self._scroller:
            self._scrollTimer.stop()
            self._scroller = None
    
    def timerEvent(self, ev):
        """Called by the _scrollTimer."""
        diff = self._scroller.step()
        # when scrolling slowly, it might be that no redraw is needed
        if diff:
            # change the scrollbars, but check how far they really moved.
            if not self.scrollBy(diff) or self._scroller.finished():
                self.stopScrolling()


class SteadyScroller:
    """Scrolls the View steadily n pixels per second."""
    def __init__(self, speed, updates_per_second):
        """Initializes with speed (QPoint) pixels per second."""
        self._x = speed.x()
        self._y = speed.y()
        self._restx = 0
        self._resty = 0
        self._ups = updates_per_second
    
    def step(self):
        """Return a QPoint indicating the diff to scroll in this step.
        
        If this is a QPoint(0, 0) it does not indicate that scrolling has
        finished. Use finished() for that.
        
        """
        # the amount of pixels to scroll per second
        x = self._x
        y = self._y
        
        # how many updates per second, compute the number of pixes to scroll now
        ups = self._ups
        dx, rx = divmod(abs(x), ups)
        dy, ry = divmod(abs(y), ups)
        dx1, self._restx = divmod(self._restx + rx, ups)
        dy1, self._resty = divmod(self._resty + ry, ups)
        dx += dx1
        dy += dy1
        
        # scroll in the right direction
        diff = QPoint(-dx if x < 0 else dx, -dy if y < 0 else dy)
        return diff

    def finished(self):
        """As this scroller has a constant speed, it never stops."""
        return False


class KineticScroller:
    """Scrolls the View with a decreasing speed."""
    def __init__(self):
        self._x = 0
        self._y = 0
        self._offset = None
    
    def scrollBy(self, diff):
        """Start a new kinetic scroll of the specified amount."""
        ### logic by Richard Cognot, May 2012, simplified by WB
        dx = diff.x()
        dy = diff.y()
        
        # solve speed*(speed+1)/2 = delta to ensure 1+2+3+...+speed is as close as possible under delta..
        sx = (math.sqrt(1 + 8 * abs(dx)) - 1) // 2
        sy = (math.sqrt(1 + 8 * abs(dy)) - 1) // 2
        
        # compute the amount of displacement still needed because we're dealing with integer values.
        # Since this function is called for exact moves (not free scrolling)
        # limit the kinetic time to 2 seconds, which means 100 ticks, 5050 pixels.
        # (TODO: adapt for other ticker speeds? WB)
        if sy > 100:
            sy = 100
        offy = abs(dy) - sy * (sy + 1) // 2
            
        # Although it is less likely to go beyond that limit for horizontal scrolling,
        # do it for x as well.
        if sx > 100:
            sx = 100
        offx = abs(dx) - sx * (sx + 1) // 2
        
        # adjust directions
        if dx < 0:
            sx = -sx
            offx = -offx
        if dy < 0:
            sy = -sy
            offy = -offy
        self._x = sx
        self._y = sy
        # the offset is accounted for in the first step
        self._offset = QPoint(offx, offy)
        
    def addDelta(self, diff):
        """Adds a displacement (QPoint). If no scroll is active, start a new one."""
        # TODO: implement
        
    def step(self):
        """Return a QPoint indicating the diff to scroll in this step."""
        ret = QPoint(self._x, self._y)
        if self._offset:
            ret += self._offset
            self._offset = None
        if self._x > 0:
            self._x -= 1
        elif self._x < 0:
            self._x += 1
        if self._y > 0:
            self._y -= 1
        elif self._y < 0:
            self._y += 1
        return ret
    
    def finished(self):
        """Return True if scrolling is done."""
        return self._x == 0 and self._y == 0


