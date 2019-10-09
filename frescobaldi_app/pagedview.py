# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2019 by Wilbert Berendsen
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
Customization classes for the qpageview.View.

This is used throughout Frescobaldi, to obey color settings etc.

"""

import itertools
import os

from PyQt5.QtCore import pyqtSignal, QSettings, Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

try:
    import popplerqt5
except ImportError:
    popplerqt5 = None

import app
import textformats
import qpageview
import qpageview.layout
import qpageview.printing
import qpageview.magnifier
import qpageview.widgetoverlay


class Magnifier(qpageview.magnifier.Magnifier):
    """A magnifier that reads and stores its settings."""
    def __init__(self):
        super().__init__()
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        s = QSettings()
        s.beginGroup("musicview/magnifier")
        size = s.value("size", 350, int)
        if self.MIN_SIZE <= size <= self.MAX_SIZE:
            self.resize(size, size)
        scale = s.value("scalef", 3.0, float)
        super().setScale(scale)

    def setScale(self, scale):
        """Reimplemented to save the scale."""
        super().setScale(scale)
        QSettings().setValue("musicview/magnifier/scalef", scale)

    def resizeEvent(self, ev):
        """Reimplemented to save the size."""
        super().resizeEvent(ev)
        QSettings().setValue("musicview/magnifier/size", ev.size().width())


class View(qpageview.widgetoverlay.WidgetOverlayViewMixin, qpageview.View):
    """A View based on qpageview.View.

    This View has additional features and customisation needed in Frescobaldi.

    Besides all the qpageview.View signals, this View emits the following
    signal:

    `pageLayoutModeChanged(str)`

        emitted when the page layout mode is changed. The page layout mode is
        set using setPageLayoutMode() and internally implemented by using
        different qpageview PageLayout classes.

    """
    pageLayoutModeChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._printer = None
        self._pageLayoutMode = None
        self.setPageLayoutMode("single")
        self.setMagnifier(Magnifier())
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def pageLayoutMode(self):
        """Return the currently set page layout mode."""
        return self._pageLayoutMode

    def setPageLayoutMode(self, mode):
        """Set the page layout mode.

        The mode is one of:

            "single"
            "double_left"
            "double_right"
            "horizontal"
            "raster"

        """
        if mode != self._pageLayoutMode:
            # get a suitable PageLayout
            if mode == "raster":
                layout = qpageview.layout.RasterLayout()
            elif mode in ("double_right", "double_left"):
                layout = qpageview.layout.RowPageLayout()
                layout.pagesPerRow = 2
                layout.pagesFirstRow = 1 if mode == "double_right" else 0
            else:
                layout = qpageview.layout.PageLayout()
                layout.orientation = qpageview.Horizontal if mode == "horizontal" else qpageview.Vertical
            # add the current pages
            layout.extend(self._pageLayout)
            # copy layout settings
            layout.zoomFactor = self._pageLayout.zoomFactor
            layout.rotation = self._pageLayout.rotation
            layout.continuousMode = self._pageLayout.continuousMode
            layout.setMargins(self._pageLayout.margins())
            layout.setPageMargins(self._pageLayout.pageMargins())
            # keep the current page in view
            page = self.currentPage()
            self.setPageLayout(layout)
            if page:
                margins = layout.margins() + layout.pageMargins()
                with self.pagingOnScrollDisabled():
                    self.ensureVisible(page.geometry(), margins, False)
            self._pageLayoutMode = mode
            self.pageLayoutModeChanged.emit(mode)
            if self.viewMode():
                with self.keepCentered():
                    self._fitLayout()

    def readSettings(self):
        # kinetic scrolling
        kinetic = QSettings().value("musicview/kinetic_scrolling", True, bool)
        self.kineticPagingEnabled = kinetic
        self.kineticScrollingEnabled = kinetic

        # scrollbar visibility
        scrollbars = QSettings().value("musicview/show_scrollbars", True, bool)
        policy = Qt.ScrollBarAsNeeded if scrollbars else Qt.ScrollBarAlwaysOff
        self.setHorizontalScrollBarPolicy(policy)
        self.setVerticalScrollBarPolicy(policy)

        # set certain preferences to the existing renderers
        renderers = set(page.renderer for page in self.pageLayout() if page.renderer)
        pages = set(page for page in self.pageLayout() if not page.renderer)
        changed = False

        # paper color; change the existing renderer
        paperColor = textformats.formatData('editor').baseColors['paper']
        # if a page has no renderer, adjust the page itself :-)
        for rp in itertools.chain(renderers, pages):
            if rp.paperColor != paperColor:
                changed = True
                rp.paperColor = paperColor

        # render backend preference
        if popplerqt5:
            import qpageview.poppler
            renderBackend, printRenderBackend = getPopplerBackends()
            for r in renderers:
                if isinstance(r, qpageview.poppler.PopplerRenderer):
                    r.printRenderBackend = printRenderBackend
                    if r.renderBackend != renderBackend:
                        changed = True
                        r.renderBackend = renderBackend

        if changed:
            self.rerender()

    def loadPdf(self, filename, renderer=None):
        """Reimplemented to use a customized renderer by default."""
        super().loadPdf(filename, renderer or getRenderer("pdf"))

    def loadSvgs(self, filenames, renderer=None):
        """Reimplemented to use a customized renderer by default."""
        super().loadSvgs(filenames, renderer or getRenderer("svg"))

    def loadImages(self, filenames, renderer=None):
        """Reimplemented to use a customized renderer by default."""
        super().loadImages(filenames, renderer or getRenderer("image"))

    def print(self, printer=None, pageNumbers=None, showDialog=True):
        """Print the contents of the View."""
        import qpageview.poppler
        import qpageview.cupsprinter

        if printer is None:
            if self._printer is None:
                self._printer = QPrinter()
            printer = self._printer
        printer.setCopyCount(1) # prevent embarrassing situations :-)
        if self.document() and self.document().filename():
            filename = os.path.basename(self.document().filename())
        else:
            filename = ""
        printer.setDocName(filename)
        if showDialog:
            qpageview.cupsprinter.clearPageSetSetting(printer)
            dlg = QPrintDialog(printer, self)
            if filename:
                title = app.caption(_("Print {filename}").format(filename=filename))
            else:
                title = app.caption(_("Print"))
            dlg.setWindowTitle(title)
            dlg.setMinMax(1, self.pageCount())
            if not dlg.exec_():
                return  # cancelled
        s = QSettings()
        printer.setResolution(s.value("printing/dpi", 300, int))

        # is it possible and preferred to print a PDF directly with cups?
        if (s.value("printing/directcups", True, bool)
            and isinstance(self.document(), qpageview.poppler.PopplerDocument)
            and os.path.isfile(self.document().filename())
            and not printer.outputFileName()):
            h = qpageview.cupsprinter.handle(printer)
            if h:
                if not h.printFile(self.document().filename()):
                    QMessageBox.warning(self, _("Printing Error"),
                        _("An error occured (code: {num}):\n{message}".format(
                            message=h.error, num=h.status)))
                return
        job = super().print(printer, pageNumbers, False)
        if job:
            progress = PrintProgressDialog(job, self)
            progress.setWindowTitle(title)
            progress.setLabelText(_("Preparing to print..."))
            progress.show()


class PrintProgressDialog(qpageview.printing.PrintProgressDialog):
    def showProgress(self, page, num, total):
        """Called by the job when printing a page."""
        self.setValue(num)
        self.setLabelText(_("Printing page {page} ({num} of {total})...").format(
                page=page, num=num, total=total))

    def showErrorMessage(self):
        """Reimplemented to show a translated error message."""
        QMessageBox.warning(self.parent(), _("Printing Error"),
                    _("Could not send the document to the printer."))


def getPopplerBackends():
    """Return a two-tuple (renderBackend, printRenderBackend) from the prefs."""
    if QSettings().value("musicview/arthurbackend", False, bool):
        renderBackend = popplerqt5.Poppler.Document.ArthurBackend
    else:
        renderBackend = popplerqt5.Poppler.Document.SplashBackend
    if QSettings().value("musicview/arthurbackend_print", True, bool):
        printRenderBackend = popplerqt5.Poppler.Document.ArthurBackend
    else:
        printRenderBackend = popplerqt5.Poppler.Document.SplashBackend
    return renderBackend, printRenderBackend


def getRenderer(rendertype):
    """Factory to create a renderer with the paper color adjusted to the prefs.

    Currently, the rendertype can be "pdf", "svg", "image" or "diff".

    For the PDF type, the render backends are also read from the prefs.
    For image types, the paper color is not used. For diff types, the paper-
    color is not set.

    """
    if rendertype == "pdf":
        if popplerqt5:
            import qpageview.poppler
            r = qpageview.poppler.PopplerRenderer()
            r.renderBackend, r.printRenderBackend = getPopplerBackends()
        else:
            return None
    elif rendertype == "svg":
        import qpageview.svg
        r = qpageview.svg.SvgRenderer()
    elif rendertype == "image":
        import qpageview.image
        r = qpageview.image.ImageRenderer()
    elif rendertype == "diff":
        import qpageview.diff
        return qpageview.diff.DiffRenderer()
    else:
        raise ValueError("unknown render type")
    r.paperColor = textformats.formatData('editor').baseColors['paper']
    return r


def loadPdf(filename):
    """Like qpageview.loadPdf(), but uses a preconfigured renderer."""
    return qpageview.loadPdf(filename, getRenderer("pdf"))


def loadSvgs(filenames):
    """Like qpageview.loadSvgs(), but uses a preconfigured renderer."""
    return qpageview.loadSvgs(filenames, getRenderer("svg"))


def loadImages(filenames):
    """Like qpageview.loadImages(), but uses a preconfigured renderer."""
    return qpageview.loadImages(filenames, getRenderer("image"))


