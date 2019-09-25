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
from PyQt5.QtWidgets import QGestureEvent, QStyle
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

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
    
    `pageCountChanged`          When the number of pages changes.

    `currentPageNumberChanged`  When the current page number changes.

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
    
    wheelZoomingEnabled = True      # zoom the View using the mouse wheel
    kineticPagingEnabled = True     # scroll smoothly on setCurrentPageNumber
    pagingOnScrollEnabled = True    # keep track of current page while scrolling
    clickToSetCurrentPageEnabled = True  # any mouseclick on a page sets it the current page
    strictPagingEnabled = False     # PageUp, PageDown and wheel call setCurrentPageNumber i.s.o. scroll

    MIN_ZOOM = 0.05
    MAX_ZOOM = 64.0

    """

    MIN_ZOOM = 0.05
    MAX_ZOOM = 64.0

    wheelZoomingEnabled = True
    kineticPagingEnabled = True  # scroll smoothly on setCurrentPageNumber
    pagingOnScrollEnabled = True # keep track of current page while scrolling
    clickToSetCurrentPageEnabled = True  # any mouseclick on a page sets it the current page
    strictPagingEnabled = False  # PageUp and PageDown call setCurrentPageNumber i.s.o. scroll

    pageCountChanged = pyqtSignal(int)
    currentPageNumberChanged = pyqtSignal(int)
    viewModeChanged = pyqtSignal(int)
    rotationChanged = pyqtSignal(int)
    orientationChanged = pyqtSignal(int)
    zoomFactorChanged = pyqtSignal(float)
    pageLayoutUpdated = pyqtSignal()
    continuousModeChanged = pyqtSignal(bool)

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._currentPageNumber = 0
        self._pageCount = 0
        self._scrollingToPage = 0
        self._prev_pages_to_paint = set()
        self._viewMode = FixedScale
        self._pageLayout = None
        self._magnifier = None
        self._rubberband = None
        self._pinchStartFactor = None
        self.grabGesture(Qt.PinchGesture)
        self.viewport().setBackgroundRole(QPalette.Dark)
        self.verticalScrollBar().setSingleStep(20)
        self.horizontalScrollBar().setSingleStep(20)
        self.setMouseTracking(True)
        self.setMinimumSize(QSize(60, 60))
        self.setPageLayout(layout.PageLayout())

    def pageCount(self):
        """Return the number of pages in the view."""
        return self._pageCount

    def currentPageNumber(self):
        """Return the current page number in view (starting with 1)."""
        return self._currentPageNumber
    
    def setCurrentPageNumber(self, num):
        """Scrolls to the specified page number (starting with 1).
        
        If the page is already in view, the view is not scrolled, otherwise
        the view is scrolled to center the page. (If the page is larger than 
        the view, the top-left corner is positioned top-left in the view.)
        
        """
        self.updateCurrentPageNumber(num)
        page = self.currentPage()
        margins = self._pageLayout.margins() + self._pageLayout.pageMargins()
        with self.pagingOnScrollDisabled():
            self.ensureVisible(page.geometry(), margins, self.kineticPagingEnabled)
        if self.isScrolling():
            self._scrollingToPage = True
    
    def updateCurrentPageNumber(self, num):
        """Set the current page number without scrolling the view."""
        count = self.pageCount()
        n = max(min(count, num), 1 if count else 0)
        if n == num and n != self._currentPageNumber:
            self._currentPageNumber = num
            self.currentPageNumberChanged.emit(num)

    def gotoNextPage(self):
        """Convenience method to go to the next page."""
        num = self.currentPageNumber()
        if num < self.pageCount():
            self.setCurrentPageNumber(num + 1)
    
    def gotoPreviousPage(self):
        """Convenience method to go to the previous page."""
        num = self.currentPageNumber()
        if num > 1:
            self.setCurrentPageNumber(num - 1)

    def currentPage(self):
        """Return the page pointed to by currentPageNumber()."""
        if self._pageCount:
            return self._pageLayout[self._currentPageNumber-1]

    def page(self, num):
        """Return the page at the specified number (starting at 1)."""
        if 0 < num <= self._pageCount:
            return self._pageLayout[num-1]

    def setPageLayout(self, layout):
        """Set our current PageLayout instance.
        
        The dpiX and dpiY attributes of the layout are set to the physical
        resolution of the widget, which should result in a natural size of 100%
        at zoom factor 1.0.
        
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
        """Update layout, adjust scrollbars, keep track of page count."""
        self._pageLayout.update()

        # keep track of page count
        count = self._pageLayout.count()
        if count != self._pageCount:
            self._pageCount = count
            self.pageCountChanged.emit(count)
            n = max(min(count, self._currentPageNumber), 1 if count else 0)
            self.updateCurrentPageNumber(n)

        self.setAreaSize(self._pageLayout.size())
        self.pageLayoutUpdated.emit()
        self.viewport().update()

    @contextlib.contextmanager
    def modifyPages(self):
        """Return the list of pages and enter a context to make modifications.

        Note that the first page is at index 0.
        On exit of the context the page layout is updated.

        """
        pages = list(self._pageLayout)
        yield pages
        self._unschedulePages(list(set(self._pageLayout) - set(pages)))
        self._pageLayout[:] = pages
        self.updatePageLayout()

    @contextlib.contextmanager
    def modifyPage(self, num):
        """Return the page (numbers start with 1) and enter a context.

        On exit of the context, the page layout is updated.

        """
        page = self.page(num)
        yield page
        if page:
            self._unschedulePages((page,))
            self.updatePageLayout()

    def clear(self):
        """Convenience method to clear the current layout."""
        with self.modifyPages() as pages:
            pages.clear()

    def loadPopplerDocument(self, document, renderer=None):
        """Convenience method to display the loaded Poppler.Document."""
        from . import poppler
        with self.modifyPages() as pages:
            pages[:] = poppler.PopplerPage.loadPopplerDocument(document, renderer)

    def loadPdf(self, filename, renderer=None):
        """Convenience method to load the specified PDF file.

        The filename can also be a QByteArray.

        """
        from . import poppler
        with self.modifyPages() as pages:
            pages[:] = poppler.PopplerPage.load(filename, renderer)

    def loadSvgs(self, filenames, renderer=None):
        """Convenience method to load the specified list of SVG files.

        Each SVG file is loaded in one Page. A filename can also be a
        QByteArray.

        """
        from . import svg
        with self.modifyPages() as pages:
            pages[:] = svg.SvgPage.loadFiles(filenames, renderer)

    def loadImages(self, filenames, renderer=None):
        """Convenience method to load images from the specified list of files.

        Each image is loaded in one Page. A filename can also be a
        QByteArray. The renderer argument is currently not used.

        """
        from . import image
        with self.modifyPages() as pages:
            pages[:] = image.ImagePage.loadFiles(filenames)

    def print(self, printer=None, pageNumbers=None, showDialog=True):
        """Print all, or speficied pages to QPrinter printer.

        If given the pageNumbers should be a list containing page numbers
        starting with 1. If showDialog is True, a print dialog is shown, and
        printing is canceled when the user cancels the dialog.

        If the QPrinter to use is not specified, a default one is created.

        """
        if printer is None:
            printer = QPrinter()
            printer.setResolution(300)
        if showDialog:
            dlg = QPrintDialog(printer, self)
            dlg.setMinMax(1, self.pageCount())
            if not dlg.exec_():
                return  # cancelled
        if not pageNumbers:
            if printer.printRange() == QPrinter.CurrentPage:
                pageNumbers = [self.currentPageNumber()]
            else:
                if printer.printRange() == QPrinter.PageRange:
                    first = printer.toPage() or 1
                    last = printer.fromPage() or self.pageCount()
                else:
                    first, last = 1, self.pageCount()
                pageNumbers = list(range(first, last + 1))
            if printer.pageOrder() == QPrinter.LastPageFirst:
                pageNumbers.reverse()
        # add the page objects
        pageList = [(n, self.page(n)) for n in pageNumbers]
        from . import printing
        # TODO some progress indication and cancel opportunity
        printing.PrintJob(printer, pageList).start()

    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            with self.keepCentered():
                self._fitLayout()
        else:
            # call layout once to tell FixedScale is active
            self.pageLayout().fit(QSize(), mode)
        self.viewModeChanged.emit(mode)

    def viewMode(self):
        """Returns the current ViewMode."""
        return self._viewMode

    def setRotation(self, rotation):
        """Set the current rotation."""
        layout = self._pageLayout
        if rotation != layout.rotation:
            with self.keepCentered():
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
            with self.keepCentered():
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
                with self.pagingOnScrollDisabled(), self.keepCentered():
                    layout.continuousMode = True
                    if self._viewMode:
                        self._fitLayout()
                self.continuousModeChanged.emit(True)
        elif oldcontinuous:
            p = self.currentPage()
            index = layout.index(p) if p else 0
            with self.pagingOnScrollDisabled(), self.keepCentered():
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

        sb = None  # where to move the scrollbar after fitlayout
        if what == "first":
            what = 0
            sb = "up"   # move to the start
        elif what == "last":
            what = layout.pageSetCount() - 1
            sb = "down" # move to the end
        elif what == "previous":
            what = layout.currentPageSet - 1
            if what < 0:
                return
            sb = "down"
        elif what == "next":
            what = layout.currentPageSet + 1
            if what >= layout.pageSetCount():
                return
            sb = "up"
        elif not 0 <= what < layout.pageSetCount():
            return
        layout.currentPageSet = what
        if self._viewMode:
            self._fitLayout()
        self.updatePageLayout()
        if sb:
            self.verticalScrollBar().setValue(0 if sb == "up" else self.verticalScrollBar().maximum())
        if self.pagingOnScrollEnabled and not self._scrollingToPage:
            s = layout.currentPageSetSlice()
            num = s.stop - 1 if sb == "down" else s.start
            self.updateCurrentPageNumber(num + 1)

    def setMagnifier(self, magnifier):
        """Sets the Magnifier to use (or None to disable the magnifier).

        The viewport takes ownership of the Magnifier.

        """
        if self._magnifier:
            self.viewport().removeEventFilter(self._magnifier)
            self._magnifier.setParent(None)
        self._magnifier = magnifier
        if magnifier:
            magnifier.setParent(self.viewport())
            self.viewport().installEventFilter(magnifier)

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
            rubberband.clearSelection()
            self.viewport().installEventFilter(rubberband)
            self.zoomFactorChanged.connect(rubberband.slotZoomChanged)
            self.rotationChanged.connect(rubberband.clearSelection)

    def rubberband(self):
        """Return the currently set rubberband."""
        return self._rubberband

    @contextlib.contextmanager
    def pagingOnScrollDisabled(self):
        """During this context a scroll is not tracked to update the current page number."""
        old, self._scrollingToPage = self._scrollingToPage, True
        try:
            yield
        finally:
            self._scrollingToPage = old
        
    def scrollContentsBy(self, dx, dy):
        """Reimplemented to move the rubberband and adjust the mouse cursor."""
        if self._rubberband:
            self._rubberband.scrollBy(QPoint(dx, dy))
        if not self.isScrolling():
            # don't adjust the cursor during a kinetic scroll
            pos = self.viewport().mapFromGlobal(QCursor.pos())
            if pos in self.viewport().rect() and not self.viewport().childAt(pos):
                self.adjustCursor(pos)
        self.viewport().update()

        # keep track of current page. If the scroll wasn't initiated by the 
        # setCurrentPage() call, check # whether the current page number needs
        # to be updated
        if self.pagingOnScrollEnabled and not self._scrollingToPage and self.pageCount() > 0:
            # do nothing if current page is still fully in view
            if self.currentPage().geometry() not in self.visibleRect():
                # find the page in the center of the view
                layout = self._pageLayout
                pos = self.visibleRect().center()
                p = layout.pageAt(pos) or layout.nearestPageAt(pos)
                if p:
                    num = layout.index(p) + 1
                    self.updateCurrentPageNumber(num)

    def stopScrolling(self):
        """Reimplemented to adjust the mouse cursor on scroll stop."""
        super().stopScrolling()
        self._scrollingToPage = False
        pos = self.viewport().mapFromGlobal(QCursor.pos())
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
    def keepCentered(self, pos=None):
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
            with self.keepCentered(pos):
                self._pageLayout.zoomFactor = factor
            if self._pageLayout.zoomToFit:
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

    def zoomNaturalSize(self, pos=None):
        """Zoom to the natural pixel size of the current page.

        The natural pixel size zoom factor can be different than 1.0, if the
        screen's DPI differs from the current page's DPI.

        """
        p = self.currentPage()
        factor = p.dpi / self.physicalDpiX() if p else 1.0
        self.setZoomFactor(factor, pos)

    def layoutPosition(self):
        """Return the position of the PageLayout relative to the viewport.

        This is the top-left position of the layout, relative to the
        top-left position of the viewport.

        If the layout is smaller than the viewport it is centered by default.
        (See ScrollArea.alignment.)

        """
        return self.areaPos() - self._pageLayout.pos()

    def visibleRect(self):
        """Return the QRect of the page layout that is currently visible in the viewport."""
        return self.visibleArea().translated(self._pageLayout.pos())

    def visiblePages(self):
        """Yield the Page instances that are currently visible."""
        return self._pageLayout.pagesAt(self.visibleRect())

    def ensureVisible(self, rect, margins=None, allowKinetic=True):
        """Ensure rect is visible, switching page set if necessary."""
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
        rect = rect.translated(-self._pageLayout.pos())
        super().ensureVisible(rect, margins, allowKinetic)

    def adjustCursor(self, pos):
        """Sets the correct mouse cursor for the position on the page."""
        pass

    def repaintPage(self, page):
        """Call this when you want to redraw the specified page."""
        rect = page.geometry().translated(self.layoutPosition())
        self.viewport().update(rect)

    def lazyUpdate(self, page=None):
        """Lazily repaint page (if visible) or all visible pages.
        
        Defers updating the viewport for a page until all rendering tasks for
        that page have finished. This reduces flicker.
        
        """
        pages = list(self.visiblePages())
        if page and page in pages:
            pages = [page]
        
        viewport = self.viewport()
        wait = False
        updates = []
        if pages:
            for p in pages:
                rect = self.visibleRect() & p.geometry()
                if rect and p.renderer:
                    if p.renderer.update(p, viewport, rect.translated(-p.pos()), self.lazyUpdate):
                        updates.append(rect.translated(self.layoutPosition()))
                    else:
                        wait = True
        if not wait:
            viewport.update()
        elif updates:
            viewport.update(sum(updates, QRegion()))

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
        
    def pagesToPaint(self, rect, painter):
        """Yield (page, rect) to paint in the specified rectangle.
        
        The specified rect is in viewport coordinates, as in the paint event.
        The returned rect describes the part of the page actually to draw, in
        page coordinates. (The full rect can be found in page.rect().)
        Translates the painter to the top left of each page.
        
        """
        layout_pos = self.layoutPosition()
        ev_rect = rect.translated(-layout_pos)
        for p in self._pageLayout.pagesAt(ev_rect):
            painter.save()
            painter.translate(layout_pos + p.pos())
            yield p, (p.geometry() & ev_rect).translated(-p.pos())
            painter.restore()

    def event(self, ev):
        """Reimplemented to get Gesture events."""
        if isinstance(ev, QGestureEvent) and self.handleGestureEvent(ev):
            ev.accept() # Accepts all gestures in the event
            return True
        return super().event(ev)

    def handleGestureEvent(self, event):
        """Gesture event handler.

        Return False if event is not accepted. Currently only cares about 
        PinchGesture. Could also handle Swipe and Pan gestures.

        """
        ## originally contributed by David Rydh, 2017
        pinch = event.gesture(Qt.PinchGesture)
        if pinch:
            return self.pinchGesture(pinch)
        return False

    def pinchGesture(self, gesture):
        """Pinch gesture event handler.

        Return False if event is not accepted. Currently only cares about 
        ScaleFactorChanged and not RotationAngleChanged.

        """
        ## originally contributed by David Rydh, 2017
        # Gesture start? Reset _pinchStartFactor in case we didn't
        # catch the finish event
        if gesture.state() == Qt.GestureStarted:
            self._pinchStartFactor = None

        changeFlags = gesture.changeFlags()
        if changeFlags & QPinchGesture.ScaleFactorChanged:
            factor = gesture.property("scaleFactor")
            if not self._pinchStartFactor: # Gesture start?
                self._pinchStartFactor = self.zoomFactor()
            self.setZoomFactor(self._pinchStartFactor * factor,
                      self.mapFromGlobal(gesture.hotSpot().toPoint()))

        # Gesture finished?
        if gesture.state() in (Qt.GestureFinished, Qt.GestureCanceled):
            self._pinchStartFactor = None

        return True

    def paintEvent(self, ev):
        """Paint the contents of the viewport."""
        painter = QPainter(self.viewport())
        pages_to_paint = set()
        for p, r in self.pagesToPaint(ev.rect(), painter):
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

    def resizeEvent(self, ev):
        """Reimplemented to scale the view if needed and update the scrollbars."""
        if self._viewMode and not self._pageLayout.empty():
            with self.pagingOnScrollDisabled():
                # sensible repositioning
                vbar = self.verticalScrollBar()
                hbar = self.horizontalScrollBar()
                x, xm = hbar.value(), hbar.maximum()
                y, ym = vbar.value(), vbar.maximum()
                self._fitLayout()
                self.updatePageLayout()
                if xm: hbar.setValue(round(x * hbar.maximum() / xm))
                if ym: vbar.setValue(round(y * vbar.maximum() / ym))
        super().resizeEvent(ev)

    def wheelEvent(self, ev):
        """Reimplemented to support wheel zooming and paging through page sets."""
        if self.wheelZoomingEnabled and ev.angleDelta().y() and ev.modifiers() & Qt.CTRL:
            factor = 1.1 ** util.sign(ev.angleDelta().y())
            self.setZoomFactor(self.zoomFactor() * factor, ev.pos())
        elif not ev.modifiers():
            # if scrolling is not possible, try going to next or previous pageset.
            sb = self.verticalScrollBar()
            sp = self.strictPagingEnabled
            if ev.angleDelta().y() > 0 and sb.value() == 0:
                self.gotoPreviousPage() if sp else self.displayPageSet("previous")
            elif ev.angleDelta().y() < 0 and sb.value() == sb.maximum():
                self.gotoNextPage() if sp else self.displayPageSet("next")
            else:
                super().wheelEvent(ev)
        else:
            super().wheelEvent(ev)

    def mousePressEvent(self, ev):
        """Implemented to set the clicked page as current, without moving it."""
        if self.clickToSetCurrentPageEnabled:
            page = self._pageLayout.pageAt(ev.pos() - self.layoutPosition())
            if page:
                num = self._pageLayout.index(page) + 1
                self.updateCurrentPageNumber(num)
        super().mousePressEvent(ev)

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
        sp = self.strictPagingEnabled
        if ev.key() == Qt.Key_PageUp and sb.value() == 0:
            self.gotoPreviousPage() if sp else self.displayPageSet("previous")
        elif ev.key() == Qt.Key_PageDown and sb.value() == sb.maximum():
            self.gotoNextPage() if sp else self.displayPageSet("next")
        elif ev.key() == Qt.Key_Home and ev.modifiers() == Qt.ControlModifier:
            self.setCurrentPageNumber(1) if sp else self.displayPageSet("first")
        elif ev.key() == Qt.Key_End and ev.modifiers() == Qt.ControlModifier:
            self.setCurrentPageNumber(self.pageCount()) if sp else self.displayPageSet("last")
        else:
            super().keyPressEvent(ev)

