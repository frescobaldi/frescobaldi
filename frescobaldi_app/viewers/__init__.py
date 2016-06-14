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

This is an abstract base class for different viewer modules.
"""


import functools
import os
import weakref

from PyQt5.QtCore import QSettings, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QKeySequence, QPalette
from PyQt5.QtWidgets import (
    QAction, QActionGroup, QApplication, QComboBox, QFileDialog, QLabel,
    QMessageBox, QSpinBox, QToolBar, QWidgetAction)

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

class AbstractViewPanel(panel.Panel):
    """Abstract base class for several viewer panels"""
    def __init__(self, mainwindow):
        super(AbstractViewPanel, self).__init__(mainwindow)
        self.hide()
        ac = self.actionCollection = self._createConcreteActions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        self.slotPageCountChanged(0)
        self.configureActions()
        self.connectActions()

    def configureActions(self):
        ac = self.actionCollection
        ac.viewer_copy_image.setEnabled(False)
        ac.viewer_next_page.setEnabled(False)
        ac.viewer_prev_page.setEnabled(False)
        ac.viewer_single_pages.setChecked(True) # default to single pages
        ac.viewer_sync_cursor.setChecked(False)
        sync_cursor = QSettings().value("{}/sync-cursor".format(self.viewerName()), False, bool)
        ac.viewer_sync_cursor.setChecked(sync_cursor)
        show_toolbar = QSettings().value("{}/show-toolbar".format(self.viewerName()), True, bool)
        ac.viewer_show_toolbar.setChecked(show_toolbar)

    def connectActions(self):
        ac = self.actionCollection
        ac.viewer_help.triggered.connect(self.slotShowHelp)
        ac.viewer_print.triggered.connect(self.printMusic)
        # Zooming actions
        ac.viewer_zoom_in.triggered.connect(self.zoomIn)
        ac.viewer_zoom_out.triggered.connect(self.zoomOut)
        ac.viewer_zoom_original.triggered.connect(self.zoomOriginal)
        ac.viewer_zoom_combo.zoomChanged.connect(self.slotZoomChanged)
        ac.viewer_fit_width.triggered.connect(self.fitWidth)
        ac.viewer_fit_height.triggered.connect(self.fitHeight)
        ac.viewer_fit_both.triggered.connect(self.fitBoth)
        # Page display actions
        ac.viewer_single_pages.triggered.connect(self.viewSinglePages)
        ac.viewer_two_pages_first_right.triggered.connect(self.viewTwoPagesFirstRight)
        ac.viewer_two_pages_first_left.triggered.connect(self.viewTwoPagesFirstLeft)
        ac.viewer_maximize.triggered.connect(self.maximize)
        # File handling actions
        ac.viewer_document_select.viewdocsChanged.connect(self.updateActions)
        ac.viewer_open.triggered.connect(self.openViewdocs)
        ac.viewer_close.triggered.connect(self.closeViewdoc)
        ac.viewer_close_other.triggered.connect(self.closeOtherViewdocs)
        ac.viewer_close_all.triggered.connect(self.closeAllViewdocs)
        ac.viewer_reload.triggered.connect(self.reloadView)
        ac.viewer_document_select.viewdocsMissing.connect(self.reportMissingViewdocs)
        # Navigation actions
        ac.viewer_next_page.triggered.connect(self.slotNextPage)
        ac.viewer_prev_page.triggered.connect(self.slotPreviousPage)
        ac.viewer_copy_image.triggered.connect(self.copyImage)
        # Miscellaneous actions
        ac.viewer_jump_to_cursor.triggered.connect(self.jumpToCursor)
        ac.viewer_sync_cursor.triggered.connect(self.toggleSyncCursor)
        ac.viewer_show_toolbar.triggered.connect(self.slotShowToolbar)
        self.mainwindow().allDocumentsClosed.connect(self.closeAllViewdocs)

    def _createConreteActions(self):
        """Create the actionCollection.
        Subclasses must override this method."""
        raise NotImplementedError()

    def _createConcreteWidget(self):
        """Create the Widget for the panel. Subclasses should override
        this to instantiatethe appropriate class."""
        raise NotImplementedError()

    def createWidget(self):
        """Creates and configures the widget for the panel."""

        w = self._createConcreteWidget()

        w.zoomChanged.connect(self.slotViewerZoomChanged)
        w.updateZoomInfo()
        w.view.surface().selectionChanged.connect(self.updateSelection)
        w.view.surface().pageLayout().setPagesPerRow(1)   # default to single
        w.view.surface().pageLayout().setPagesFirstRow(0) # pages

        import qpopplerview.pager
        self._pager = p = qpopplerview.pager.Pager(w.view)
        p.pageCountChanged.connect(self.slotPageCountChanged)
        p.currentPageChanged.connect(self.slotCurrentPageChanged)
        app.languageChanged.connect(self.updatePagerLanguage)

        selector = self.actionCollection.viewer_document_select
        selector.currentViewdocChanged.connect(w.openViewdoc)
        selector.viewdocClosed.connect(w.clear)

        if selector.currentViewdoc():
            # open a document only after the widget has been created;
            # this prevents many superfluous resizes
            def open():
                if selector.currentViewdoc():
                    w.openViewdoc(selector.currentViewdoc())
            QTimer.singleShot(0, open)

        return w

    def viewerName(self):
        """Returns the 'name' of the viewer panel.
        This is the lowercase classname, right-stripped
        of a trailing 'panel'.
        To be used for accessing the QSettings group."""
        if not hasattr(self, '_viewerName'):
            name = type(self).__name__.lower()
            self._viewerName = name if not name.endswith('panel') else name[:-5]
        return self._viewerName

    def viewerPanelDisplayName(self):
        """Returns the 'display name' of the current viewer."""
        return self.toggleViewAction().text()

    def updateSelection(self, rect):
        """Called when the selection has changed.
        Update copy-image action according to selection state."""
        self.actionCollection.viewer_copy_image.setEnabled(bool(rect))

    def updatePagerLanguage(self):
        """Called when the application lanugage has changed.
        Update the pager to implicitly update the language."""
        self.actionCollection.viewer_pager.setPageCount(self._pager.pageCount())

    def slotPageCountChanged(self, total):
        self.actionCollection.viewer_pager.setPageCount(total)

    def slotCurrentPageChanged(self, num):
        self.actionCollection.viewer_pager.setCurrentPage(num)
        self.actionCollection.viewer_next_page.setEnabled(num < self._pager.pageCount())
        self.actionCollection.viewer_prev_page.setEnabled(num > 1)

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
        ac.viewer_print.setEnabled(bool(ac.viewer_document_select.viewdocs()))

    def printMusic(self):
        doc = self.actionCollection.viewer_document_select.currentViewdoc()
        if doc and doc.document():
            ### temporarily disable printing on Mac OS X
            import sys
            if sys.platform.startswith('darwin'):
                from PyQt5.QtCore import QUrl
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
        layout = self.widget().view.surface().pageLayout()
        layout.setPagesPerRow(1)
        layout.setPagesFirstRow(0)
        layout.update()

    @activate
    def viewTwoPagesFirstRight(self):
        layout = self.widget().view.surface().pageLayout()
        layout.setPagesPerRow(2)
        layout.setPagesFirstRow(1)
        layout.update()

    @activate
    def viewTwoPagesFirstLeft(self):
        layout = self.widget().view.surface().pageLayout()
        layout.setPagesPerRow(2)
        layout.setPagesFirstRow(0)
        layout.update()

    @activate
    def jumpToCursor(self):
        self.widget().showCurrentLinks()

    @activate
    def reloadView(self):
        d = self.mainwindow().currentDocument()
        group = documents.group(d)
        if group.update() or group.update(False):
            ac = self.actionCollection
            ac.viewer_document_select.setCurrentViewdoc(d)

    def toggleSyncCursor(self):
        checked = self.actionCollection.viewer_sync_cursor.isChecked()
        QSettings().setValue("{}/sync-cursor".format(self.viewerName()), checked)

    def slotShowToolbar(self):
        """Sets the visibility of the viewer's toolbar and saves it to
        the application settings."""
        checked = self.actionCollection.viewer_show_toolbar.isChecked()
        self.widget().toolbar().setVisible(checked)
        QSettings().setValue("{}/show-toolbar".format(self.viewerName()), checked)

    def slotShowHelp(self):
        import userguide
        userguide.show(self.viewerName())

    def copyImage(self):
        page = self.widget().view.surface().selectedPage()
        if not page:
            return
        rect = self.widget().view.surface().selectedPageRect(page)
        import copy2image
        copy2image.copy_image(self, page, rect, documents.filename(page.document()))

    def slotZoomChanged(self, mode, scale):
        """Called when the combobox is changed, changes view zoom."""
        self.activate()
        if mode == FixedScale:
            self.widget().view.zoom(scale)
        else:
            self.widget().view.setViewMode(mode)

    def slotViewerZoomChanged(self, mode, scale):
        """Called when the music view is changed, updates the toolbar actions."""
        ac = self.actionCollection
        ac.viewer_fit_width.setChecked(mode == FitWidth)
        ac.viewer_fit_height.setChecked(mode == FitHeight)
        ac.viewer_fit_both.setChecked(mode == FitBoth)
        ac.viewer_zoom_combo.updateZoomInfo(mode, scale)

    def slotShowViewdoc(self):
        """Bring the document to front that was selected from the context menu"""
        doc_filename = self.sender().checkedAction()._document_filename
        self.actionCollection.viewer_document_select.setActiveViewdoc(doc_filename)

    def _openViewdocsCaption(self):
        """Returns the caption for the file open dialog."""
        raise NotImplementedError('Method _openViewdocsCaption has to be implemented in {}'.format(self.viewerName()))

    def openViewdocs(self):
        """ Displays an open dialog to open music document(s). """
        caption = self._openViewdocsCaption()
        current_viewer_doc = self.widget().currentViewdoc()
        current_filename = current_viewer_doc.filename() if current_viewer_doc else None
        current_editor_document = self.mainwindow().currentDocument().url().toLocalFile()
        directory = os.path.dirname(current_filename or current_editor_document or app.basedir())
        filenames = QFileDialog().getOpenFileNames(self, caption, directory, '*.pdf',)[0]
        if filenames:
            # TODO: This has to be generalized too
            self.actionCollection.viewer_document_select.loadFiles(filenames)

    def closeViewdoc(self):
        """ Close current music document. """
        mds = self.actionCollection.viewer_document_select
        mds.removeViewdoc(self.widget().currentViewdoc())
        if len(mds.viewdocs()) == 0:
            self.widget().clear()

    def closeOtherViewdocs(self):
        """Close all viewer documents except the one currently opened"""
        mds = self.actionCollection.viewer_document_select
        mds.removeOtherViewdocs(self.widget().currentViewdoc())

    def closeAllViewdocs(self):
        """Close all opened viewer documents"""
        mds = self.actionCollection.viewer_document_select
        mds.removeAllViewdocs()
        self.widget().clear()

    def reportMissingViewdocs(self, missing):
        """Report missing viewer document files when restoring a session."""
        report_msg = _(
            "The following file is missing and could not be loaded "
            "when restoring a session:",
            "The following files are missing and could not be loaded "
            "when restoring a session:",
            len(missing))
        QMessageBox.warning(self, _("Missing files in {name}").format(name=self.viewerPanelDisplayName()),
                                    report_msg + '\n\n' + '\n'.join(missing))


class ViewerActions(actioncollection.ActionCollection):
    name = "abstractviewpanel"
    def createActions(self, panel):
        self.viewer_help = QAction(panel)
        self.viewer_document_select = self._createViewdocChooserAction(panel)
        self.viewer_print = QAction(panel)
        self.viewer_zoom_in = QAction(panel)
        self.viewer_zoom_out = QAction(panel)
        self.viewer_zoom_original = QAction(panel)
        self.viewer_zoom_combo = ZoomerAction(panel)
        self.viewer_fit_width = QAction(panel, checkable=True)
        self.viewer_fit_height = QAction(panel, checkable=True)
        self.viewer_fit_both = QAction(panel, checkable=True)
        self._column_mode = ag = QActionGroup(panel)
        self.viewer_single_pages = QAction(ag, checkable=True)
        self.viewer_two_pages_first_right = QAction(ag, checkable=True)
        self.viewer_two_pages_first_left = QAction(ag, checkable=True)
        self.viewer_maximize = QAction(panel)
        self.viewer_jump_to_cursor = QAction(panel)
        self.viewer_sync_cursor = QAction(panel, checkable=True)
        self.viewer_copy_image = QAction(panel)
        self.viewer_pager = PagerAction(panel)
        self.viewer_next_page = QAction(panel)
        self.viewer_prev_page = QAction(panel)
        self.viewer_reload = QAction(panel)
        self.viewer_show_toolbar = QAction(panel, checkable=True)
        self.viewer_open = QAction(panel)
        self.viewer_close = QAction(panel)
        self.viewer_close_other = QAction(panel)
        self.viewer_close_all = QAction(panel)

        self.viewer_help.setIcon(icons.get('help-contents'))
        self.viewer_print.setIcon(icons.get('document-print'))
        self.viewer_zoom_in.setIcon(icons.get('zoom-in'))
        self.viewer_zoom_out.setIcon(icons.get('zoom-out'))
        self.viewer_zoom_original.setIcon(icons.get('zoom-original'))
        self.viewer_fit_width.setIcon(icons.get('zoom-fit-width'))
        self.viewer_fit_height.setIcon(icons.get('zoom-fit-height'))
        self.viewer_fit_both.setIcon(icons.get('zoom-fit-best'))
        self.viewer_maximize.setIcon(icons.get('view-fullscreen'))
        self.viewer_jump_to_cursor.setIcon(icons.get('go-jump'))
        self.viewer_copy_image.setIcon(icons.get('edit-copy'))
        self.viewer_next_page.setIcon(icons.get('go-next'))
        self.viewer_prev_page.setIcon(icons.get('go-previous'))
        self.viewer_reload.setIcon(icons.get('reload'))
        self.viewer_open.setIcon(icons.get('document-open'))
        self.viewer_close.setIcon(icons.get('document-close'))
        self.viewer_close_other.setText(_("Close other documents"))
        self.viewer_close_all.setText(_("Close all documents"))

    def translateUI(self):
        self.viewer_help.setText(_("Show Help"))
        self.viewer_document_select.setText(_("Select Music View Document"))
        self.viewer_print.setText(_("&Print Music..."))
        self.viewer_zoom_in.setText(_("Zoom &In"))
        self.viewer_zoom_out.setText(_("Zoom &Out"))
        self.viewer_zoom_original.setText(_("Original &Size"))
        self.viewer_zoom_combo.setText(_("Zoom Music"))
        self.viewer_fit_width.setText(_("Fit &Width"))
        self.viewer_fit_height.setText(_("Fit &Height"))
        self.viewer_fit_both.setText(_("Fit &Page"))
        self.viewer_single_pages.setText(_("Single Pages"))
        self.viewer_two_pages_first_right.setText(_("Two Pages (first page right)"))
        self.viewer_two_pages_first_left.setText(_("Two Pages (first page left)"))
        self.viewer_maximize.setText(_("&Maximize"))
        self.viewer_jump_to_cursor.setText(_("&Jump to Cursor Position"))
        self.viewer_sync_cursor.setText(_("S&ynchronize with Cursor Position"))
        self.viewer_copy_image.setText(_("Copy to &Image..."))
        self.viewer_pager.setText(_("Pager"))
        self.viewer_next_page.setText(_("Next Page"))
        self.viewer_next_page.setIconText(_("Next"))
        self.viewer_prev_page.setText(_("Previous Page"))
        self.viewer_prev_page.setIconText(_("Previous"))
        self.viewer_reload.setText(_("&Reload"))
        self.viewer_show_toolbar.setText(_("Show toolbar"))
        self.viewer_open.setText(_("Open music document(s)"))
        self.viewer_open.setIconText(_("Open"))
        self.viewer_close.setText(_("Close document"))
        self.viewer_close.setIconText(_("Close"))

    def _createViewdocChooserAction(self, panel):
        """Create the document chooser action.
        Subclasses must override this."""
        raise NotImplementedError()

class ComboBoxAction(QWidgetAction):
    """A widget action that opens a combobox widget popup when triggered."""
    def __init__(self, panel):
        super(ComboBoxAction, self).__init__(panel)
        self.triggered.connect(self.showPopup)

    def _createWidget(self, parent):
        """Factory method to create a concrete widget instance.
        Must be implemented by subclasses."""
        raise NotImplementedError()

    def createWidget(self, parent):
        """Create the concrete widget for the action,
        but only when it is added to a QToolBar instance."""

        # TODO:
        # Note this is a workaround for issue #760 / #762
        # Suppress the creation of a widget if the action is not added
        # to a QToolBar (the erroneous calls parent to QMenu items instead)

        if not isinstance(parent, QToolBar):
            return None
        else:
            return self._createWidget(parent)

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


class ViewdocChooserAction(ComboBoxAction):
    """A ComboBoxAction that keeps track of the current text document.
    It manages the list of generated PDF documents for every text document.
    If the mainwindow changes its current document and there are PDFs to display,
    it switches the current document.
    It also switches to a text document if a job finished for that document,
    and it generated new PDF documents.
    """

    viewdocClosed = pyqtSignal()
    viewdocsChanged = pyqtSignal()
    currentViewdocChanged = pyqtSignal(documents.Document)
    viewdocsMissing = pyqtSignal(list)

    def __init__(self, panel):
        super(ViewdocChooserAction, self).__init__(panel)
        self._model = None
        self._viewdoc = None
        self._viewdocs = []
        self._currentIndex = -1
        self._indices = weakref.WeakKeyDictionary()
        panel.mainwindow().currentDocumentChanged.connect(self.slotEditdocChanged)
        documents.documentUpdated.connect(self.slotEditdocUpdated)

    def _createWidget(self, parent):
        """Create and configure a ViewdocChooser.
        This is a factory method to instantiate the right class."""
        w = ViewdocChooser(parent)
        w.activated[int].connect(self.setCurrentIndex)
        if self._model:
            w.setModel(self._model)
        return w

    def _viewdocFiles(self):
        """Return a list with the filenames of all documents."""
        return [d.filename() for d in self._viewdocs]

    def slotEditdocChanged(self, doc):
        """Called when the mainwindow changes its current document."""
        # only switch our document if there are PDF documents to display
        if self._viewdoc is None or documents.group(doc).documents():
            self.setCurrentViewdoc(doc)

    def slotEditdocUpdated(self, doc, job):
        """Called when a Job, finished on the document, has created new PDFs."""
        # if result files of this document were already displayed, the display
        # is updated. Else the current document is switched if the document was
        # the current document to be engraved (e.g. sticky or master) and the
        # the job was started on this mainwindow
        import engrave
        mainwindow = self.parent().mainwindow()
        if (doc == self._viewdoc or
            (jobattributes.get(job).mainwindow == mainwindow and
             doc == engrave.engraver(mainwindow).document())):
            self.setCurrentViewdoc(doc)

    def setCurrentViewdoc(self, document):
        """Displays the DocumentGroup of the given text Document in our chooser."""
        prev = self._viewdoc
        self._viewdoc = document
        if prev:
            prev.loaded.disconnect(self.updateViewdoc)
            prev.closed.disconnect(self.closeViewdoc)
            self._indices[prev] = self._currentIndex
        document.loaded.connect(self.updateViewdoc)
        document.closed.connect(self.closeViewdoc)
        self._viewdocs = documents.group(document).documents()
        self._currentIndex = self._indices.get(document, 0)
        self.updateViewdoc()

    def updateViewdoc(self):
        """(Re)read the output documents of the current document and show them."""
        docs = self._viewdocs
        self.setVisible(bool(docs))
        self.setEnabled(bool(docs))

        # make model for the docs
        m = self._model = listmodel.ListModel([d.filename() for d in docs],
            display = os.path.basename, tooltip = self.setToolTip,
            icon = icons.file_type)
        m.setRoleFunction(Qt.UserRole, lambda f: f)
        for w in self.createdWidgets():
            w.setModel(m)

        index = self._currentIndex
        if index < 0 or index >= len(docs):
            index = 0
        self.viewdocsChanged.emit()
        self.setCurrentIndex(index)

    def setToolTip(self, name):
        if self.isPresent(name):
            return name
        else:
            return (_("File not found:\n{}\nPlease restore if you can.").format(name))

    def isPresent(self, filename):
        """Check if the viewdoc with the given filename
        has been marked as present."""
        for d in self._viewdocs:
            if d.filename() == filename:
                return d.ispresent

    def closeViewdoc(self):
        """Called when the current document is closed by the user."""
        self._viewdoc = None
        self._viewdocs = []
        self._currentIndex = -1
        self.setVisible(False)
        self.setEnabled(False)
        self.viewdocClosed.emit()
        self.viewdocsChanged.emit()

    def viewdocs(self):
        return self._viewdocs

    def setActiveViewdoc(self, filename, update = True):
        """Activate the given document if it's in the list of documents"""
        filenames = [d.filename() for d in self._viewdocs]
        if filename in filenames:
            self._currentIndex = filenames.index(filename)
            if update:
                self.updateViewdoc()

    def setCurrentIndex(self, index):
        if self._viewdocs:
            self._currentIndex = index
            p = QApplication.palette()
            if not self._viewdocs[index].updated:
                color = qutil.mixcolor(QColor(Qt.red), p.color(QPalette.Base), 0.3)
                p.setColor(QPalette.Base, color)
            for w in self.createdWidgets():
                w.setCurrentIndex(index)
                w.setPalette(p)
            self.currentViewdocChanged.emit(self._viewdocs[index])

    def currentIndex(self):
        return self._currentIndex

    def currentViewdoc(self):
        """Returns the currently selected viewer document."""
        if self._viewdocs:
            return self._viewdocs[self._currentIndex]

    def replaceViewdoc(self, olddoc, newdoc):
        """Instead of adding a new document replace an existing."""
        try:
            docindex = self._viewdocs.index(olddoc)
            self._viewdocs[docindex] = newdoc
            self.updateViewdoc()
        except ValueError:
            # no replacement possible because the original doc isn't found
            pass

    def removeViewdoc(self, document):
        if document:
            self._viewdocs.remove(document)
            self.updateViewdoc()

    def removeOtherViewdocs(self, document):
        self._viewdocs = [document]
        self.updateViewdoc()

    def removeAllViewdocs(self, update = True):
        self._viewdocs = []
        if update:
            self.updateViewdoc()

    def loadFiles(self, files, sort=False):
        """Load from a list of filenames. Check if the file already exists."""
        viewdocs = []
        for f in files:
            if not f in self._viewdocFiles():
                doc = documents.Document(f)
                viewdocs.append(doc)
        self.loadViewdocs(viewdocs, files[-1], sort)

    def loadViewdocs(self, viewdocs, active_viewdoc="", sort=False):
        """Load the viewer documents and set the active document."""
        self._viewdocs += viewdocs

        # bring active document to front
        # (will automatically 'pass' if empty)
        self.setActiveViewdoc(active_viewdoc, update = False)

        if sort:
            self.sortViewdocs(update = False)

        # finally: load documents
        self.updateViewdoc()

    def sortViewdocs(self, update = True):
        """sort the open manuscripts alphabetically."""
        self._viewdocs = sorted(self._viewdocs,
                            key= lambda d: os.path.basename(d.filename()))
        if update:
            self.updateViewdoc()

    def checkMissingFiles(self):
        """Check for missing files and emit signal if found."""
        missing = []
        for d in self._viewdocs:
            if not d.ispresent:
                missing.append(d.filename())
        if missing:
            self.viewdocsMissing.emit(missing)


class ViewdocChooser(QComboBox):
    def __init__(self, parent):
        super(ViewdocChooser, self).__init__(parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setEditable(False)
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

    def _createWidget(self, parent):
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
            text = "{0:.0f}%".format(round(scale * 100.0))
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
        self.setEditable(False)
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
