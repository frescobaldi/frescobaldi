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
import platform
import sys
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
import job
import pagedview
import qpageview.document
import qutil
import panel
import listmodel
import gadgets.drag

from . import documents

# viewModes from qpageview:
from qpageview import FixedScale, FitWidth, FitHeight, FitBoth
from qpageview import Horizontal, Vertical


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
        ac.music_save_settings.triggered.connect(self.writeSettings)
        ac.music_maximize.triggered.connect(self.maximize)
        ac.music_jump_to_cursor.triggered.connect(self.jumpToCursor)
        ac.music_sync_cursor.triggered.connect(self.toggleSyncCursor)
        ac.music_copy_image.triggered.connect(self.copyImage)
        ac.music_copy_text.triggered.connect(self.copyText)
        ac.music_document_select.documentsChanged.connect(self.updateActions)
        ac.music_copy_image.setEnabled(False)
        ac.music_copy_text.setEnabled(False)
        ac.music_reload.triggered.connect(self.reloadView)
        ac.music_clear.triggered.connect(self.clearView)

        # load the state of the actions from the preferences
        s = QSettings()
        s.beginGroup("musicview")
        ac.music_sync_cursor.setChecked(s.value("sync_cursor", False, bool))
        props = pagedview.PagedView.properties().setdefaults().load(s)
        ac._viewActions.updateFromProperties(props)
        ac._viewActions.viewRequested.connect(self.widget)   # force creation

    def translateUI(self):
        self.setWindowTitle(_("window title", "Music View"))
        self.toggleViewAction().setText(_("&Music View"))

    def createWidget(self):
        from . import widget
        w = widget.MusicView(self)
        s = QSettings()
        s.beginGroup("musicview")
        w.view.readProperties(s)
        w.view.rubberband().selectionChanged.connect(self.updateSelection)
        self.actionCollection._viewActions.setView(w.view)
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

    def writeSettings(self):
        """Save the current view properties as default."""
        if self.instantiated():
            s = QSettings()
            s.beginGroup("musicview")
            self.widget().view.writeProperties(s)

    def updateSelection(self, rect):
        self.actionCollection.music_copy_image.setEnabled(bool(rect))
        self.actionCollection.music_copy_text.setEnabled(bool(rect))

    def updateActions(self):
        ac = self.actionCollection
        ac.music_print.setEnabled(bool(ac.music_document_select.documents()))

    @activate
    def printMusic(self):
        if self.widget().view.pageCount():
            # warn about printing directly with cups on Mac
            s = QSettings()
            if (s.value("printing/directcups",
                       False if platform.system() == "Darwin" else True, bool)
                and platform.system() == "Darwin"):
                from PyQt5.QtCore import QUrl
                from PyQt5.QtWidgets import QMessageBox
                result =  QMessageBox.warning(self.mainwindow(),
                    _("Print Music"), _(
                    "As per your settings, you are about to print the file "
                    "directly to CUPS.\n"
                    "This is discouraged on macOS, since in this case the "
                    "settings of the system print window are ignored.\n"
                    "You can disable it in Music Preferences.\n\n"
                    "Do you really want to print to CUPS?\n\n"
                    "(If you are unsure, the answer is likely no.)"),
                    QMessageBox.Yes | QMessageBox.No)
                if result == QMessageBox.No:
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
            ac.music_document_select.setCurrentDocument(d)

    def clearView(self):
        """Clear the music view and 'forget' the compiled documents."""
        if self.instantiated():
            d = self.mainwindow().currentDocument()
            documents.group(d).clear()
            self.actionCollection.music_document_select.setCurrentDocument(d)
            self.widget().clear()

    def toggleSyncCursor(self):
        QSettings().setValue("musicview/sync_cursor",
            self.actionCollection.music_sync_cursor.isChecked())

    def copyImage(self):
        page, rect = self.widget().view.rubberband().selectedPage()
        if not page:
            return
        filename = self.widget().view.document().filename()
        import copy2image
        copy2image.copy_image(self, page, rect, filename)

    def copyText(self):
        text = self.widget().view.rubberband().selectedText()
        if text:
            QApplication.clipboard().setText(text)


class Actions(actioncollection.ActionCollection):
    name = "musicview"
    def createActions(self, panel):
        self._viewActions = va = pagedview.ViewActions()
        self.music_document_select = DocumentChooserAction(panel)
        self.music_print = QAction(panel)
        self.music_zoom_in = va.zoom_in
        self.music_zoom_out = va.zoom_out
        self.music_zoom_original = va.zoom_original
        self.music_zoom_combo = va.zoomer
        self.music_rotate_left = va.rotate_left
        self.music_rotate_right = va.rotate_right
        self.music_fit_width = va.fit_width
        self.music_fit_height = va.fit_height
        self.music_fit_both = va.fit_both
        self.music_single_pages = va.layout_single
        self.music_two_pages_first_right = va.layout_double_right
        self.music_two_pages_first_left = va.layout_double_left
        self.music_raster = va.layout_raster
        self.music_horizontal = va.horizontal
        self.music_vertical = va.vertical
        self.music_continuous = va.continuous
        self.music_save_settings = QAction(panel)
        self.music_maximize = QAction(panel)
        self.music_jump_to_cursor = QAction(panel)
        self.music_sync_cursor = QAction(panel, checkable=True)
        self.music_copy_image = QAction(panel)
        self.music_copy_text = QAction(panel)
        self.music_pager = va.pager
        self.music_next_page = va.next_page
        self.music_prev_page = va.previous_page
        self.music_magnifier = va.magnifier
        self.music_reload = QAction(panel)
        self.music_clear = QAction(panel)

        self.music_print.setIcon(icons.get('document-print'))
        self.music_maximize.setIcon(icons.get('view-fullscreen'))
        self.music_jump_to_cursor.setIcon(icons.get('go-jump'))
        self.music_copy_image.setIcon(icons.get('edit-copy'))
        self.music_copy_text.setIcon(icons.get('edit-copy'))
        self.music_clear.setIcon(icons.get('edit-clear'))

        self.music_document_select.setShortcut(QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_O))
        self.music_jump_to_cursor.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_J))
        self.music_copy_image.setShortcut(QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_C))
        self.music_reload.setShortcut(QKeySequence(Qt.Key_F5))

    def translateUI(self):
        self.music_document_select.setText(_("Select Music View Document"))
        self.music_print.setText(_("&Print Music..."))
        self.music_zoom_combo.setText(_("Zoom Music"))
        self.music_save_settings.setText(_("Save current View settings as default"))
        self.music_maximize.setText(_("&Maximize"))
        self.music_jump_to_cursor.setText(_("&Jump to Cursor Position"))
        self.music_sync_cursor.setText(_("S&ynchronize with Cursor Position"))
        self.music_copy_image.setText(_("Copy to &Image..."))
        self.music_copy_text.setText(_("Copy Selected &Text"))
        self.music_reload.setText(_("&Reload"))
        self.music_clear.setText(_("Clear"))


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
    currentDocumentChanged = pyqtSignal(qpageview.document.Document)

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

    def slotDocumentUpdated(self, doc, j):
        """Called when a Job, finished on the document, has created new PDFs."""
        # if result files of this document were already displayed, the display
        # is updated. Else the current document is switched if the document was
        # the current document to be engraved (e.g. sticky or master) and the
        # the job was started on this mainwindow
        import engrave
        mainwindow = self.parent().mainwindow()
        if (doc == self._document or
            (job.attributes.get(j).mainwindow == mainwindow and
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
