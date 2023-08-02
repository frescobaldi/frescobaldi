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
import platform

from PyQt5.QtCore import pyqtSignal, QMargins, QSettings, Qt
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

try:
    import popplerqt5
except ImportError:
    popplerqt5 = None

import app
import icons
import textformats
import qpageview
import qpageview.view
import qpageview.layout
import qpageview.printing
import qpageview.magnifier
import qpageview.viewactions
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


class PagedView(qpageview.widgetoverlay.WidgetOverlayViewMixin, qpageview.View):
    """A View based on qpageview.View.

    This View has additional features and customisation needed in Frescobaldi.

    """


    def __init__(self, parent=None):
        super().__init__(parent)
        self._printer = None
        self.documentPropertyStore = qpageview.view.DocumentPropertyStore()
        self.setMagnifier(Magnifier())
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        # strict paging with pageup/pagedown
        self.strictPagingEnabled = QSettings().value("musicview/strict_paging", False, bool)

        # shadow/margin
        shadow = QSettings().value("musicview/shadow", True, bool)
        oldshadow, self.dropShadowEnabled = self.dropShadowEnabled, shadow
        self.pageLayout().setMargins(QMargins(6, 6, 6, 6) if shadow else QMargins(1, 1, 1, 1))
        changed = shadow != oldshadow

        # kinetic scrolling
        kinetic = QSettings().value("musicview/kinetic_scrolling", True, bool)
        self.kineticPagingEnabled = kinetic
        self.kineticScrollingEnabled = kinetic

        # scrollbar visibility
        scrollbars = QSettings().value("musicview/show_scrollbars", True, bool)
        policy = Qt.ScrollBarAsNeeded if scrollbars else Qt.ScrollBarAlwaysOff
        oldpolicy = self.horizontalScrollBarPolicy()
        self.setHorizontalScrollBarPolicy(policy)
        self.setVerticalScrollBarPolicy(policy)
        if policy != oldpolicy:
            changed = True

        if not self.pageCount():
            return

        # if margin or scrollbar visibility was changed, relayout
        if changed:
            if self._viewMode:
                self.fitPageLayout()
            self.updatePageLayout()


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
        if renderers and popplerqt5:
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
        # on Mac, when printing directly with cups, the system print window is shown
        # but its settings are ignored and any choice (including opening the PDF)
        # results in printing to cups' default printer
        if (s.value("printing/directcups",
                    False if platform.system() == "Darwin" else True, bool)
            and isinstance(self.document(), qpageview.poppler.PopplerDocument)
            and os.path.isfile(self.document().filename())
            and not printer.outputFileName()):
            h = qpageview.cupsprinter.handle(printer)
            if h:
                if not h.printFile(self.document().filename()):
                    QMessageBox.warning(self,
                        _("Printing Error"),
                        "{0}\n{1}".format(
                            _("An error occurred (code: {num}):").format(num=h.status),
                            h.error))
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


class ViewActions(qpageview.viewactions.ViewActions):
    """View actions with translated texts and icons."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app.translateUI(self)

    def translateUI(self):
        """Translate our actions correctly."""
        self.setActionTexts(_)
        self.pager.setDisplayFormat(_("{num} of {total}"))

    def setActionIcons(self):
        """Set icons to our actions."""
        self.print.setIcon(icons.get('document-print'))
        self.zoom_in.setIcon(icons.get('zoom-in'))
        self.zoom_out.setIcon(icons.get('zoom-out'))
        self.zoom_original.setIcon(icons.get('zoom-original'))
        self.fit_width.setIcon(icons.get('zoom-fit-width'))
        self.fit_height.setIcon(icons.get('zoom-fit-height'))
        self.fit_both.setIcon(icons.get('zoom-fit-best'))
        self.rotate_left.setIcon(icons.get('rotate-left'))
        self.rotate_right.setIcon(icons.get('rotate-right'))
        self.next_page.setIcon(icons.get('go-next'))
        self.previous_page.setIcon(icons.get('go-previous'))
        self.magnifier.setIcon(icons.get('zoom-magnifier'))
        self.reload.setIcon(icons.get('view-refresh'))


def getPopplerBackends():
    """Return a two-tuple (renderBackend, printRenderBackend) from the prefs."""
    if QSettings().value("musicview/arthurbackend", False, bool):
        renderBackend = popplerqt5.Poppler.Document.ArthurBackend
    else:
        renderBackend = popplerqt5.Poppler.Document.SplashBackend
    if QSettings().value("printing/arthurbackend_print", True, bool):
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
