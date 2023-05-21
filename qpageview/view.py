# -*- coding: utf-8 -*-
#
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
from PyQt5.QtWidgets import QGestureEvent, QPinchGesture, QStyle
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

    # orientation:
    Horizontal,
    Vertical,
)


Position = collections.namedtuple("Position", "pageNumber x y")


class View(scrollarea.ScrollArea):
    """View is a generic scrollable widget to display Pages in a layout.

    Using setPageLayout() you can set a PageLayout to the View, and you can
    add Pages to the layout using a list-like api. (PageLayout derives from
    list). A simple PageLayout is set by default. Call updatePageLayout() after
    every change to the layout (like adding or removing pages).

    You can also add a Magnifier to magnify parts of a Page, and a Rubberband
    to enable selecting a rectangular region.

    View emits the following signals:

    :attr:`pageCountChanged` (int)
        emitted when the total amount of pages has changed

    :attr:`currentPageNumberChanged` (int)
        emitted when the current page number has changed (starting with 1)

    :attr:`viewModeChanged` (int)
        emitted when the ``viewMode`` has changed

    :attr:`rotationChanged` (int)
        emitted when the ``rotation`` has changed

    :attr:`orientationChanged` (int)
        emitted when the ``orientation`` has changed

    :attr:`zoomFactorChanged` (float)
        emitted when the ``zoomFactor`` has changed

    :attr:`continuousModeChanged` (bool)
        emitted when the ``continuousMode`` has changed

    :attr:`pageLayoutModeChanged` (str)
        emitted when the ``pageLayoutMode`` has changed

    :attr:`pageLayoutUpdated` ()
        emitted whenever the page layout has been updated (redraw/resize)

    """

    MIN_ZOOM = 0.05
    MAX_ZOOM = 64.0

    #: whether to enable mouse wheel zooming
    wheelZoomingEnabled = True

    #: whether to enable kinetic scrolling while paging (setCurrentPageNumber)
    kineticPagingEnabled = True

    #: whether to keep track of current page while scrolling
    pagingOnScrollEnabled = True

    #: whether a mouse click in a page makes it the current page
    clickToSetCurrentPageEnabled = True

    #: whether PageUp and PageDown call setCurrentPageNumber instead of scroll
    strictPagingEnabled = False

    #: can be set to a DocumentPropertyStore object. If set, the object is
    #: used to store certain View settings on a per-document basis.
    #: (This happens in the :meth:`clear` and :meth:`setDocument` methods.)
    documentPropertyStore = None

    #: (int) emitted when the total amount of pages has changed
    pageCountChanged = pyqtSignal(int)

    #: (int) emitted when the current page number has changed (starting with 1)
    currentPageNumberChanged = pyqtSignal(int)

    #: (int) emitted when the ``viewMode`` has changed
    viewModeChanged = pyqtSignal(int)

    #: (int) emitted when the ``rotation`` has changed
    rotationChanged = pyqtSignal(int)

    #: (int) emitted when the ``orientation`` has changed
    orientationChanged = pyqtSignal(int)

    #: (float) emitted when the ``zoomFactor`` has changed
    zoomFactorChanged = pyqtSignal(float)

    #: (bool) emitted when the ``continuousMode`` has changed
    continuousModeChanged = pyqtSignal(bool)

    #: (str) emitted when the ``pageLayoutMode`` has changed
    pageLayoutModeChanged = pyqtSignal(str)

    #: emitted whenever the page layout has been updated (redraw/resize)
    pageLayoutUpdated = pyqtSignal()

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, **kwds)
        self._document = None
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
        props = self.properties().setdefaults()
        self._viewMode = props.viewMode
        self._pageLayout.continuousMode = props.continuousMode
        self._pageLayout.orientation = props.orientation
        self._pageLayoutMode = props.pageLayoutMode
        self.pageLayout().engine = self.pageLayoutModes()[props.pageLayoutMode]()

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
        if page:
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

    def pages(self):
        """Return a list of all Pages in the page layout."""
        return list(self._pageLayout)

    def position(self):
        """Return a three-tuple Position(pageNumber, x, y).

        The Position describes where the center of the viewport is on the layout.
        The page is the page number (starting with 1) and x and y the position
        on the page, in a 0..1 range. This way a position can be remembered even
        if the zoom or orientation of the layout changes.

        """
        pos = self.viewport().rect().center()
        i, x, y = self._pageLayout.pos2offset(pos - self.layoutPosition())
        return Position(i + 1, x, y)

    def setPosition(self, position, allowKinetic=True):
        """Centers the view on the spot stored in the specified Position.

        If allowKinetic is False, immediately jumps to the position, otherwise
        scrolls smoothly (if kinetic scrolling is enabled).

        """
        i, x, y = position
        rect = self.viewport().rect()
        rect.moveCenter(self._pageLayout.offset2pos((i - 1, x, y)))
        self.ensureVisible(rect, allowKinetic=allowKinetic)

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

    def pageLayoutModes(self):
        """Return a dictionary mapping names to callables.

        The callable returns a configured LayoutEngine that is set to the
        page layout. You can reimplement this method to returns more layout
        modes, but it is required that the name "single" exists.

        """
        def single():
            return layout.LayoutEngine()

        def raster():
            return layout.RasterLayoutEngine()

        def double_left():
            engine = layout.RowLayoutEngine()
            engine.pagesPerRow = 2
            engine.pagesFirstRow = 0
            return engine

        def double_right():
            engine = double_left()
            engine.pagesFirstRow = 1
            return engine

        return locals()

    def pageLayoutMode(self):
        """Return the currently set page layout mode."""
        return self._pageLayoutMode

    def setPageLayoutMode(self, mode):
        """Set the page layout mode.

        The mode is one of the names returned by pageLayoutModes().
        The mode name "single" is guaranteed to exist.

        """
        if mode != self._pageLayoutMode:
            # get a suitable LayoutEngine
            try:
                engine = self.pageLayoutModes()[mode]()
            except KeyError:
                return
            self._pageLayout.engine = engine
            # keep the current page in view
            page = self.currentPage()
            self.updatePageLayout()
            if page:
                margins = self._pageLayout.margins() + self._pageLayout.pageMargins()
                with self.pagingOnScrollDisabled():
                    self.ensureVisible(page.geometry(), margins, False)
            self._pageLayoutMode = mode
            self.pageLayoutModeChanged.emit(mode)
            if self.viewMode():
                with self.keepCentered():
                    self.fitPageLayout()

    def updatePageLayout(self, lazy=False):
        """Update layout, adjust scrollbars, keep track of page count.

        If lazy is set to True, calls lazyUpdate() to update the view.

        """
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
        self.lazyUpdate() if lazy else self.viewport().update()

    @contextlib.contextmanager
    def modifyPages(self):
        """Return the list of pages and enter a context to make modifications.

        Note that the first page is at index 0.
        On exit of the context the page layout is updated.

        """
        pages = list(self._pageLayout)
        if self.rubberband():
            selectedpages = set(p for p, r in self.rubberband().selectedPages())
        else:
            selectedpages = set()
        lazy = bool(pages)
        try:
            yield pages
        finally:
            lazy &= bool(pages)
            removedpages = set(self._pageLayout) - set(pages)
            if selectedpages & removedpages:
                self.rubberband().clearSelection() # rubberband'll always be there
            self._unschedulePages(removedpages)
            self._pageLayout[:] = pages
            if self._viewMode:
                zoomFactor = self._pageLayout.zoomFactor
                self.fitPageLayout()
                if zoomFactor != self._pageLayout.zoomFactor:
                    lazy = False
            self.updatePageLayout(lazy)

    @contextlib.contextmanager
    def modifyPage(self, num):
        """Return the page (numbers start with 1) and enter a context.

        On exit of the context, the page layout is updated.

        """
        page = self.page(num)
        yield page
        if page:
            self._unschedulePages((page,))
            self.updatePageLayout(True)

    def clear(self):
        """Convenience method to clear the current layout."""
        self.setPages([])

    def setPages(self, pages):
        """Load the iterable of pages into the View.

        Existing pages are removed, and the document is set to None.

        """
        if self.documentPropertyStore and self._document:
            self.documentPropertyStore.set(self._document, self.properties().get(self))
        self._document = None
        with self.modifyPages() as pgs:
            pgs[:] = pages

    def setDocument(self, document):
        """Set the Document to display (see document.Document)."""
        store = self._document is not document and self.documentPropertyStore
        if store and self._document:
            store.set(self._document, self.properties().get(self))
        self._document = document
        with self.modifyPages() as pages:
            pages[:] = document.pages()
        if store:
            (store.get(document) or store.default or self.properties()).set(self)

    def document(self):
        """Return the Document currently displayed (see document.Document)."""
        return self._document

    def reload(self):
        """If a Document was set, invalidate()s it and then reloads it."""
        if self._document:
            self._document.invalidate()
            with self.modifyPages() as pages:
                pages[:] = self._document.pages()

    def loadPdf(self, filename, renderer=None):
        """Convenience method to load the specified PDF file.

        The filename can also be a QByteArray or an already loaded
        popplerqt5.Poppler.Document instance.

        """
        from . import poppler
        self.setDocument(poppler.PopplerDocument(filename, renderer))

    def loadSvgs(self, filenames, renderer=None):
        """Convenience method to load the specified list of SVG files.

        Each SVG file is loaded in one Page. A filename can also be a
        QByteArray.

        """
        from . import svg
        self.setDocument(svg.SvgDocument(filenames, renderer))

    def loadImages(self, filenames, renderer=None):
        """Convenience method to load images from the specified list of files.

        Each image is loaded in one Page. A filename can also be a
        QByteArray or a QImage.

        """
        from . import image
        self.setDocument(image.ImageDocument(filenames, renderer))

    def print(self, printer=None, pageNumbers=None, showDialog=True):
        """Print all, or speficied pages to QPrinter printer.

        If given the pageNumbers should be a list containing page numbers
        starting with 1. If showDialog is True, a print dialog is shown, and
        printing is canceled when the user cancels the dialog.

        If the QPrinter to use is not specified, a default one is created.
        The print job is started and returned (a printing.PrintJob instance),
        so signals for monitoring the progress could be connected to. (If the
        user cancels the dialog, no print job is returned.)

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
        job = printing.PrintJob(printer, pageList)
        job.start()
        return job

    @staticmethod
    def properties():
        """Return an uninitialized ViewProperties object."""
        return ViewProperties()

    def readProperties(self, settings):
        """Read View settings from the QSettings object.

        If a documentPropertyStore is set, the settings are also set
        as default for the DocumentPropertyStore.

        """
        props = self.properties().load(settings)
        props.position = None   # storing the position makes no sense
        props.set(self)
        if self.documentPropertyStore:
            self.documentPropertyStore.default = props

    def writeProperties(self, settings):
        """Write the current View settings to the QSettings object.

        If a documentPropertyStore is set, the settings are also set
        as default for the DocumentPropertyStore.

        """
        props = self.properties().get(self)
        props.position = None   # storing the position makes no sense
        props.save(settings)
        if self.documentPropertyStore:
            self.documentPropertyStore.default = props

    def setViewMode(self, mode):
        """Sets the current ViewMode."""
        if mode == self._viewMode:
            return
        self._viewMode = mode
        if mode:
            with self.keepCentered():
                self.fitPageLayout()
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
                self.fitPageLayout()
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
                self.fitPageLayout()
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
                    self.fitPageLayout()
                self.continuousModeChanged.emit(True)
        elif oldcontinuous:
            p = self.currentPage()
            index = layout.index(p) if p else 0
            with self.pagingOnScrollDisabled(), self.keepCentered():
                layout.continuousMode = False
                layout.currentPageSet = layout.pageSet(index)
                self.fitPageLayout()
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
        self.fitPageLayout()
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
        if not self.isScrolling() and not self.isDragging():
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

    def fitPageLayout(self):
        """Fit the layout according to the view mode.

        Does nothing in FixedScale mode. Prevents scrollbar/resize loops by
        precalculating which scrollbars will appear.

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
            if self._pageLayout.zoomsToFit():
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

    def visiblePages(self, rect=None):
        """Yield the Page instances that are currently visible.

        If rect is not given, the visibleRect() is used.  The pages are sorted
        so that the pages with the largest visible part come first.

        """
        if rect is None:
            rect = self.visibleRect()
        def key(page):
            overlayrect = rect & page.geometry()
            return overlayrect.width() * overlayrect.height()
        return sorted(self._pageLayout.pagesAt(rect), key=key, reverse=True)

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
        viewport = self.viewport()
        full = True
        updates = []
        for p in self.visiblePages():
            rect = self.visibleRect() & p.geometry()
            if rect and p.renderer:
                info = p.renderer.info(p, viewport, rect.translated(-p.pos()))
                if info.missing:
                    full = False
                    if page is p or page is None:
                        p.renderer.schedule(p, info.key, info.missing, self.lazyUpdate)
                elif page is p or page is None:
                    updates.append(rect.translated(self.layoutPosition()))
        if full:
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

        The pages are sorted with largest area last.

        """
        layout_pos = self.layoutPosition()
        ev_rect = rect.translated(-layout_pos)
        for p in self.visiblePages(ev_rect):
            r = (p.geometry() & ev_rect).translated(-p.pos())
            painter.save()
            painter.translate(layout_pos + p.pos())
            yield p, r
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
            factor = gesture.property("totalScaleFactor")
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
                self.fitPageLayout()
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
        if ev.key() == Qt.Key_PageUp:
            if sp:
                self.gotoPreviousPage()
            elif sb.value() == 0:
                self.displayPageSet("previous")
            else:
                super().keyPressEvent(ev)
        elif ev.key() == Qt.Key_PageDown:
            if sp:
                self.gotoNextPage()
            elif sb.value() == sb.maximum():
                self.displayPageSet("next")
            else:
                super().keyPressEvent(ev)
        elif ev.key() == Qt.Key_Home and ev.modifiers() == Qt.ControlModifier:
            self.setCurrentPageNumber(1) if sp else self.displayPageSet("first")
        elif ev.key() == Qt.Key_End and ev.modifiers() == Qt.ControlModifier:
            self.setCurrentPageNumber(self.pageCount()) if sp else self.displayPageSet("last")
        else:
            super().keyPressEvent(ev)


class ViewProperties:
    """Simple helper class encapsulating certain settings of a View.

    The settings can be set to and got from a View, and saved to or loaded
    from a QSettings group.

    Class attributes serve as default values, None means: no change.
    All methods return self, so operations can easily be chained.

    If you inherit from a View and add more settings, you can also add
    properties to this class by inheriting from it. Reimplement
    View.properties() to return an instance of your new ViewProperties
    subclass.

    """
    position = None
    rotation = Rotate_0
    zoomFactor = 1.0
    viewMode = FixedScale
    orientation = None
    continuousMode = None
    pageLayoutMode = None

    def setdefaults(self):
        """Set all properties to default values. Also used by View on init."""
        self.orientation = Vertical
        self.continuousMode = True
        self.pageLayoutMode = "single"
        return self

    def copy(self):
        """Return a copy or ourselves."""
        cls = type(self)
        props = cls.__new__(cls)
        props.__dict__.update(self.__dict__)
        return props

    def names(self):
        """Return a tuple with all the property names we support."""
        return (
            'position',
            'rotation',
            'zoomFactor',
            'viewMode',
            'orientation',
            'continuousMode',
            'pageLayoutMode',
        )

    def mask(self, names):
        """Set properties not listed in names to None."""
        for name in self.names():
            if name not in names and getattr(self, name) is not None:
                setattr(self, name, None)
        return self

    def get(self, view):
        """Get the properties of a View."""
        self.position = view.position()
        self.rotation = view.rotation()
        self.orientation = view.orientation()
        self.viewMode = view.viewMode()
        self.zoomFactor = view.zoomFactor()
        self.continuousMode = view.continuousMode()
        self.pageLayoutMode = view.pageLayoutMode()
        return self

    def set(self, view):
        """Set all our properties that are not None to a View."""
        if self.pageLayoutMode is not None:
            view.setPageLayoutMode(self.pageLayoutMode)
        if self.rotation is not None:
            view.setRotation(self.rotation)
        if self.orientation is not None:
            view.setOrientation(self.orientation)
        if self.continuousMode is not None:
            view.setContinuousMode(self.continuousMode)
        if self.viewMode is not None:
            view.setViewMode(self.viewMode)
        if self.zoomFactor is not None:
            if self.viewMode is FixedScale or not view.pageLayout().zoomsToFit():
                view.setZoomFactor(self.zoomFactor)
        if self.position is not None:
            view.setPosition(self.position, False)
        return self

    def save(self, settings):
        """Save the properties that are not None to a QSettings group."""
        if self.pageLayoutMode is not None:
            settings.setValue("pageLayoutMode", self.pageLayoutMode)
        else:
            settings.remove("pageLayoutMode")
        if self.rotation is not None:
            settings.setValue("rotation", self.rotation)
        else:
            settings.remove("rotation")
        if self.orientation is not None:
            settings.setValue("orientation", self.orientation)
        else:
            settings.remove("orientation")
        if self.continuousMode is not None:
            settings.setValue("continuousMode", self.continuousMode)
        else:
            settings.remove("continuousMode")
        if self.viewMode is not None:
            settings.setValue("viewMode", self.viewMode)
        else:
            settings.remove("viewMode")
        if self.zoomFactor is not None:
            settings.setValue("zoomFactor", self.zoomFactor)
        else:
            settings.remove("zoomFactor")
        if self.position is not None:
            settings.setValue("position/pageNumber", self.position.pageNumber)
            settings.setValue("position/x", self.position.x)
            settings.setValue("position/y", self.position.y)
        else:
            settings.remove("position")
        return self

    def load(self, settings):
        """Load the properties from a QSettings group."""
        if settings.contains("pageLayoutMode"):
            v = settings.value("pageLayoutMode", "", str)
            if v:
                self.pageLayoutMode = v
        if settings.contains("rotation"):
            v = settings.value("rotation", -1, int)
            if v in (Rotate_0, Rotate_90, Rotate_180, Rotate_270):
                self.rotation = v
        if settings.contains("orientation"):
            v = settings.value("orientation", 0, int)
            if v in (Horizontal, Vertical):
                self.orientation = v
        if settings.contains("continuousMode"):
            v = settings.value("continuousMode", True, bool)
            self.continuousMode = v
        if settings.contains("viewMode"):
            v = settings.value("viewMode", -1, int)
            if v in (FixedScale, FitHeight, FitWidth, FitBoth):
                self.viewMode = v
        if settings.contains("zoomFactor"):
            v = settings.value("zoomFactor", 0, float)
            if v:
                self.zoomFactor = v
        if settings.contains("position/pageNumber"):
            pageNumber = settings.value("position/pageNumber", -1, int)
            if pageNumber != -1:
                x = settings.value("position/x", 0.0, float)
                y = settings.value("position/y", 0.0, float)
                self.position = Position(pageNumber, x, y)
        return self


class DocumentPropertyStore:
    """Store ViewProperties (settings) on a per-Document basis.

    If you create a DocumentPropertyStore and install it in the
    documentPropertyStore attribute of a View, the View will automatically
    remember its settings for earlier displayed Document instances.

    """

    default = None
    mask = None

    def __init__(self):
        self._properties = weakref.WeakKeyDictionary()

    def get(self, document):
        """Get the View properties stored for the document, if available.

        If a ViewProperties instance is stored in the `default` attribute,
        it is returned when no properties were available. Otherwise, None
        is returned.

        """
        props = self._properties.get(document)
        if props is None:
            if self.default:
                props = self.default
                if self.mask:
                    props = props.copy().mask(self.mask)
        return props

    def set(self, document, properties):
        """Store the View properties for the document.

        If the `mask` attribute is set to a list or tuple of names, only the
        listed properties are remembered.

        """
        if self.mask:
            properties.mask(self.mask)
        self._properties[document] = properties

