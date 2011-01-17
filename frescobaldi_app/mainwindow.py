# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Frescobaldi Main Window.
"""

import itertools
import os
import re
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import info
import icons
import actioncollection
import document
import view
import viewmanager
import metainfo
import signals
import recentfiles
import sessionmanager
import util
import matcher
import bookmarks
import lyrics
import panels


class MainWindow(QMainWindow):
    
    # both signals emit (current, previous)
    currentDocumentChanged = pyqtSignal(document.Document, document.Document)
    currentViewChanged = pyqtSignal(view.View, view.View)
    
    def __init__(self, other=None):
        """Creates a new MainWindow.
        
        It adds itself to app.windows to keep a reference.
        It shares the documents list with all other MainWindows. It copies
        some info (like the currently active document) from the 'other' window,
        if given.
        
        """
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self._currentDocument = None
        self._currentView = lambda: None
        self._allActionCollections = []
        
        # find an unused objectName
        names = set(win.objectName() for win in app.windows)
        for num in itertools.count(1):
            name = "MainWindow{0}".format(num)
            if name not in names:
                self.setObjectName(name)
                break
        
        self.setWindowIcon(icons.get('frescobaldi'))
        app.windows.append(self)
        
        mainwidget = QWidget()
        self.setCentralWidget(mainwidget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        mainwidget.setLayout(layout)
        self.tabBar = TabBar(self)
        self.viewManager = viewmanager.ViewManager(self)
        layout.addWidget(self.tabBar)
        layout.addWidget(self.viewManager)

        self.documentActions = DocumentActionGroup(self)
        self.sessionManager = sessionmanager.SessionManager(self)
        self.createActions()
        
        # create other stuff that have their own actions
        
        self.createMenus()
        self.createToolBars()
        
        app.translateUI(self)
        app.sessionChanged.connect(self.updateWindowTitle)
        
        self.readSettings()
        
        self.historyManager = HistoryManager(self, other.historyManager if other else None)
        self.viewManager.viewChanged.connect(self.slotViewChanged)
        self.tabBar.currentDocumentChanged.connect(self.setCurrentDocument)
        self.setAcceptDrops(True)
        
        # keep track of all ActionCollections for the keyboard settings dialog
        self.addActionCollection(self.actionCollection)
        self.addActionCollection(self.viewManager.actionCollection)
        self.addActionCollection(self.sessionManager.actionCollection)
        
        if other:
            self.setCurrentDocument(other.currentDocument())
        app.mainwindowCreated(self)
        
    def documents(self):
        """Returns the list of documents in the order of the TabBar."""
        return self.tabBar.documents()
        
    def currentView(self):
        return self._currentView()
    
    def currentDocument(self):
        return self._currentDocument
        
    def setCurrentDocument(self, doc, findOpenView=False):
        self.viewManager.setCurrentDocument(doc, findOpenView)

    def slotViewChanged(self, view):
        curv = self._currentView()
        if curv:
            if curv is view:
                return
            curv.copyAvailable.disconnect(self.updateViewActions)
            curv.selectionChanged.disconnect(self.updateViewActions)
            curv.cursorPositionChanged.disconnect(self.updateMarkStatus)
        view.copyAvailable.connect(self.updateViewActions)
        view.selectionChanged.connect(self.updateViewActions)
        view.cursorPositionChanged.connect(self.updateMarkStatus)
        self._currentView = weakref.ref(view)
        
        doc = view.document()
        curd, self._currentDocument = self._currentDocument, doc
        if curd is not doc:
            if curd:
                curd.undoAvailable.disconnect(self.updateDocActions)
                curd.redoAvailable.disconnect(self.updateDocActions)
                curd.modificationChanged.disconnect(self.updateWindowTitle)
                curd.urlChanged.disconnect(self.updateWindowTitle)
                curd.loaded.disconnect(self.updateDocActions)
                bookmarks.bookmarks(curd).marksChanged.disconnect(self.updateMarkStatus)
            doc.undoAvailable.connect(self.updateDocActions)
            doc.redoAvailable.connect(self.updateDocActions)
            doc.modificationChanged.connect(self.updateWindowTitle)
            doc.urlChanged.connect(self.updateWindowTitle)
            doc.loaded.connect(self.updateDocActions)
            bookmarks.bookmarks(doc).marksChanged.connect(self.updateMarkStatus)
            self.updateDocActions()
            self.updateWindowTitle()
        self.updateViewActions()
        self.updateMarkStatus()
        self.currentViewChanged.emit(view, curv)
        if curd is not doc:
            self.currentDocumentChanged.emit(doc, curd)
    
    def updateMarkStatus(self):
        view = self._currentView()
        ac = self.actionCollection
        ac.view_bookmark.setChecked(
            bookmarks.bookmarks(view.document()).hasMark(view.textCursor().blockNumber(), 'mark'))
        
    def updateViewActions(self):
        view = self._currentView()
        ac = self.actionCollection
        selection = view.textCursor().hasSelection()
        ac.edit_copy.setEnabled(selection)
        ac.edit_copy_colored_html.setEnabled(selection)
        ac.edit_cut.setEnabled(selection)
        ac.edit_cut_assign.setEnabled(selection)
        ac.edit_select_none.setEnabled(selection)
    
    def updateDocActions(self):
        doc = self.currentDocument()
        ac = self.actionCollection
        ac.edit_undo.setEnabled(doc.isUndoAvailable())
        ac.edit_redo.setEnabled(doc.isRedoAvailable())
        ac.view_highlighting.setChecked(metainfo.info(doc).highlighting)
        ac.tools_indent_auto.setChecked(metainfo.info(doc).autoindent)
        
    def updateWindowTitle(self):
        doc = self.currentDocument()
        name = []
        if sessionmanager.currentSession():
            name.append(sessionmanager.currentSession() + ':')
        if doc.url().isEmpty():
            name.append(doc.documentName())
        elif doc.url().toLocalFile():
            name.append(doc.url().toLocalFile())
        else:
            name.append(doc.url().toString())
        if doc.isModified():
            name.append(_("[modified]"))
        self.setWindowTitle(app.caption(" ".join(name)))
    
    def dropEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.accept()
            docs = [self.openUrl(url) for url in ev.mimeData().urls()]
            if docs:
                self.setCurrentDocument(docs[-1])
        
    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.accept()
        
    def closeEvent(self, ev):
        lastWindow = len(app.windows) == 1
        if lastWindow:
            self.sessionManager.saveCurrentSessionIfDesired()
            self.writeSettings()
        if not lastWindow or self.queryClose():
            app.windows.remove(self)
            app.mainwindowClosed(self)
            ev.accept()
        else:
            ev.ignore()

    def queryClose(self):
        """Tries to close all documents, returns True if succeeded."""
        for doc in self.historyManager.documents():
            if not self.queryCloseDocument(doc):
                return False
        for doc in self.historyManager.documents()[::-1]:
            doc.close()
        return True

    def queryCloseDocument(self, doc):
        """Returns whether a document can be closed.
        
        If modified, asks the user. The document is not closed.
        """
        if not doc.isModified():
            return True
        self.setCurrentDocument(doc, findOpenView=True)
        res = QMessageBox.warning(self, _("Close Document"),
            _("The document \"{name}\" has been modified.\n"
            "Do you want to save your changes or discard them?").format(name=doc.documentName()),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if res == QMessageBox.Save:
            return self.saveDocument(doc)
        else:
            return res == QMessageBox.Discard
        
    def readSettings(self):
        """ Read a few settings from the application global config. """
        settings = QSettings()
        defaultSize = QApplication.desktop().screen().size() * 2 / 3
        self.resize(settings.value("size", defaultSize))
        
    def writeSettings(self):
        """ Write a few settings to the application global config. """
        settings = QSettings()
        if not self.isFullScreen():
            settings.setValue("size", self.size())
        
    def readSessionSettings(self, settings):
        """Restore ourselves from session manager settings.
        
        These methods store much more information than the readSettings and
        writeSettings methods. This method tries to restore window size and
        position. Also the objectName() is set, so that the window manager can
        preserve stacking order, etc.
        
        """
        name = settings.value('name', '')
        if name:
            self.setObjectName(name)
        self.restoreGeometry(settings.value('geometry', QByteArray()))
        
    def writeSessionSettings(self, settings):
        """Write our state to the session manager settings.
        
        See readSessionSettings().
        
        """
        settings.setValue('name', self.objectName())
        settings.setValue('geometry', self.saveGeometry())

    def openUrl(self, url, encoding=None):
        """Same as app.openUrl but with some error checking and recent files."""
        if not url.toLocalFile():
            # we only support local files
            QMessageBox.warning(self, app.caption(_("Warning")),
                _("Can't load non-local document:\n\n{url}").format(
                    url=url.toString()))
        else:
            recentfiles.add(url)
        return app.openUrl(url, encoding)
    
    def addActionCollection(self, collection):
        """Add an actioncollection to our list (used for changing keyboard shortcuts).
        
        Does not keep a reference to it.  If the ActionCollection gets garbage collected,
        it is removed automatically from our list.
        
        """
        ref = weakref.ref(collection)
        if ref not in self._allActionCollections:
            self._allActionCollections.append(ref)
        
    def removeActionCollection(self, collection):
        """Removes the given ActionCollection from our list."""
        ref = weakref.ref(collection)
        try:
            self._allActionCollections.remove(ref)
        except ValueError:
            pass

    def actionCollections(self):
        """Iterate over the ActionCollections in our list."""
        for ref in self._allActionCollections[:]: # copy
            collection = ref()
            if collection:
                yield collection
            else:
                self._allActionCollections.remove(ref)
        
    ##
    # Implementations of menu actions
    ##
    
    def newDocument(self):
        """ Creates a new, empty document. """
        self.setCurrentDocument(document.Document())
        
    def openDocument(self):
        """ Displays an open dialog to open one or more documents. """
        ext = os.path.splitext(self.currentDocument().url().path())[1]
        filetypes = app.filetypes(ext)
        caption = app.caption(_("Open File"))
        directory = os.path.dirname(self.currentDocument().url().toLocalFile())
        if not directory:
            conf = sessionmanager.currentSessionGroup() or QSettings()
            directory = conf.value("basedir", "")
        files = QFileDialog.getOpenFileNames(self, caption, directory, filetypes)
        docs = [self.openUrl(QUrl.fromLocalFile(f)) for f in files]
        if docs:
            self.setCurrentDocument(docs[-1])
        
    def saveDocument(self, doc):
        """ Saves the document, asking for a name if necessary.
        
        Returns True if saving succeeded.
        
        """
        if doc.url().isEmpty():
            return self.saveDocumentAs(doc)
        filename = dest = doc.url().toLocalFile()
        if not filename:
            dest = doc.url().toString()
        if not util.iswritable(filename):
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=dest))
            return False
        success = doc.save()
        if not success:
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=filename))
        return success
            
    def saveDocumentAs(self, doc):
        """ Saves the document, always asking for a name.
        
        Returns True if saving succeeded.
        
        """
        filename = doc.url().toLocalFile()
        filetypes = app.filetypes(os.path.splitext(filename)[1])
        caption = app.caption(_("Save File"))
        filename = doc.url().toLocalFile()
        if not filename:
            conf = sessionmanager.currentSessionGroup() or QSettings()
            filename = conf.value("basedir", "") # default directory to save to
        filename = QFileDialog.getSaveFileName(self, caption, filename, filetypes)
        if not filename:
            return False # cancelled
        if not util.iswritable(filename):
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=filename))
            return False
        url = QUrl.fromLocalFile(filename)
        doc.setUrl(url)
        recentfiles.add(url)
        return self.saveDocument(doc)
        
    def closeDocument(self, doc):
        """ Closes the document, asking for saving if modified.
        
        Returns True if closing succeeded.
        
        """
        close = self.queryCloseDocument(doc)
        if close:
            doc.close()
            # keep one document
            if not app.documents:
                document.Document()
        return close
        
    def saveCurrentDocument(self):
        return self.saveDocument(self.currentDocument())
    
    def saveCurrentDocumentAs(self):
        return self.saveDocumentAs(self.currentDocument())
        
    def closeCurrentDocument(self):
        return self.closeDocument(self.currentDocument())
    
    def saveAllDocuments(self):
        """ Saves all documents.
        
        Returns True if all documents were saved.
        If one document failed or was cancelled the whole operation is cancelled
        and this function returns False.
        
        """
        cur = self.currentDocument()
        for doc in self.historyManager.documents():
            if doc.isModified():
                if doc.url().isEmpty():
                    self.setCurrentDocument(doc, findOpenView=True)
                    res = self.saveDocumentAs(doc)
                else:
                    res = self.saveDocument(doc)
                if not res:
                    return False
        self.setCurrentDocument(cur, findOpenView=True)
        return True
                    
    def closeOtherDocuments(self):
        """ Closes all documents that are not the current document.
        
        Returns True if all documents were closed.
        
        """
        cur = self.currentDocument()
        docs = self.historyManager.documents()[1:]
        for doc in docs:
            if not self.queryCloseDocument(doc):
                self.setCurrentDocument(cur, findOpenView=True)
                return False
        for doc in docs:
            doc.close()
        return True
    
    def closeAllDocuments(self):
        """Closes all documents and keep one new, empty document."""
        self.sessionManager.saveCurrentSessionIfDesired()
        if self.queryClose():
            sessionmanager.setCurrentSession(None)
            document.Document()
    
    def quit(self):
        """Closes all MainWindows."""
        for window in app.windows[:]: # copy
            if window is not self:
                window.close()
        self.close()
            
    def openCurrentDirectory(self):
        directory = os.path.dirname(self.currentDocument().url().toLocalFile()) or os.getcwdu()
        QDesktopServices.openUrl(QUrl.fromLocalFile(directory))
    
    def printSource(self):
        cursor = self.currentView().textCursor()
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle(app.caption(_("Print Source")))
        options = QAbstractPrintDialog.PrintToFile | QAbstractPrintDialog.PrintShowPageSize
        if cursor.hasSelection():
            options |= QAbstractPrintDialog.PrintSelection
        dlg.setOptions(options)
        if dlg.exec_():
            doc = self.currentDocument().htmlCopy('printer')
            doc.setMetaInformation(QTextDocument.DocumentTitle, self.currentDocument().url().toString())
            font = doc.defaultFont()
            font.setPointSizeF(font.pointSizeF() * 0.8)
            doc.setDefaultFont(font)
            if dlg.testOption(QAbstractPrintDialog.PrintSelection):
                # cut out not selected text
                start, end = cursor.position(), cursor.anchor()
                if start > end:
                    start, end = end, start
                cur1 = QTextCursor(doc)
                cur1.setPosition(start, QTextCursor.KeepAnchor)
                cur2 = QTextCursor(doc)
                cur2.setPosition(end)
                cur2.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                cur2.removeSelectedText()
                cur1.removeSelectedText()
            doc.print_(printer)
    
    def exportColoredHtml(self):
        doc = self.currentDocument()
        name, ext = os.path.splitext(os.path.basename(doc.url().path()))
        if name:
            if ext.lower() == ".html":
                name += "_html"
            name += ".html"
        dir = os.path.dirname(doc.url().toLocalFile())
        if dir:
            name = os.path.join(dir, name)
        filename = QFileDialog.getSaveFileName(self, app.caption(_("Export as HTML")),
            name, "{0} (*.html)".format("HTML Files"))
        if not filename:
            return #cancelled
        html = doc.htmlCopy().toHtml('utf-8').encode('utf-8')
        try:
            with open(filename, "w") as f:
                f.write(str(html))
        except (IOError, OSError) as err:
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}\n\n{error}").format(url=filename, error=err))
        
    def undo(self):
        self.currentDocument().undo()
        
    def redo(self):
        self.currentDocument().redo()
    
    def cut(self):
        self.currentView().cut()
        
    def copy(self):
        self.currentView().copy()
        
    def paste(self):
        self.currentView().paste()
        
    def copyColoredHtml(self):
        cursor = self.currentView().textCursor()
        if not cursor.hasSelection():
            return
        doc = self.currentDocument().htmlCopy()
        cur1 = QTextCursor(doc)
        cur1.setPosition(cursor.anchor())
        cur1.setPosition(cursor.position(), QTextCursor.KeepAnchor)
        html = QMimeData()
        html.setHtml(cur1.selection().toHtml())
        html.setText(cur1.selection().toHtml())
        QApplication.clipboard().setMimeData(html)
        
    def selectNone(self):
        cursor = self.currentView().textCursor()
        cursor.clearSelection()
        self.currentView().setTextCursor(cursor)
    
    def selectAll(self):
        self.currentView().selectAll()
        
    def find(self):
        import search
        search.Search.instance(self).find()
        
    def replace(self):
        import search
        search.Search.instance(self).replace()
        
    def showPreferences(self):
        import preferences
        dlg = preferences.PreferencesDialog(self)
        dlg.exec_()
        dlg.deleteLater()
    
    def toggleHighlighting(self):
        minfo = metainfo.info(self.currentDocument())
        minfo.highlighting = not minfo.highlighting
        self.currentDocument().highlighter.setHighlighting(minfo.highlighting)
        
    def markCurrentLine(self):
        view = self.currentView()
        lineNumber = view.textCursor().blockNumber()
        bookmarks.bookmarks(view.document()).toggleMark(lineNumber, 'mark')
    
    def clearErrorMarks(self):
        bookmarks.bookmarks(self.currentDocument()).clear('error')
        
    def clearAllMarks(self):
        bookmarks.bookmarks(self.currentDocument()).clear()
    
    def nextMark(self):
        view = self.currentView()
        lineNumber = view.textCursor().blockNumber()
        lineNumber = bookmarks.bookmarks(view.document()).nextMark(lineNumber)
        if lineNumber is not None:
            cursor = QTextCursor(view.document().findBlockByNumber(lineNumber))
            view.setTextCursor(cursor)
            view.ensureCursorVisible()
            
    def previousMark(self):
        view = self.currentView()
        lineNumber = view.textCursor().blockNumber()
        lineNumber = bookmarks.bookmarks(view.document()).previousMark(lineNumber)
        if lineNumber is not None:
            cursor = QTextCursor(view.document().findBlockByNumber(lineNumber))
            view.setTextCursor(cursor)
            view.ensureCursorVisible()
    
    def toggleAutoIndent(self):
        minfo = metainfo.info(self.currentDocument())
        minfo.autoindent = not minfo.autoindent
    
    def reIndent(self):
        import indent
        indent.reIndent(self.currentView().textCursor())
        
    def toggleFullScreen(self, enabled):
        if enabled:
            self._maximized = self.isMaximized()
            self.showFullScreen()
        else:
            self.showNormal()
            if self._maximized:
                self.showMaximized()
    
    def newWindow(self):
        """Opens a new MainWindow."""
        MainWindow(self).show()

    def scrollUp(self):
        """Scroll up without moving the cursor"""
        sb = self.currentView().verticalScrollBar()
        sb.setValue(sb.value() - 1 if sb.value() else 0)
        
    def scrollDown(self):
        """Scroll down without moving the cursor"""
        sb = self.currentView().verticalScrollBar()
        sb.setValue(sb.value() + 1)
        
    def createActions(self):
        self.actionCollection = ac = ActionCollection()
        
        # recent files
        self.menu_recent_files = m = QMenu()
        ac.file_open_recent.setMenu(m)
        m.aboutToShow.connect(self.populateRecentFilesMenu)
        m.triggered.connect(self.slotRecentFilesAction)
        
        # documents submenu
        self.menu_documents = m = QMenu()
        ac.view_document.setMenu(m)
        m.aboutToShow.connect(self.populateDocumentsMenu)
        
        # connections
        ac.file_quit.triggered.connect(self.quit, Qt.QueuedConnection)
        ac.file_new.triggered.connect(self.newDocument)
        ac.file_open.triggered.connect(self.openDocument)
        ac.file_open_current_directory.triggered.connect(self.openCurrentDirectory)
        ac.file_save.triggered.connect(self.saveCurrentDocument)
        ac.file_save_as.triggered.connect(self.saveCurrentDocumentAs)
        ac.file_save_all.triggered.connect(self.saveAllDocuments)
        ac.file_print_source.triggered.connect(self.printSource)
        ac.file_close.triggered.connect(self.closeCurrentDocument)
        ac.file_close_other.triggered.connect(self.closeOtherDocuments)
        ac.file_close_all.triggered.connect(self.closeAllDocuments)
        ac.export_colored_html.triggered.connect(self.exportColoredHtml)
        ac.edit_undo.triggered.connect(self.undo)
        ac.edit_redo.triggered.connect(self.redo)
        ac.edit_cut.triggered.connect(self.cut)
        ac.edit_copy.triggered.connect(self.copy)
        ac.edit_paste.triggered.connect(self.paste)
        ac.edit_copy_colored_html.triggered.connect(self.copyColoredHtml)
        ac.edit_select_all.triggered.connect(self.selectAll)
        ac.edit_select_none.triggered.connect(self.selectNone)
        ac.edit_find.triggered.connect(self.find)
        ac.edit_replace.triggered.connect(self.replace)
        ac.edit_preferences.triggered.connect(self.showPreferences)
        ac.view_next_document.triggered.connect(self.tabBar.nextDocument)
        ac.view_previous_document.triggered.connect(self.tabBar.previousDocument)
        ac.view_next_mark.triggered.connect(self.nextMark)
        ac.view_previous_mark.triggered.connect(self.previousMark)
        ac.view_scroll_up.triggered.connect(self.scrollUp)
        ac.view_scroll_down.triggered.connect(self.scrollDown)
        ac.view_highlighting.triggered.connect(self.toggleHighlighting)
        ac.view_bookmark.triggered.connect(self.markCurrentLine)
        ac.view_clear_error_marks.triggered.connect(self.clearErrorMarks)
        ac.view_clear_all_marks.triggered.connect(self.clearAllMarks)
        ac.tools_indent_auto.triggered.connect(self.toggleAutoIndent)
        ac.tools_indent_indent.triggered.connect(self.reIndent)
        ac.window_new.triggered.connect(self.newWindow)
        ac.window_fullscreen.toggled.connect(self.toggleFullScreen)
        ac.help_whatsthis.triggered.connect(QWhatsThis.enterWhatsThisMode)
        
    def populateDocumentsMenu(self):
        self.menu_documents.clear()
        for a in self.documentActions.actions():
            self.menu_documents.addAction(a)
    
    def populateRecentFilesMenu(self):
        self.menu_recent_files.clear()
        used = []
        for url in recentfiles.urls():
            f = url.toLocalFile()
            dirname, basename = os.path.split(f)
            text = "{0} ({1})".format(basename, dirname)
            
            # add accelerators
            text = text.replace('&', '&&')
            for m in itertools.chain(re.finditer(r'\b\w', text),
                                     re.finditer(r'\B\w', text)):
                if m.group().lower() not in used:
                    used.append(m.group().lower())
                    text = text[:m.start()] + '&' + text[m.start():]
                    break

            self.menu_recent_files.addAction(text).url = url
    
    def slotRecentFilesAction(self, action):
        """Called when a recent files menu action is triggered."""
        doc = self.openUrl(action.url)
        self.setCurrentDocument(doc)
        
    def createMenus(self):
        ac = self.actionCollection
        self.menu_file = m = self.menuBar().addMenu('')
        m.addAction(ac.file_new)
        m.addSeparator()
        m.addAction(ac.file_open)
        m.addAction(ac.file_open_recent)
        m.addAction(ac.file_open_current_directory)
        m.addSeparator()
        m.addAction(ac.file_save)
        m.addAction(ac.file_save_as)
        m.addSeparator()
        m.addAction(ac.file_save_all)
        m.addSeparator()
        m.addAction(ac.file_print_music)
        m.addAction(ac.file_print_source)
        self.menu_file_export = e = m.addMenu('')
        m.addSeparator()
        m.addAction(ac.file_close)
        m.addAction(ac.file_close_other)
        m.addAction(ac.file_close_all)
        m.addSeparator()
        m.addAction(ac.file_quit)
        
        e.addAction(ac.export_colored_html)
        
        self.menu_edit = m = self.menuBar().addMenu('')
        m.addAction(ac.edit_undo)
        m.addAction(ac.edit_redo)
        m.addSeparator()
        m.addAction(ac.edit_cut_assign)
        m.addAction(ac.edit_cut)
        m.addAction(ac.edit_copy)
        m.addAction(ac.edit_copy_colored_html)
        m.addAction(ac.edit_paste)
        m.addSeparator()
        m.addAction(ac.edit_select_all)
        m.addAction(ac.edit_select_current_toplevel)
        m.addAction(ac.edit_select_none)
        m.addSeparator()
        m.addAction(ac.edit_find)
        m.addAction(ac.edit_find_next)
        m.addAction(ac.edit_find_previous)
        m.addAction(ac.edit_replace)
        m.addSeparator()
        m.addAction(ac.edit_preferences)
        
        self.menu_view = m = self.menuBar().addMenu('')
        m.addAction(ac.view_next_document)
        m.addAction(ac.view_previous_document)
        m.addAction(ac.view_document)
        m.addSeparator()
        m.addAction(ac.view_highlighting)
        m.addSeparator()
        m.addAction(ac.view_bookmark)
        m.addAction(ac.view_clear_error_marks)
        m.addAction(ac.view_clear_all_marks)
        
        self.menu_lilypond = m = self.menuBar().addMenu('')
        m.addAction(ac.lilypond_run_preview)
        m.addAction(ac.lilypond_run_publish)
        m.addAction(ac.lilypond_run_custom)
        m.addAction(ac.lilypond_cancel)
        
        self.menu_tools = m = self.menuBar().addMenu('')
        m.addAction(ac.tools_indent_auto)
        m.addAction(ac.tools_indent_indent)
        m.addSeparator()
        self.menu_tools_lyrics = lm = m.addMenu('')
        
        la = lyrics.lyrics(self).actionCollection
        lm.addAction(la.lyrics_hyphenate)
        lm.addAction(la.lyrics_dehyphenate)
        lm.addSeparator()
        lm.addAction(la.lyrics_copy_dehyphenated)
        
        m.addSeparator()
        panels.manager(self).addActionsToMenu(m)
        
        self.menu_window = m = self.menuBar().addMenu('')
        vm = self.viewManager.actionCollection
        m.addAction(ac.window_new)
        m.addSeparator()
        m.addAction(vm.window_split_horizontal)
        m.addAction(vm.window_split_vertical)
        m.addAction(vm.window_close_view)
        m.addAction(vm.window_close_others)
        m.addAction(vm.window_next_view)
        m.addAction(vm.window_previous_view)
        m.addSeparator()
        m.addAction(ac.window_fullscreen)
        
        self.menu_sessions = m = self.menuBar().addMenu('')
        sm = self.sessionManager.actionCollection
        m.addAction(sm.session_new)
        m.addAction(sm.session_save)
        m.addSeparator()
        m.addAction(sm.session_manage)
        m.addSeparator()
        m.addAction(sm.session_none)
        m.addSeparator()
        
        m.aboutToShow.connect(self.sessionManager.populateSessionsMenu)
        
        self.menu_help = m = self.menuBar().addMenu('')
        m.addAction(ac.help_manual)
        m.addAction(ac.help_whatsthis)
        m.addSeparator()
        m.addAction(ac.help_bugreport)
        m.addSeparator()
        m.addAction(ac.help_about)
        
        # actions that are not in menus
        self.addAction(ac.view_scroll_up)
        self.addAction(ac.view_scroll_down)
        self.addAction(ac.view_next_mark)
        self.addAction(ac.view_previous_mark)
        
    def createToolBars(self):
        ac = self.actionCollection
        self.toolbar_main = t = self.addToolBar('')
        t.addAction(ac.file_new)
        t.addAction(ac.file_open)
        t.addSeparator()
        t.addAction(ac.file_save)
        t.addAction(ac.file_save_as)
        t.addSeparator()
        t.addAction(ac.edit_undo)
        t.addAction(ac.edit_redo)
        t.addSeparator()
        t.addAction(ac.lilypond_runner)
        t.addAction(ac.file_print_music)
        
    def translateUI(self):
        self.menu_file.setTitle(_('&File'))
        self.menu_edit.setTitle(_('&Edit'))
        self.menu_view.setTitle(_('&View'))
        self.menu_lilypond.setTitle(_('&LilyPond'))
        self.menu_tools.setTitle(_('&Tools'))
        self.menu_window.setTitle(_('&Window'))
        self.menu_sessions.setTitle(_('&Sessions'))
        self.menu_help.setTitle(_('&Help'))
        self.toolbar_main.setWindowTitle(_("Main Toolbar"))
        
        self.menu_file_export.setTitle(_("&Export"))
        self.menu_tools_lyrics.setTitle(_("&Lyrics"))
    

class HistoryManager(object):
    """Keeps the history of document switches by the user.
    
    If a document is closed, the previously active document is set active.
    If a document is created and it is the first one, it is also set active.
    
    """
    def __init__(self, mainwin, othermanager=None):
        self.mainwin = weakref.ref(mainwin)
        self._documents = list(othermanager._documents if othermanager else app.documents)
        mainwin.currentDocumentChanged.connect(self.setCurrentDocument)
        app.documentCreated.connect(self.addDocument, 1)
        app.documentClosed.connect(self.removeDocument, 1)
        
    def addDocument(self, doc):
        self._documents.insert(-1, doc)
        if len(self._documents) == 1:
            self.mainwin().setCurrentDocument(doc)

    def removeDocument(self, doc):
        active = doc is self._documents[-1]
        if active and len(self._documents) > 1:
            self.mainwin().setCurrentDocument(self._documents[-2])
        self._documents.remove(doc)
    
    def setCurrentDocument(self, doc):
        self._documents.remove(doc)
        self._documents.append(doc)
    
    def documents(self):
        """Returns the documents in order of most recent been active."""
        return self._documents[::-1]


class DocumentActionGroup(QActionGroup):
    """Maintains a list of actions to set the current document.
    
    The actions are added to the View->Documents menu in the order
    of the tabbar. The actions also get accelerators that are kept
    during the lifetime of a document.
    
    """
    def __init__(self, parent):
        super(DocumentActionGroup, self).__init__(parent)
        self._acts = {}
        self._accels = {}
        self.setExclusive(True)
        for d in app.documents:
            self.addDocument(d)
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        parent.currentDocumentChanged.connect(self.setCurrentDocument)
        self.triggered.connect(self.slotTriggered)
    
    def actions(self):
        return [self._acts[doc] for doc in self.parent().documents()]

    def addDocument(self, doc):
        a = QAction(self)
        a.setCheckable(True)
        if doc is self.parent().currentDocument():
            a.setChecked(True)
        self._acts[doc] = a
        self.setDocumentStatus(doc)
        
    def removeDocument(self, doc):
        self._acts[doc].deleteLater()
        del self._acts[doc]
        del self._accels[doc]
        
    def setCurrentDocument(self, doc):
        self._acts[doc].setChecked(True)

    def setDocumentStatus(self, doc):
        # create accels
        accels = [self._accels[d] for d in self._accels if d is not doc]
        name = doc.documentName().replace('&', '&&')
        for index, char in enumerate(name):
            if char.isalnum() and char.lower() not in accels:
                name = name[:index] + '&' + name[index:]
                self._accels[doc] = char.lower()
                break
        else:
            self._accels[doc] = ''
        self._acts[doc].setText(name)
        self._acts[doc].setIcon(icons.get('document-save') if doc.isModified() else QIcon())
    
    def slotTriggered(self, action):
        self.parent().setCurrentDocument(self._acts.keys()[self._acts.values().index(action)])


class TabBar(QTabBar):
    """The tabbar above the editor window."""
    
    currentDocumentChanged = pyqtSignal(document.Document)
    
    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent)
        
        self.setFocusPolicy(Qt.NoFocus)
        self.setTabsClosable(True) # TODO: make configurable
        self.setMovable(True)      # TODO: make configurable
        self.setExpanding(False)
        
        mainwin = self.window()
        self.docs = []
        for doc in app.documents:
            self.addDocument(doc)
            if doc is mainwin.currentDocument():
                self.setCurrentDocument(doc)
        
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        mainwin.currentDocumentChanged.connect(self.setCurrentDocument)
        self.currentChanged.connect(self.slotCurrentChanged)
        self.tabMoved.connect(self.slotTabMoved)
        self.tabCloseRequested.connect(self.slotTabCloseRequested)
        
    def documents(self):
        return list(self.docs)
        
    def addDocument(self, doc):
        if doc not in self.docs:
            self.docs.append(doc)
            self.blockSignals(True)
            self.addTab('')
            self.blockSignals(False)
            self.setDocumentStatus(doc)

    def removeDocument(self, doc):
        if doc in self.docs:
            index = self.docs.index(doc)
            self.docs.remove(doc)
            self.blockSignals(True)
            self.removeTab(index)
            self.blockSignals(False)

    def setDocumentStatus(self, doc):
        if doc in self.docs:
            index = self.docs.index(doc)
            icon = 'document-save' if doc.isModified() else 'text-plain'
            self.setTabIcon(index, icons.get(icon))
            self.setTabText(index, doc.documentName())
            tooltip = None
            if not doc.url().isEmpty():
                tooltip = doc.url().toString(QUrl.RemoveUserInfo)
            self.setTabToolTip(index, tooltip)
    
    def setCurrentDocument(self, doc):
        """ Raise the tab belonging to this document."""
        if doc in self.docs:
            index = self.docs.index(doc)
            self.blockSignals(True)
            self.setCurrentIndex(index)
            self.blockSignals(False)

    def slotCurrentChanged(self, index):
        """ Called when the user clicks a tab. """
        self.currentDocumentChanged.emit(self.docs[index])
    
    def slotTabCloseRequested(self, index):
        """ Called when the user clicks the close button. """
        self.window().closeDocument(self.docs[index])
    
    def slotTabMoved(self, index_from, index_to):
        """ Called when the user moved a tab. """
        doc = self.docs.pop(index_from)
        self.docs.insert(index_to, doc)
        
    def nextDocument(self):
        """ Switches to the next document. """
        index = self.currentIndex() + 1
        if index == self.count():
            index = 0
        self.setCurrentIndex(index)
        
    def previousDocument(self):
        index = self.currentIndex() - 1
        if index < 0:
            index = self.count() - 1
        self.setCurrentIndex(index)
    
    def contextMenuEvent(self, ev):
        index = self.tabAt(ev.pos())
        if index >= 0:
            self.contextMenu().exec_(self.docs[index], ev.globalPos())

    def contextMenu(self):
        try:
            return self._contextMenu
        except AttributeError:
            self._contextMenu = TabContextMenu(self)
        return self._contextMenu


class TabContextMenu(QMenu):
    def __init__(self, parent):
        super(TabContextMenu, self).__init__(parent)
        self._doc = lambda: None
        self.doc_save = self.addAction(icons.get('document-save'), '')
        self.doc_save_as = self.addAction(icons.get('document-save-as'), '')
        self.addSeparator()
        self.doc_close = self.addAction(icons.get('document-close'), '')
        
        self.doc_save.triggered.connect(self.docSave)
        self.doc_save_as.triggered.connect(self.docSaveAs)
        self.doc_close.triggered.connect(self.docClose)
        app.languageChanged.connect(self.translateUI)
        self.translateUI()
    
    def translateUI(self):
        self.doc_save.setText(_("&Save"))
        self.doc_save_as.setText(_("Save &As..."))
        self.doc_close.setText(_("&Close"))
        
    def exec_(self, document, pos):
        self._doc = weakref.ref(document)
        super(TabContextMenu, self).exec_(pos)
    
    def docSave(self):
        doc = self._doc()
        if doc:
            self.parent().window().saveDocument(doc)
    
    def docSaveAs(self):
        doc = self._doc()
        if doc:
            self.parent().window().saveDocumentAs(doc)
    
    def docClose(self):
        doc = self._doc()
        if doc:
            self.parent().window().closeDocument(doc)


class ActionCollection(actioncollection.ActionCollection):
    name = "main"
    def createActions(self, parent=None):
        self.file_new = QAction(parent)
        self.file_open = QAction(parent)
        self.file_open_recent = QAction(parent)
        self.file_open_current_directory = QAction(parent)
        self.file_save = QAction(parent)
        self.file_save_as = QAction(parent)
        self.file_save_all = QAction(parent)
        self.file_print_source = QAction(parent)
        self.file_print_music = QAction(parent)
        self.file_close = QAction(parent)
        self.file_close_other = QAction(parent)
        self.file_close_all = QAction(parent)
        self.file_quit = QAction(parent)
        
        self.export_colored_html = QAction(parent)
        
        self.edit_undo = QAction(parent)
        self.edit_redo = QAction(parent)
        self.edit_cut_assign = QAction(parent)
        self.edit_cut = QAction(parent)
        self.edit_copy = QAction(parent)
        self.edit_copy_colored_html = QAction(parent)
        self.edit_paste = QAction(parent)
        self.edit_select_all = QAction(parent)
        self.edit_select_current_toplevel = QAction(parent)
        self.edit_select_none = QAction(parent)
        self.edit_find = QAction(parent)
        self.edit_find_next = QAction(parent)
        self.edit_find_previous = QAction(parent)
        self.edit_replace = QAction(parent)
        self.edit_preferences = QAction(parent)
        
        self.view_next_document = QAction(parent)
        self.view_previous_document = QAction(parent)
        self.view_document = QAction(parent)
        self.view_highlighting =QAction(parent)
        self.view_highlighting.setCheckable(True)
        self.view_bookmark = QAction(parent)
        self.view_bookmark.setCheckable(True)
        self.view_clear_error_marks = QAction(parent)
        self.view_clear_all_marks = QAction(parent)
        self.view_next_mark = QAction(parent)
        self.view_previous_mark = QAction(parent)
        self.view_scroll_up = QAction(parent)
        self.view_scroll_down = QAction(parent)
        
        self.lilypond_runner = QAction(parent)
        self.lilypond_run_preview = QAction(parent)
        self.lilypond_run_publish = QAction(parent)
        self.lilypond_run_custom = QAction(parent)
        self.lilypond_cancel = QAction(parent)
        
        self.tools_indent_auto = QAction(parent)
        self.tools_indent_auto.setCheckable(True)
        self.tools_indent_indent = QAction(parent)
        
        self.window_new = QAction(parent)
        self.window_fullscreen = QAction(parent)
        self.window_fullscreen.setCheckable(True)
        
        self.help_manual = QAction(parent)
        self.help_whatsthis = QAction(parent)
        self.help_about = QAction(parent)
        self.help_bugreport = QAction(parent)
        
        # icons
        self.file_new.setIcon(icons.get('document-new'))
        self.file_open.setIcon(icons.get('document-open'))
        self.file_open_recent.setIcon(icons.get('document-open-recent'))
        self.file_open_current_directory.setIcon(icons.get('document-open-folder'))
        self.file_save.setIcon(icons.get('document-save'))
        self.file_save_as.setIcon(icons.get('document-save-as'))
        self.file_save_all.setIcon(icons.get('document-save-all'))
        self.file_print_source.setIcon(icons.get('document-print'))
        self.file_print_music.setIcon(icons.get('document-print'))
        self.file_close.setIcon(icons.get('document-close'))
        self.file_quit.setIcon(icons.get('application-exit'))
        
        self.edit_undo.setIcon(icons.get('edit-undo'))
        self.edit_redo.setIcon(icons.get('edit-redo'))
        self.edit_cut_assign.setIcon(icons.get('edit-cut'))
        self.edit_cut.setIcon(icons.get('edit-cut'))
        self.edit_copy.setIcon(icons.get('edit-copy'))
        self.edit_paste.setIcon(icons.get('edit-paste'))
        self.edit_select_all.setIcon(icons.get('edit-select-all'))
        self.edit_select_current_toplevel.setIcon(icons.get('edit-select'))
        self.edit_find.setIcon(icons.get('edit-find'))
        self.edit_find_next.setIcon(icons.get('go-down-search'))
        self.edit_find_previous.setIcon(icons.get('go-up-search'))
        self.edit_replace.setIcon(icons.get('edit-find-replace'))
        self.edit_preferences.setIcon(icons.get('configure'))
        
        self.view_next_document.setIcon(icons.get('go-next'))
        self.view_previous_document.setIcon(icons.get('go-previous'))
        self.view_bookmark.setIcon(icons.get('bookmark-new'))
        
        self.lilypond_runner.setIcon(icons.get('lilypond-run'))
        self.lilypond_run_preview.setIcon(icons.get('lilypond-run'))
        self.lilypond_run_publish.setIcon(icons.get('lilypond-run'))
        self.lilypond_run_custom.setIcon(icons.get('lilypond-run'))
        self.lilypond_cancel.setIcon(icons.get('process-stop'))
        
        self.window_new.setIcon(icons.get('window-new'))
        self.window_fullscreen.setIcon(icons.get('view-fullscreen'))
        
        self.help_manual.setIcon(icons.get('help-contents'))
        self.help_whatsthis.setIcon(icons.get('help-contextual'))
        self.help_bugreport.setIcon(icons.get('tools-report-bug'))
        self.help_about.setIcon(icons.get('help-about'))
        
        # shortcuts
        self.file_new.setShortcuts(QKeySequence.New)
        self.file_open.setShortcuts(QKeySequence.Open)
        self.file_save.setShortcuts(QKeySequence.Save)
        self.file_save_as.setShortcuts(QKeySequence.SaveAs)
        self.file_print_music.setShortcuts(QKeySequence.Print)
        self.file_close.setShortcuts(QKeySequence.Close)
        self.file_quit.setShortcuts(QKeySequence.Quit)
        
        self.edit_undo.setShortcuts(QKeySequence.Undo)
        self.edit_redo.setShortcuts(QKeySequence.Redo)
        self.edit_cut_assign.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_C))
        self.edit_cut.setShortcuts(QKeySequence.Cut)
        self.edit_copy.setShortcuts(QKeySequence.Copy)
        self.edit_paste.setShortcuts(QKeySequence.Paste)
        self.edit_select_all.setShortcuts(QKeySequence.SelectAll)
        self.edit_select_current_toplevel.setShortcut(QKeySequence(Qt.SHIFT+Qt.CTRL+Qt.Key_B))
        self.edit_select_none.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_A))
        self.edit_find.setShortcuts(QKeySequence.Find)
        self.edit_find_next.setShortcuts(QKeySequence.FindNext)
        self.edit_find_previous.setShortcuts(QKeySequence.FindPrevious)
        self.edit_replace.setShortcuts(QKeySequence.Replace)
        self.edit_preferences.setShortcuts(QKeySequence.Preferences)
        
        self.view_next_document.setShortcuts(QKeySequence.Forward)
        self.view_previous_document.setShortcuts(QKeySequence.Back)
        self.view_bookmark.setShortcut(Qt.CTRL + Qt.Key_B)
        self.view_next_mark.setShortcut(Qt.ALT + Qt.Key_PageDown)
        self.view_previous_mark.setShortcut(Qt.ALT + Qt.Key_PageUp)
        self.view_scroll_up.setShortcut(Qt.CTRL + Qt.Key_Up)
        self.view_scroll_down.setShortcut(Qt.CTRL + Qt.Key_Down)
        
        self.lilypond_run_preview.setShortcut(Qt.CTRL + Qt.Key_M)
        self.lilypond_run_publish.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_P)
        self.lilypond_run_custom.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_M)
        
        self.window_fullscreen.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_F)
        
        self.help_manual.setShortcuts(QKeySequence.HelpContents)
        self.help_whatsthis.setShortcuts(QKeySequence.WhatsThis)
        
    def translateUI(self):
        self.file_new.setText(_("&New"))
        self.file_open.setText(_("&Open..."))
        self.file_open_recent.setText(_("Open &Recent"))
        self.file_open_current_directory.setText(_("Open Current Directory"))
        self.file_save.setText(_("&Save"))
        self.file_save_as.setText(_("Save &As..."))
        self.file_save_all.setText(_("Save All"))
        self.file_print_music.setText(_("&Print Music..."))
        self.file_print_source.setText(_("Print Source..."))
        self.file_close.setText(_("&Close"))
        self.file_close_other.setText(_("Close Other Documents"))
        self.file_close_all.setText(_("Close All Documents"))
        self.file_close_all.setToolTip(_("Closes all documents and leaves the current session."))
        self.file_quit.setText(_("&Quit"))
        
        self.export_colored_html.setText(_("Export Source as Colored &HTML..."))
        
        self.edit_undo.setText(_("&Undo"))
        self.edit_redo.setText(_("Re&do"))
        self.edit_cut_assign.setText(_("Cut and Assign..."))
        self.edit_cut.setText(_("Cu&t"))
        self.edit_copy.setText(_("&Copy"))
        self.edit_copy_colored_html.setText(_("Copy as Colored &HTML"))
        self.edit_paste.setText(_("&Paste"))
        self.edit_select_all.setText(_("Select &All"))
        self.edit_select_current_toplevel.setText(_("Select &Block"))
        self.edit_select_none.setText(_("Select &None"))
        self.edit_find.setText(_("&Find..."))
        self.edit_find_next.setText(_("Find Ne&xt"))
        self.edit_find_previous.setText(_("Find Pre&vious"))
        self.edit_replace.setText(_("&Replace..."))
        self.edit_preferences.setText(_("Pr&eferences..."))
        
        self.view_next_document.setText(_("&Next Document"))
        self.view_previous_document.setText(_("&Previous Document"))
        self.view_document.setText(_("&Document"))
        self.view_highlighting.setText(_("Syntax &Highlighting"))
        self.view_bookmark.setText(_("&Mark Current Line"))
        self.view_clear_error_marks.setText(_("Clear &Error Marks"))
        self.view_clear_all_marks.setText(_("Clear &All Marks"))
        self.view_next_mark.setText(_("Next Mark"))
        self.view_previous_mark.setText(_("Previous Mark"))
        self.view_scroll_up.setText(_("Scroll Up"))
        self.view_scroll_down.setText(_("Scroll Down"))
        
        self.lilypond_runner.setText(_("LilyPond"))
        self.lilypond_run_preview.setText(_("Run &LilyPond (preview)"))
        self.lilypond_run_publish.setText(_("Run LilyPond (&publish)"))
        self.lilypond_run_custom.setText(_("Run LilyPond (&custom)"))
        self.lilypond_cancel.setText(_("Interrupt LilyPond &Job"))
        
        self.tools_indent_auto.setText(_("&Automatic Indent"))
        self.tools_indent_indent.setText(_("Re-&Indent"))
        
        self.window_new.setText(_("New &Window"))
        self.window_fullscreen.setText(_("&Fullscreen"))
        
        self.help_manual.setText(_("&User Guide"))
        self.help_whatsthis.setText(_("&What's This?"))
        self.help_bugreport.setText(_("Report a &Bug..."))
        self.help_about.setText(_("&About {name}").format(name=info.appname))
        

