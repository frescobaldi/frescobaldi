# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
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

import collections
import contextlib
import weakref

from PyQt5.QtCore import pyqtSignal, QEvent, QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QCursor, QPainter, QPalette, QRegion
from PyQt5.QtWidgets import QStyle

from . import layout
from . import page
from . import scrollarea
from . import util

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



class View(scrollarea.ScrollArea):
    """View is a generic scrollable widget to display Pages in a layout.
    
    Using setPageLayout() you can set a PageLayout to the View, and you can
    add Pages to the layout using a list-like api. (PageLayout derives from
    list). A simple PageLayout is set by default. Call updatePageLayout() after
    every change to the layout (like adding or removing pages).
    
    You can also add a Magnifier to magnify parts of a Page, and a Rubberband
    to enable selecting a rectangular region.
    
    View emits the following signals:
    
    `viewModeChanged`   When the user changes the view mode (one of FixedScale,
                        FitWidth, FitHeight and FitBoth)

    `rotationChanged`   When the user changes the rotation (one of Rotate_0,
                        Rotate_90, Rotate_180, Rotate_270)

    `zoomFactorChanged` When the zoomfactor changes
    
    `pageLayoutUpdated` When the page layout is updated (e.g. after adding
                        or removing pages, but also zoom and rotation cause a
                        layout update)

    `continuousModeChanged` When the user toggle the continuousMode() setting.
    
    
    The following instance variables can be set, and default to:
    
    wheelZoomingEnabled = True      # if True, the user can zoom the View using the mouse wheel
    MIN_ZOOM = 0.05
    MAX_ZOOM = 64.0

    """

    MIN_ZOOM = 0.05
    MAX_ZOOM = 64.0

    wheelZoomingEnabled = True

    viewModeChanged = pyqtSignal(int)
    rotationChanged = pyqtSignal(int)
    orientationChanged = pyqtSignal(int)
    zoomFactorChanged = pyqtSignal(float)
    pageLayoutUpdated = pyqtSignal()
    continuousModeChanged = pyqtSignal(bool)

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._prev_pages_to_paint = set()
        self._viewMode = FixedScale
        self._pageLayout = None
        self._magnifier = None
        self._rubberband = None
        self.viewport().setBackgroundRole(QPalette.Dark)
        self.verticalScrollBar().setSingleStep(20)
        self.horizontalScrollBar().setSingleStep(20)
        self.setMouseTracking(True)
        self.setMinimumSize(QSize(60, 60))
        self.setPageLayout(layout.PageLayout())

    def loadPdf(self, filename):
        """Convenience method to load the specified PDF file."""
        import popplerqt5
        from . import poppler
        doc = popplerqt5.Poppler.Document.load(filename)
        self._unschedulePages(self._pageLayout)
        self.pageLayout()[:] = poppler.PopplerPage.createPages(doc)
        self.updatePageLayout()

    def loadSvgs(self, filenames):
        """Convenience method to load the specified list of SVG files.

        Each SVG file is loaded in one Page.

        """
        self._unschedulePages(self._pageLayout)
        from . import svg
        self.pageLayout()[:] = (svg.SvgPage(f) for f in filenames)
        self.updatePageLayout()

    def setPageLayout(self, layout):
        """Set our current PageLayout instance.
        
        The dpiX and dpiY attributes of the layout are set to the physical
        resolution of the widget, which should result in a natural size of 100%
        at zoom factor 1.0
        
        """
        if self._pageLayout:
            self._unschedulePages(self._pageLayout)
        layout.dpiX = self.physicalDpiX()
        layout.dpiY = self.physicalDpiY()
        self._pageLayout = layout
        self.updatePageLayout()

    def pageLayout(self):
        """Return our current PageLayout instance."""
        return self._pageLayout

    def updatePageLayout(self):
        """Update layout and adjust scrollbars."""
        self._pageLayout.update()
        self._updateScrollBars()
        self.pageLayoutUpdated.emit()
        self.viewport().update()

    def clear(self):
        """Convenience method to clear the current layout."""
        self._unschedulePages(self._pageLayout)
        self._pageLayout.clear()
        self.updatePageLayout()

    def currentPage(self):
        """Return the page that is in the center of the View.
        
        Might return None, if there are no pages.
        
        """
        pos = self.viewport().rect().center() - self.layoutPosition()
        return self._pageLayout.pageAt(pos) or self._pageLayout.nearestPageAt(pos)

    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            with self._keepCentered():
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

    def setOrientation(self, orientation):
        """Set the orientation (Horizontal or Vertical)."""
        layout = self._pageLayout
        if orientation != layout.orientation:
            with self._keepCentered():
                layout.orientation = orientation
                if self._viewMode:
                    self._fitLayout()
            self.orientationChanged.emit(orientation)

    def orientation(self):
        """Return the current orientation (Horizontal or Vertical)."""
        return self._pageLayout.orientation

    def setContinuousMode(self, continuous):
        """Sets whether the layout should display all pages.
        
        If True, the layout shows all pages. If False, only the page set
        containing the current page is displayed. If the pageLayout() does not
        support the PageSetLayoutMixin methods, this method does nothing.
        
        """
        layout = self._pageLayout
        oldcontinuous = layout.continuousMode
        if continuous:
            if not oldcontinuous:
                with self._keepCentered():
                    layout.continuousMode = True
                    if self._viewMode:
                        self._fitLayout()
                self.continuousModeChanged.emit(True)
        elif oldcontinuous:
            p = self.currentPage()
            index = layout.index(p) if p else 0
            with self._keepCentered():
                layout.continuousMode = False
                layout.currentPageSet = layout.pageSet(index)
                if self._viewMode:
                    self._fitLayout()
            self.continuousModeChanged.emit(False)
    
    def continuousMode(self):
        """Return True if the layout displays all pages."""
        return self._pageLayout.continuousMode

    def displayPageSet(self, what):
        """Try to display a page set (if the layout is not in continuous mode).
        
        `what` can be:
        
            "next":     go to the next page set
            "previous": go to the previous page set
            "first":    go to the first page set
            "last":     go to the last page set
            integer:    go to the specified page set

        """
        layout = self._pageLayout
        if layout.continuousMode:
            return

        sb = 0  # where to move the scrollbar after fitlayout
        if what == "first":
            what = 0
            sb = -1     # move to the start
        elif what == "last":
            what = layout.pageSetCount() - 1
            sb = 1      # move to the end
        elif what == "previous":
            what = layout.currentPageSet - 1
            if what < 0:
                return
            sb = 1
        elif what == "next":
            what = layout.currentPageSet + 1
            if what >= layout.pageSetCount():
                return
            sb = -1
        elif not 0 <= what < layout.pageSetCount():
            return
        layout.currentPageSet = what
        if self._viewMode:
            self._fitLayout()
        self.updatePageLayout()
        if sb:
            self.verticalScrollBar().setValue(0 if sb == -1 else self.verticalScrollBar().maximum())

    def setMagnifier(self, magnifier):
        """Sets the Magnifier to use (or None to disable the magnifier).

        The viewport takes ownership of the Magnifier.

        """
        if self._magnifier:
            self.viewport().removeEventFilter(self._magnifier)
            self.removeEventFilter(self._magnifier)
            self._magnifier.setParent(None)
        self._magnifier = magnifier
        if magnifier:
            magnifier.setParent(self.viewport())
            self.viewport().installEventFilter(magnifier)
            self.installEventFilter(magnifier)

    def magnifier(self):
        """Returns the currently set magnifier."""
        return self._magnifier

    def setRubberband(self, rubberband):
        """Sets the Rubberband to use for selections (or None to not use one)."""
        if self._rubberband:
            self.viewport().removeEventFilter(self._rubberband)
            self.zoomFactorChanged.disconnect(self._rubberband.slotZoomChanged)
            self.rotationChanged.disconnect(self._rubberband.clearSelection)
            self._rubberband.setParent(None)
        self._rubberband = rubberband
        if rubberband:
            rubberband.setParent(self.viewport())
            self.viewport().installEventFilter(rubberband)
            self.zoomFactorChanged.connect(rubberband.slotZoomChanged)
            self.rotationChanged.connect(rubberband.clearSelection)

    def rubberband(self):
        """Return the currently set rubberband."""
        return self._rubberband

    def scrollContentsBy(self, dx, dy):
        """Reimplemented to move the rubberband and adjust the mouse cursor."""
        if self._rubberband:
            self._rubberband.scrollBy(QPoint(dx, dy))
        if not self.isScrolling():
            # don't adjust the cursor during a kinetic scroll
            pos = self.mapFromGlobal(QCursor.pos())
            if pos in self.viewport().rect() and not self.viewport().childAt(pos):
                self.adjustCursor(pos)
        self.viewport().update()
    
    def stopScrolling(self):
        """Reimplemented to adjust the mouse cursor on scroll stop."""
        super().stopScrolling()
        pos = self.mapFromGlobal(QCursor.pos())
        if pos in self.viewport().rect() and not self.viewport().childAt(pos):
            self.adjustCursor(pos)
            
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
        if zoom_factor != self.zoomFactor():
            self.zoomFactorChanged.emit(self.zoomFactor())
            self._unschedulePages(layout)

    @contextlib.contextmanager
    def _keepCentered(self, pos=None):
        """Context manager to keep the same spot centered while changing the layout.

        If pos is not given, the viewport's center is used.
        After yielding, updatePageLayout() is called.

        """
        if pos is None:
            pos = self.viewport().rect().center()

        # find the spot on the page
        layout = self._pageLayout
        layout_pos = self.layoutPosition()
        pos_on_layout = pos - layout_pos
        offset = layout.pos2offset(pos_on_layout)
        pos_on_layout -= layout.pos()   # pos() of the layout might change

        yield
        self.updatePageLayout()

        new_pos_on_layout = layout.offset2pos(offset) - layout.pos()
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
            with self._keepCentered(pos):
                self._pageLayout.zoomFactor = factor
            self.setViewMode(FixedScale)
            self.zoomFactorChanged.emit(factor)
            self._unschedulePages(self._pageLayout)

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
        return QPoint(left, top) - self._pageLayout.pos()

    def visibleRect(self):
        """Return the QRect of the page layout that is currently visible in the viewport."""
        return self.viewport().rect().translated(-self.layoutPosition())

    def visiblePages(self):
        """Yield the Page instances that are currently visible."""
        return self._pageLayout.pagesAt(self.visibleRect())

    def offsetToEnsureVisible(self, rect):
        """Return an offset QPoint with the minimal scroll to make rect visible.

        If the rect is too large, it is positioned top-left.

        """
        vrect = self.visibleRect()
        # vertical
        dy = 0
        if rect.bottom() > vrect.bottom():
            dy = rect.bottom() - vrect.bottom()
        if rect.top() < vrect.top() + dy:
            dy = rect.top() - vrect.top()
        # horizontal
        dx = 0
        if rect.right() > vrect.right():
            dx = rect.right() - vrect.right()
        if rect.left() < vrect.left() + dx:
            dx = rect.left() - vrect.left()
        return QPoint(dx, dy)

    def ensureVisible(self, rect, margins=None, allowKinetic=True):
        """Performs the minimal scroll to make rect visible.
        
        Switches page set if needed. If allowKinetic is False, immediately
        jumps to the position, otherwise scrolls smoothly (if kinetic scrolling
        is enabeled).
        
        For finding the page set, rect is used. When scrolling, margins is
        added if given, and should be a QMargins instance.
        
        """
        if not any(self.pageLayout().pagesAt(rect)):
            if self.continuousMode():
                return
            # we might need to switch page set
            # find the rect
            for p in layout.PageRects(self.pageLayout()).intersecting(*rect.getCoords()):
                num = self.pageLayout().index(p)
                self.displayPageSet(self.pageLayout().pageSet(num))
                break
            else:
                return
        if margins is not None:
            rect = rect + margins
        diff = self.offsetToEnsureVisible(rect)
        if diff:
            if allowKinetic and self.kineticScrollingEnabled:
                self.kineticScrollBy(diff)
            else:
                self.scrollBy(diff)

    def adjustCursor(self, pos):
        """Sets the correct mouse cursor for the position on the page."""
        pass

    def resizeEvent(self, ev):
        """Reimplemented to update the scrollbars."""
        if self._viewMode and not self._pageLayout.empty():
            # sensible repositioning
            vbar = self.verticalScrollBar()
            hbar = self.horizontalScrollBar()
            x, xm = hbar.value(), hbar.maximum()
            y, ym = vbar.value(), vbar.maximum()
            self._fitLayout()
            self.updatePageLayout()
            if xm: hbar.setValue(round(x * hbar.maximum() / xm))
            if ym: vbar.setValue(round(y * vbar.maximum() / ym))
        else:
            self._updateScrollBars()

    def repaintPage(self, page):
        """Call this when you want to redraw the specified page."""
        rect = page.geometry().translated(self.layoutPosition())
        self.viewport().update(rect)

    def lazyUpdate(self, page=None):
        """Repaint page or all visible pages, rendering the pages if needed.
        
        Only updates the viewport as soon as all rendering tasks for the page
        have finished. This reduces flicker.
        
        """
        pages = list(self.visiblePages())
        if page and page in pages:
            pages = [page]
        
        viewport = self.viewport()
        if pages:
            for p in pages:
                rect = self.visibleRect() & p.geometry()
                if rect and (not p.renderer or p.renderer.update(p, viewport, rect.translated(-p.pos()), self.lazyUpdate)):
                    viewport.update(rect.translated(self.layoutPosition()))
        else:
            viewport.update()

    def rerender(self, page=None):
        """Schedule the specified page or all pages for rerendering.
        
        Call this when you have changed render options or page contents.
        Repaints the page or visible pages lazily, reducing flicker.
        
        """
        renderers = collections.defaultdict(list)
        pages = (page,) if page else self._pageLayout
        for p in pages:
            if p.renderer:
                renderers[p.renderer].append(p)
        for renderer, pages in renderers.items():
            renderer.invalidate(pages)
        self.lazyUpdate(page)

    def _unschedulePages(self, pages):
        """(Internal.)
        Unschedule rendering of pages that are pending but not needed anymore.
        
        Called inside paintEvent, on zoomFactor change and some other places.
        This prevents rendering jobs hogging the cpu for pages that are deleted
        or out of view.
        
        """
        unschedule = collections.defaultdict(set)
        for page in pages:
            if page.renderer:
                unschedule[page.renderer].add(page)
        for renderer, pages in unschedule.items():
            renderer.unschedule(pages, self.repaintPage)
        
    def pagesToPaint(self, event, painter):
        """Yield (page, rect) to paint at the event's rectangle.
        
        The rect describes the part of the page actually to draw. (The full
        rect can be found in page.rect().) Translates the painter to each page.
        
        """
        layout_pos = self.layoutPosition()
        ev_rect = event.rect().translated(-layout_pos)
        for p in self._pageLayout.pagesAt(ev_rect):
            painter.save()
            painter.translate(layout_pos + p.pos())
            yield p, (p.geometry() & ev_rect).translated(-p.pos())
            painter.restore()

    def paintEvent(self, ev):
        """Paint the contents of the viewport."""
        painter = QPainter(self.viewport())
        pages_to_paint = set()
        for p, r in self.pagesToPaint(ev, painter):
            p.paint(painter, r, self.repaintPage)
            pages_to_paint.add(p)

        # remove pending render jobs for pages that were visible, but are not
        # visible now
        rect = self.visibleRect()
        pages = set(page
            for page in self._prev_pages_to_paint - pages_to_paint
                if not rect.intersects(page.geometry()))
        self._unschedulePages(pages)
        self._prev_pages_to_paint = pages_to_paint

    def wheelEvent(self, ev):
        """Reimplemented to support wheel zooming and paging through page sets."""
        if self.wheelZoomingEnabled and ev.angleDelta().y() and ev.modifiers() & Qt.CTRL:
            factor = 1.1 ** util.sign(ev.angleDelta().y())
            self.setZoomFactor(self.zoomFactor() * factor, ev.pos())
        elif not ev.modifiers():
            # if scrolling is not possible, try going to next or previous pageset.
            sb = self.verticalScrollBar()
            if ev.angleDelta().y() > 0 and sb.value() == 0:
                self.displayPageSet("previous")
            elif ev.angleDelta().y() < 0 and sb.value() == sb.maximum():
                self.displayPageSet("next")
            else:
                super().wheelEvent(ev)
        else:
            super().wheelEvent(ev)

    def mouseMoveEvent(self, ev):
        """Implemented to adjust the mouse cursor depending on the page contents."""
        # no cursor updates when dragging the background is busy, see scrollarea.py.
        if not self.isDragging():
            self.adjustCursor(ev.pos())
        super().mouseMoveEvent(ev)

    def keyPressEvent(self, ev):
        """Reimplemented to go to next or previous page set if possible."""
        # ESC clears the selection, if any.
        if (ev.key() == Qt.Key_Escape and not ev.modifiers() 
            and self.rubberband() and self.rubberband().hasSelection()):
            self.rubberband().clearSelection()
            return

        # Paging through page sets?
        sb = self.verticalScrollBar()
        if ev.key() == Qt.Key_PageUp and sb.value() == 0:
            self.displayPageSet("previous")
        elif ev.key() == Qt.Key_PageDown and sb.value() == sb.maximum():
            self.displayPageSet("next")
        elif ev.key() == Qt.Key_Home and ev.modifiers() == Qt.ControlModifier:
            self.displayPageSet("first")
        elif ev.key() == Qt.Key_End and ev.modifiers() == Qt.ControlModifier:
            self.displayPageSet("last")
        else:
            super().keyPressEvent(ev)

