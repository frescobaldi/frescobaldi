# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
The PDF preview panel.

This file loads even if popplerqt5 is absent, although the PDF preview
panel only shows a message about missing the popplerqt5 module.

The widget module contains the real widget, the documents module a simple
abstraction and caching of Poppler documents with their filename,
and the printing module contains code to print a Poppler document, either
via a PostScript rendering or by printing raster images to a QPrinter.

All the point & click stuff is handled in the pointandclick module.

"""


import functools
import os
import weakref

from PyQt5.QtCore import QSettings, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence, QPalette
from PyQt5.QtWidgets import (
    QAction, QActionGroup, QApplication, QComboBox, QLabel, QSpinBox,
    QWidgetAction)

import app
import actioncollection
import actioncollectionmanager
import icons
import qutil
import panel
import listmodel
import gadgets.drag
import jobattributes

from . import documents


# default zoom percentages
_zoomvalues = [50, 75, 100, 125, 150, 175, 200, 250, 300]

# viewModes from qpopplerview:
from qpopplerview import FixedScale, FitWidth, FitHeight, FitBoth


def activate(func):
    """Decorator for MusicViewPanel methods/slots.

    The purpose is to first activate the widget and only perform an action
    when the event loop starts. This gives the PDF widget the chance to resize
    and position itself correctly.

    """
    @functools.wraps(func)
    def wrapper(self):
        instantiated = bool(super(panel.Panel, self).widget())
        self.activate()
        if instantiated:
            func(self)
        else:
            QTimer.singleShot(0, lambda: func(self))
    return wrapper


class MusicViewPanel(panel.Panel):
    def __init__(self, mainwindow):
        super(MusicViewPanel, self).__init__(mainwindow)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+M"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)

        ac = self.actionCollection = Actions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.music_print.triggered.connect(self.printMusic)
        ac.music_zoom_in.triggered.connect(self.zoomIn)
        ac.music_zoom_out.triggered.connect(self.zoomOut)
        ac.music_zoom_original.triggered.connect(self.zoomOriginal)
        ac.music_zoom_combo.zoomChanged.connect(self.slotZoomChanged)
        ac.music_fit_width.triggered.connect(self.fitWidth)
        ac.music_fit_height.triggered.connect(self.fitHeight)
        ac.music_fit_both.triggered.connect(self.fitBoth)
        ac.music_single_pages.triggered.connect(self.viewSinglePages)
        ac.music_two_pages_first_right.triggered.connect(self.viewTwoPagesFirstRight)
        ac.music_two_pages_first_left.triggered.connect(self.viewTwoPagesFirstLeft)
        ac.music_maximize.triggered.connect(self.maximize)
        ac.music_jump_to_cursor.triggered.connect(self.jumpToCursor)
        ac.music_sync_cursor.triggered.connect(self.toggleSyncCursor)
        ac.music_copy_image.triggered.connect(self.copyImage)
        ac.music_copy_text.triggered.connect(self.copyText)
        ac.music_document_select.documentsChanged.connect(self.updateActions)
        ac.music_copy_image.setEnabled(False)
        ac.music_next_page.triggered.connect(self.slotNextPage)
        ac.music_prev_page.triggered.connect(self.slotPreviousPage)
        self.slotPageCountChanged(0)
        ac.music_next_page.setEnabled(False)
        ac.music_prev_page.setEnabled(False)
        ac.music_single_pages.setChecked(True) # default to single pages
        ac.music_reload.triggered.connect(self.reloadView)
        self.actionCollection.music_sync_cursor.setChecked(
            QSettings().value("musicview/sync_cursor", False, bool))

        mode = QSettings().value("muziekview/layoutmode", "single", str)
        if mode == "double_left":
            ac.music_two_pages_first_left.setChecked(True)
        elif mode == "double_right":
            ac.music_two_pages_first_right.setChecked(True)
        else: # mode == "single":
            ac.music_single_pages.setChecked(True)

    def translateUI(self):
        self.setWindowTitle(_("window title", "Music View"))
        self.toggleViewAction().setText(_("&Music View"))

    def createWidget(self):
        from . import widget
        w = widget.MusicView(self)
        w.zoomChanged.connect(self.slotMusicZoomChanged)
        w.updateZoomInfo()
        w.view.surface().selectionChanged.connect(self.updateSelection)

        # read layout mode setting before using the widget
        layout = w.view.surface().pageLayout()
        if self.actionCollection.music_two_pages_first_right.isChecked():
            layout.setPagesPerRow(2)
            layout.setPagesFirstRow(1)
        elif self.actionCollection.music_two_pages_first_left.isChecked():
            layout.setPagesPerRow(2)
            layout.setPagesFirstRow(0)
        else: # "single"
            layout.setPagesPerRow(1)   # default to single
            layout.setPagesFirstRow(0) # pages

        import qpopplerview.pager
        self._pager = p = qpopplerview.pager.Pager(w.view)
        p.pageCountChanged.connect(self.slotPageCountChanged)
        p.currentPageChanged.connect(self.slotCurrentPageChanged)
        app.languageChanged.connect(self.updatePagerLanguage)

        selector = self.actionCollection.music_document_select
        selector.currentDocumentChanged.connect(w.openDocument)
        selector.documentClosed.connect(w.clear)

        if selector.currentDocument():
            # open a document only after the widget has been created;
            # this prevents many superfluous resizes
            def open():
                if selector.currentDocument():
                    w.openDocument(selector.currentDocument())
            QTimer.singleShot(0, open)
        return w

    def setPageLayoutMode(self, mode):
        """Change the page layout and store the setting as well.

        The mode is "single", "double_left" or "double_right".

        "single": a vertical row of single pages
        "double_left": two pages besides each other, first page is a left page
        "double_right": two pages, first page is a right page.

        """
        layout = self.widget().view.surface().pageLayout()
        if mode == "double_right":
            layout.setPagesPerRow(2)
            layout.setPagesFirstRow(1)
        elif mode == "double_left":
            layout.setPagesPerRow(2)
            layout.setPagesFirstRow(0)
        elif mode == "single":
            layout.setPagesPerRow(1)
            layout.setPagesFirstRow(0)
        else:
            raise ValueError("wrong mode value")
        QSettings().setValue("muziekview/layoutmode", mode)
        layout.update()

    def updateSelection(self, rect):
        self.actionCollection.music_copy_image.setEnabled(bool(rect))
        self.actionCollection.music_copy_text.setEnabled(bool(rect))

    def updatePagerLanguage(self):
        self.actionCollection.music_pager.setPageCount(self._pager.pageCount())

    def slotPageCountChanged(self, total):
        self.actionCollection.music_pager.setPageCount(total)

    def slotCurrentPageChanged(self, num):
        self.actionCollection.music_pager.setCurrentPage(num)
        self.actionCollection.music_next_page.setEnabled(num < self._pager.pageCount())
        self.actionCollection.music_prev_page.setEnabled(num > 1)

    @activate
    def slotNextPage(self):
        self._pager.setCurrentPage(self._pager.currentPage() + 1)

    @activate
    def slotPreviousPage(self):
        self._pager.setCurrentPage(self._pager.currentPage() - 1)

    def setCurrentPage(self, num):
        self.activate()
        self._pager.setCurrentPage(num)

    def updateActions(self):
        ac = self.actionCollection
        ac.music_print.setEnabled(bool(ac.music_document_select.documents()))

    def printMusic(self):
        doc = self.actionCollection.music_document_select.currentDocument()
        if doc and doc.document():
            ### temporarily disable printing on Mac OS X
            import sys
            if sys.platform.startswith('darwin'):
                from PyQt5.QtCore import QUrl
                from PyQt5.QtGui import QMessageBox
                result =  QMessageBox.warning(self.mainwindow(),
                    _("Print Music"), _(
                    "Unfortunately, this version of Frescobaldi is unable to print "
                    "PDF documents on Mac OS X due to various technical reasons.\n\n"
                    "Do you want to open the file in the default viewer for printing instead? "
                    "(remember to close it again to avoid access problems)\n\n"
                    "Choose Yes if you want that, No if you want to try the built-in "
                    "printing functionality anyway, or Cancel to cancel printing."),
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                if result == QMessageBox.Yes:
                    import helpers
                    helpers.openUrl(QUrl.fromLocalFile(doc.filename()), "pdf")
                    return
                elif result == QMessageBox.Cancel:
                    return
            ### end temporarily disable printing on Mac OS X
            import popplerprint
            popplerprint.printDocument(doc, self)

    @activate
    def zoomIn(self):
        self.widget().view.zoomIn()

    @activate
    def zoomOut(self):
        self.widget().view.zoomOut()

    @activate
    def zoomOriginal(self):
        self.widget().view.zoom(1.0)

    @activate
    def fitWidth(self):
        self.widget().view.setViewMode(FitWidth)

    @activate
    def fitHeight(self):
        self.widget().view.setViewMode(FitHeight)

    @activate
    def fitBoth(self):
        self.widget().view.setViewMode(FitBoth)

    @activate
    def viewSinglePages(self):
        self.setPageLayoutMode("single")

    @activate
    def viewTwoPagesFirstRight(self):
        self.setPageLayoutMode("double_right")

    @activate
    def viewTwoPagesFirstLeft(self):
        self.setPageLayoutMode("double_left")

    @activate
    def jumpToCursor(self):
        self.widget().showCurrentLinks()

    @activate
    def reloadView(self):
        d = self.mainwindow().currentDocument()
        group = documents.group(d)
        if group.update() or group.update(False):
            ac = self.actionCollection
            ac.music_document_select.setCurrentDocument(d)

    def toggleSyncCursor(self):
        QSettings().setValue("musicview/sync_cursor",
            self.actionCollection.music_sync_cursor.isChecked())

    def copyImage(self):
        page = self.widget().view.surface().selectedPage()
        if not page:
            return
        rect = self.widget().view.surface().selectedPageRect(page)
        import copy2image
        copy2image.copy_image(self, page, rect, documents.filename(page.document()))

    def copyText(self):
        text = self.widget().view.surface().selectedText()
        if text:
            QApplication.clipboard().setText(text)

    def slotZoomChanged(self, mode, scale):
        """Called when the combobox is changed, changes view zoom."""
        self.activate()
        if mode == FixedScale:
            self.widget().view.zoom(scale)
        else:
            self.widget().view.setViewMode(mode)

    def slotMusicZoomChanged(self, mode, scale):
        """Called when the music view is changed, updates the toolbar actions."""
        ac = self.actionCollection
        ac.music_fit_width.setChecked(mode == FitWidth)
        ac.music_fit_height.setChecked(mode == FitHeight)
        ac.music_fit_both.setChecked(mode == FitBoth)
        ac.music_zoom_combo.updateZoomInfo(mode, scale)


class Actions(actioncollection.ActionCollection):
    name = "musicview"
    def createActions(self, panel):
        self.music_document_select = DocumentChooserAction(panel)
        self.music_print = QAction(panel)
        self.music_zoom_in = QAction(panel)
        self.music_zoom_out = QAction(panel)
        self.music_zoom_original = QAction(panel)
        self.music_zoom_combo = ZoomerAction(panel)
        self.music_fit_width = QAction(panel, checkable=True)
        self.music_fit_height = QAction(panel, checkable=True)
        self.music_fit_both = QAction(panel, checkable=True)
        self._column_mode = ag = QActionGroup(panel)
        self.music_single_pages = QAction(ag, checkable=True)
        self.music_two_pages_first_right = QAction(ag, checkable=True)
        self.music_two_pages_first_left = QAction(ag, checkable=True)
        self.music_maximize = QAction(panel)
        self.music_jump_to_cursor = QAction(panel)
        self.music_sync_cursor = QAction(panel, checkable=True)
        self.music_copy_image = QAction(panel)
        self.music_copy_text = QAction(panel)
        self.music_pager = PagerAction(panel)
        self.music_next_page = QAction(panel)
        self.music_prev_page = QAction(panel)
        self.music_reload = QAction(panel)

        self.music_print.setIcon(icons.get('document-print'))
        self.music_zoom_in.setIcon(icons.get('zoom-in'))
        self.music_zoom_out.setIcon(icons.get('zoom-out'))
        self.music_zoom_original.setIcon(icons.get('zoom-original'))
        self.music_fit_width.setIcon(icons.get('zoom-fit-width'))
        self.music_fit_height.setIcon(icons.get('zoom-fit-height'))
        self.music_fit_both.setIcon(icons.get('zoom-fit-best'))
        self.music_maximize.setIcon(icons.get('view-fullscreen'))
        self.music_jump_to_cursor.setIcon(icons.get('go-jump'))
        self.music_copy_image.setIcon(icons.get('edit-copy'))
        self.music_copy_text.setIcon(icons.get('edit-copy'))
        self.music_next_page.setIcon(icons.get('go-next'))
        self.music_prev_page.setIcon(icons.get('go-previous'))

        self.music_document_select.setShortcut(QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_O))
        self.music_print.setShortcuts(QKeySequence.Print)
        self.music_zoom_in.setShortcuts(QKeySequence.ZoomIn)
        self.music_zoom_out.setShortcuts(QKeySequence.ZoomOut)
        self.music_jump_to_cursor.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_J))
        self.music_copy_image.setShortcut(QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_C))
        self.music_reload.setShortcut(QKeySequence(Qt.Key_F5))

    def translateUI(self):
        self.music_document_select.setText(_("Select Music View Document"))
        self.music_print.setText(_("&Print Music..."))
        self.music_zoom_in.setText(_("Zoom &In"))
        self.music_zoom_out.setText(_("Zoom &Out"))
        self.music_zoom_original.setText(_("Original &Size"))
        self.music_zoom_combo.setText(_("Zoom Music"))
        self.music_fit_width.setText(_("Fit &Width"))
        self.music_fit_height.setText(_("Fit &Height"))
        self.music_fit_both.setText(_("Fit &Page"))
        self.music_single_pages.setText(_("Single Pages"))
        self.music_two_pages_first_right.setText(_("Two Pages (first page right)"))
        self.music_two_pages_first_left.setText(_("Two Pages (first page left)"))
        self.music_maximize.setText(_("&Maximize"))
        self.music_jump_to_cursor.setText(_("&Jump to Cursor Position"))
        self.music_sync_cursor.setText(_("S&ynchronize with Cursor Position"))
        self.music_copy_image.setText(_("Copy to &Image..."))
        self.music_copy_text.setText(_("Copy Selected &Text"))
        self.music_next_page.setText(_("Next Page"))
        self.music_next_page.setIconText(_("Next"))
        self.music_prev_page.setText(_("Previous Page"))
        self.music_prev_page.setIconText(_("Previous"))
        self.music_reload.setText(_("&Reload"))


class ComboBoxAction(QWidgetAction):
    """A widget action that opens a combobox widget popup when triggered."""
    def __init__(self, panel):
        super(ComboBoxAction, self).__init__(panel)
        self.triggered.connect(self.showPopup)

    def showPopup(self):
        """Called when our action is triggered by a keyboard shortcut."""
        # find the widget in our floating panel, if available there
        for w in self.createdWidgets():
            if w.window() == self.parent():
                w.showPopup()
                return
        # find the one in the main window
        for w in self.createdWidgets():
            if w.window() == self.parent().mainwindow():
                w.showPopup()
                return


class DocumentChooserAction(ComboBoxAction):
    """A ComboBoxAction that keeps track of the current text document.

    It manages the list of generated PDF documents for every text document.
    If the mainwindow changes its current document and there are PDFs to display,
    it switches the current document.

    It also switches to a text document if a job finished for that document,
    and it generated new PDF documents.

    """

    documentClosed = pyqtSignal()
    documentsChanged = pyqtSignal()
    currentDocumentChanged = pyqtSignal(documents.Document)

    def __init__(self, panel):
        super(DocumentChooserAction, self).__init__(panel)
        self._model = None
        self._document = None
        self._documents = []
        self._currentIndex = -1
        self._indices = weakref.WeakKeyDictionary()
        panel.mainwindow().currentDocumentChanged.connect(self.slotDocumentChanged)
        documents.documentUpdated.connect(self.slotDocumentUpdated)

    def createWidget(self, parent):
        w = DocumentChooser(parent)
        w.activated[int].connect(self.setCurrentIndex)
        if self._model:
            w.setModel(self._model)
        return w

    def slotDocumentChanged(self, doc):
        """Called when the mainwindow changes its current document."""
        # only switch our document if there are PDF documents to display
        if self._document is None or documents.group(doc).documents():
            self.setCurrentDocument(doc)

    def slotDocumentUpdated(self, doc, job):
        """Called when a Job, finished on the document, has created new PDFs."""
        # if result files of this document were already displayed, the display
        # is updated. Else the current document is switched if the document was
        # the current document to be engraved (e.g. sticky or master) and the
        # the job was started on this mainwindow
        import engrave
        mainwindow = self.parent().mainwindow()
        if (doc == self._document or
            (jobattributes.get(job).mainwindow == mainwindow and
             doc == engrave.engraver(mainwindow).document())):
            self.setCurrentDocument(doc)

    def setCurrentDocument(self, document):
        """Displays the DocumentGroup of the given text Document in our chooser."""
        prev = self._document
        self._document = document
        if prev:
            prev.loaded.disconnect(self.updateDocument)
            prev.closed.disconnect(self.closeDocument)
            self._indices[prev] = self._currentIndex
        document.loaded.connect(self.updateDocument)
        document.closed.connect(self.closeDocument)
        self.updateDocument()

    def updateDocument(self):
        """(Re)read the output documents of the current document and show them."""
        docs = self._documents = documents.group(self._document).documents()
        self.setVisible(bool(docs))
        self.setEnabled(bool(docs))

        # make model for the docs
        m = self._model = listmodel.ListModel([d.filename() for d in docs],
            display = os.path.basename, icon = icons.file_type)
        m.setRoleFunction(Qt.UserRole, lambda f: f)
        for w in self.createdWidgets():
            w.setModel(m)

        index = self._indices.get(self._document, 0)
        if index < 0 or index >= len(docs):
            index = 0
        self.documentsChanged.emit()
        self.setCurrentIndex(index)

    def closeDocument(self):
        """Called when the current document is closed by the user."""
        self._document = None
        self._documents = []
        self._currentIndex = -1
        self.setVisible(False)
        self.setEnabled(False)
        self.documentClosed.emit()
        self.documentsChanged.emit()

    def documents(self):
        return self._documents

    def setCurrentIndex(self, index):
        if self._documents:
            self._currentIndex = index
            p = QApplication.palette()
            if not self._documents[index].updated:
                color = qutil.mixcolor(QColor(Qt.red), p.color(QPalette.Base), 0.3)
                p.setColor(QPalette.Base, color)
            for w in self.createdWidgets():
                w.setCurrentIndex(index)
                w.setPalette(p)
            self.currentDocumentChanged.emit(self._documents[index])

    def currentIndex(self):
        return self._currentIndex

    def currentDocument(self):
        """Returns the currently selected Music document (Note: NOT the text document!)"""
        if self._documents:
            return self._documents[self._currentIndex]


class DocumentChooser(QComboBox):
    def __init__(self, parent):
        super(DocumentChooser, self).__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.setFocusPolicy(Qt.NoFocus)
        app.translateUI(self)
        gadgets.drag.ComboDrag(self).role = Qt.UserRole

    def translateUI(self):
        self.setToolTip(_("Choose the PDF document to display."))
        self.setWhatsThis(_(
            "Choose the PDF document to display or drag the file "
            "to another application or location."))


class ZoomerAction(ComboBoxAction):
    zoomChanged = pyqtSignal(int, float)

    def createWidget(self, parent):
        return Zoomer(self, parent)

    def setCurrentIndex(self, index):
        """Called when a user manipulates a Zoomer combobox.

        Updates the other widgets and calls the corresponding method of the panel.

        """
        for w in self.createdWidgets():
            w.setCurrentIndex(index)
        if index == 0:
            self.zoomChanged.emit(FitWidth, 0)
        elif index == 1:
            self.zoomChanged.emit(FitHeight, 0)
        elif index == 2:
            self.zoomChanged.emit(FitBoth, 0)
        else:
            self.zoomChanged.emit(FixedScale, _zoomvalues[index-3] / 100.0)

    def updateZoomInfo(self, mode, scale):
        """Connect view.viewModeChanged and layout.scaleChanged to this."""
        if mode == FixedScale:
            text = "{0:.0%}".format(scale)
            for w in self.createdWidgets():
                w.setEditText(text)
        else:
            if mode == FitWidth:
                index = 0
            elif mode == FitHeight:
                index = 1
            else: # qpopplerview.FitBoth:
                index = 2
            for w in self.createdWidgets():
                w.setCurrentIndex(index)


class Zoomer(QComboBox):
    def __init__(self, action, parent):
        super(Zoomer, self).__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.activated[int].connect(action.setCurrentIndex)
        self.addItems(['']*3)
        self.addItems(list(map("{0}%".format, _zoomvalues)))
        self.setMaxVisibleItems(20)
        app.translateUI(self)

    def translateUI(self):
        self.setItemText(0, _("Fit Width"))
        self.setItemText(1, _("Fit Height"))
        self.setItemText(2, _("Fit Page"))


class PagerAction(QWidgetAction):
    def __init__(self, panel):
        super(PagerAction, self).__init__(panel)

    def createWidget(self, parent):
        w = QSpinBox(parent, buttonSymbols=QSpinBox.NoButtons)
        w.setFocusPolicy(Qt.ClickFocus)
        w.valueChanged[int].connect(self.slotValueChanged)
        return w

    def setPageCount(self, total):
        if total:
            self.setVisible(True)
            # L10N: page numbering: page {num} of {total}
            prefix, suffix = _("{num} of {total}").split('{num}')
            def adjust(w):
                w.setRange(1, total)
                w.setSuffix(suffix.format(total=total))
                w.setPrefix(prefix.format(total=total))
        else:
            self.setVisible(False)
            def adjust(w):
                w.setRange(0, 0)
                w.clear()
        for w in self.createdWidgets():
            with qutil.signalsBlocked(w):
                adjust(w)

    def setCurrentPage(self, num):
        if num:
            for w in self.createdWidgets():
                with qutil.signalsBlocked(w):
                    w.setValue(num)
                    w.lineEdit().deselect()

    def slotValueChanged(self, num):
        self.parent().setCurrentPage(num)


