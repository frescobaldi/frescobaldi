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
import platform
import weakref

from PyQt6.QtCore import QSettings, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QPalette
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QLabel,
    QMessageBox, QSpinBox, QToolBar, QWidgetAction)

import app
import actioncollection
import actioncollectionmanager
import icons
import pagedview
import qpageview.document
import qutil
import panel
import listmodel
import gadgets.drag

from . import documents


# default zoom percentages
_zoomvalues = [50, 75, 100, 125, 150, 175, 200, 250, 300]

# viewModes from qpageview:
from qpageview import FixedScale, FitWidth, FitHeight, FitBoth


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
        super().__init__(mainwindow)
        self.hide()
        ac = self.actionCollection = self._createConcreteActions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        self.configureActions()
        self.connectActions()

    def configureActions(self):
        ac = self.actionCollection
        ac.viewer_copy_image.setEnabled(False)
        ac.viewer_sync_cursor.setChecked(False)

        # load the state of the actions from the preferences
        s = QSettings()
        s.beginGroup(self.viewerName())
        ac.viewer_sync_cursor.setChecked(s.value("sync-cursor", False, bool))
        ac.viewer_show_toolbar.setChecked(s.value("show-toolbar", True, bool))
        props = pagedview.PagedView.properties().setdefaults().load(s)
        ac._viewActions.updateFromProperties(props)
        ac._viewActions.viewRequested.connect(self.widget)   # force creation

    def connectActions(self):
        ac = self.actionCollection
        ac.viewer_help.triggered.connect(self.slotShowHelp)
        ac.viewer_print.triggered.connect(self.printMusic)
        # Page display actions
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
        s = QSettings()
        s.beginGroup(self.viewerName())
        w.view.readProperties(s)
        w.view.rubberband().selectionChanged.connect(self.updateSelection)
        self.actionCollection._viewActions.setView(w.view)
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

    def updateActions(self):
        ac = self.actionCollection
        ac.viewer_print.setEnabled(bool(ac.viewer_document_select.viewdocs()))

    @activate
    def printMusic(self):
        if self.widget().view.pageCount():
            # warn about printing directly with cups on Mac
            s = QSettings()
            if (s.value("printing/directcups",
                       False if platform.system() == "Darwin" else True, bool)
                and platform.system() == "Darwin"):
                from PyQt6.QtCore import QUrl
                from PyQt6.QtWidgets import QMessageBox
                result =  QMessageBox.warning(self.mainwindow(),
                    _("Print Music"), _(
                    "As per your settings, you are about to print the file "
                    "directly to CUPS.\n"
                    "This is discouraged on macOS, since in this case the "
                    "settings of the system print window are ignored.\n"
                    "You can disable it in Music Preferences.\n\n"
                    "Do you really want to print to CUPS?\n\n"
                    "(If you are unsure, the answer is likely no.)"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if result == QMessageBox.StandardButton.No:
                    return
            self.widget().view.print()

    @activate
    def jumpToCursor(self):
        self.widget().showCurrentLinks(True, 10000)

    @activate
    def reloadView(self):
        d = self.mainwindow().currentDocument()
        group = documents.group(d)
        if group.update() or group.update(False):
            ac = self.actionCollection
            ac.viewer_document_select.setCurrentViewdoc(d)

    def toggleSyncCursor(self):
        checked = self.actionCollection.viewer_sync_cursor.isChecked()
        QSettings().setValue(f"{self.viewerName()}/sync-cursor", checked)

    def slotShowToolbar(self):
        """Sets the visibility of the viewer's toolbar and saves it to
        the application settings."""
        checked = self.actionCollection.viewer_show_toolbar.isChecked()
        self.widget().toolbar().setVisible(checked)
        QSettings().setValue(f"{self.viewerName()}/show-toolbar", checked)

    def slotShowHelp(self):
        import userguide
        userguide.show(self.viewerName())

    def copyImage(self):
        page, rect = self.widget().view.rubberband().selectedPage()
        if not page:
            return
        filename = self.widget().view.document().filename()
        import copy2image
        copy2image.copy_image(self, page, rect, filename)

    def slotShowViewdoc(self):
        """Bring the document to front that was selected from the context menu"""
        doc_filename = self.sender().checkedAction()._document_filename
        self.actionCollection.viewer_document_select.setActiveViewdoc(doc_filename)

    def _openViewdocsCaption(self):
        """Returns the caption for the file open dialog."""
        raise NotImplementedError(f'Method _openViewdocsCaption has to be implemented in {self.viewerName()}')

    def openViewdocs(self):
        """ Displays an open dialog to open music document(s). """
        caption = self._openViewdocsCaption()
        current_viewer_doc = self.widget().currentViewdoc()
        current_filename = current_viewer_doc.filename() if current_viewer_doc else None
        current_editor_document = self.mainwindow().currentDocument().url().toLocalFile()
        directory = os.path.dirname(current_filename or current_editor_document or app.basedir())
        filetype = "{} (*.pdf)".format(_("PDF Files"))
        filenames = QFileDialog().getOpenFileNames(self, caption, directory, filetype)[0]
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
        self._viewActions = va = pagedview.ViewActions()
        self.viewer_help = QAction(panel)
        self.viewer_document_select = self._createViewdocChooserAction(panel)
        self.viewer_print = QAction(panel)
        self.viewer_zoom_in = va.zoom_in
        self.viewer_zoom_out = va.zoom_out
        self.viewer_zoom_original = va.zoom_original
        self.viewer_zoom_combo = va.zoomer
        self.viewer_rotate_left = va.rotate_left
        self.viewer_rotate_right = va.rotate_right
        self.viewer_fit_width = va.fit_width
        self.viewer_fit_height = va.fit_height
        self.viewer_fit_both = va.fit_both
        self.viewer_single_pages = va.layout_single
        self.viewer_two_pages_first_right = va.layout_double_right
        self.viewer_two_pages_first_left = va.layout_double_left
        self.viewer_maximize = QAction(panel)
        self.viewer_jump_to_cursor = QAction(panel)
        self.viewer_sync_cursor = QAction(panel, checkable=True)
        self.viewer_copy_image = QAction(panel)
        self.viewer_pager = va.pager
        self.viewer_next_page = va.next_page
        self.viewer_prev_page = va.previous_page
        self.viewer_magnifier = va.magnifier
        self.viewer_reload = QAction(panel)
        self.viewer_show_toolbar = QAction(panel, checkable=True)
        self.viewer_open = QAction(panel)
        self.viewer_close = QAction(panel)
        self.viewer_close_other = QAction(panel)
        self.viewer_close_all = QAction(panel)

        self.viewer_help.setIcon(icons.get('help-contents'))
        self.viewer_print.setIcon(icons.get('document-print'))
        self.viewer_maximize.setIcon(icons.get('view-fullscreen'))
        self.viewer_jump_to_cursor.setIcon(icons.get('go-jump'))
        self.viewer_copy_image.setIcon(icons.get('edit-copy'))
        self.viewer_reload.setIcon(icons.get('reload'))
        self.viewer_open.setIcon(icons.get('document-open'))
        self.viewer_close.setIcon(icons.get('document-close'))

    def translateUI(self):
        self.viewer_help.setText(_("Show Help"))
        self.viewer_document_select.setText(_("Select Music View Document"))
        self.viewer_print.setText(_("&Print Music..."))
        self.viewer_zoom_combo.setText(_("Zoom Music"))
        self.viewer_maximize.setText(_("&Maximize"))
        self.viewer_jump_to_cursor.setText(_("&Jump to Cursor Position"))
        self.viewer_sync_cursor.setText(_("S&ynchronize with Cursor Position"))
        self.viewer_copy_image.setText(_("Copy to &Image..."))
        self.viewer_reload.setText(_("&Reload"))
        self.viewer_show_toolbar.setText(_("Show toolbar"))
        self.viewer_open.setText(_("Open music document(s)"))
        self.viewer_open.setIconText(_("Open"))
        self.viewer_close.setText(_("Close document"))
        self.viewer_close.setIconText(_("Close"))
        self.viewer_close_other.setText(_("Close other documents"))
        self.viewer_close_all.setText(_("Close all documents"))

    def _createViewdocChooserAction(self, panel):
        """Create the document chooser action.
        Subclasses must override this."""
        raise NotImplementedError()

class ComboBoxAction(QWidgetAction):
    """A widget action that opens a combobox widget popup when triggered."""
    def __init__(self, panel):
        super().__init__(panel)
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
    currentViewdocChanged = pyqtSignal(qpageview.document.Document)
    viewdocsMissing = pyqtSignal(list)

    def __init__(self, panel):
        super().__init__(panel)
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

    def slotEditdocUpdated(self, doc, j):
        """Called when a Job, finished on the document, has created new PDFs."""
        # if result files of this document were already displayed, the display
        # is updated. Else the current document is switched if the document was
        # the current document to be engraved (e.g. sticky or master) and the
        # the job was started on this mainwindow
        import engrave
        mainwindow = self.parent().mainwindow()
        if (doc == self._viewdoc or
            (job.attributes.get(j).mainwindow == mainwindow and
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
            for w in self.createdWidgets():
                w.setCurrentIndex(index)
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
                doc = pagedview.loadPdf(f)
                doc.ispresent = os.path.isfile(f)
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
        super().__init__(parent)
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
