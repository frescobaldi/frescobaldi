# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Frescobaldi Main Window.
"""

from __future__ import unicode_literals

import itertools
import os
import sys
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import backup
import info
import icons
import actioncollection
import actioncollectionmanager
import menu
import tabbar
import document
import view
import viewmanager
import highlighter
import historymanager
import recentfiles
import sessions.manager
import util
import qutil
import helpers
import panelmanager
import engrave
import scorewiz
import externalchanges


class MainWindow(QMainWindow):
    
    # emitted when the MainWindow will close
    aboutToClose = pyqtSignal()
    
    # only emitted when this is the last MainWindow to close
    aboutToCloseLast = pyqtSignal()
    
    # both signals emit (current, previous)
    currentDocumentChanged = pyqtSignal(document.Document, document.Document)
    currentViewChanged = pyqtSignal(view.View, view.View)
    
    # emitted when whether there is a selection changes
    selectionStateChanged = pyqtSignal(bool)
    
    def __init__(self, other=None):
        """Creates a new MainWindow.
        
        It adds itself to app.windows to keep a reference.
        It shares the documents list with all other MainWindows. It copies
        some info (like the currently active document) from the 'other' window,
        if given.
        
        """
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # this could be made configurable
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
        self._currentDocument = None
        self._currentView = lambda: None
        self._selectedState = None
        
        # find an unused objectName
        names = set(win.objectName() for win in app.windows)
        for num in itertools.count(1):
            name = "MainWindow{0}".format(num)
            if name not in names:
                self.setObjectName(name)
                break
        
        app.windows.append(self)
        
        mainwidget = QWidget()
        self.setCentralWidget(mainwidget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        mainwidget.setLayout(layout)
        self.tabBar = tabbar.TabBar(self)
        self.viewManager = viewmanager.ViewManager(self)
        layout.addWidget(self.tabBar)
        layout.addWidget(self.viewManager)

        self.createActions()
        self.createMenus()
        self.createToolBars()
        
        app.translateUI(self)
        app.sessionChanged.connect(self.updateWindowTitle)
        
        self.readSettings()
        
        self.historyManager = historymanager.HistoryManager(self, other.historyManager if other else None)
        self.viewManager.viewChanged.connect(self.slotViewChanged)
        self.tabBar.currentDocumentChanged.connect(self.setCurrentDocument)
        self.setAcceptDrops(True)
        
        # keep track of all ActionCollections for the keyboard settings dialog
        actioncollectionmanager.manager(self).addActionCollection(self.actionCollection)
        actioncollectionmanager.manager(self).addActionCollection(self.viewManager.actionCollection)
        
        if other:
            self.setCurrentDocument(other.currentDocument())
        app.mainwindowCreated(self)
        
    def documents(self):
        """Returns the list of documents in the order of the TabBar."""
        return self.tabBar.documents()
        
    def currentView(self):
        """Returns the current View or None."""
        return self._currentView()
    
    def currentDocument(self):
        """Returns the current Document or None."""
        return self._currentDocument
        
    def setCurrentDocument(self, doc, findOpenView=None):
        """Set the current document.
        
        The findOpenView argument makes sense when the user has split the
        editor view in more than one.  If findOpenView == True and one of the
        views has the document, that view is focused. If findOpenView == False,
        the currently focused view is changed to the document. If findOpenView
        is None, the users setting is read.
        
        """
        if findOpenView is None:
            findOpenView = QSettings().value("mainwindow/find_open_view", True, bool)
        self.viewManager.setCurrentDocument(doc, findOpenView)
    
    def hasSelection(self):
        """Returns whether there is a selection."""
        return self.textCursor().hasSelection() if self.currentView() else False
            
    def textCursor(self):
        """Returns the QTextCursor of the current View.
        
        Raises an error if there is not yet a view.
        
        """
        return self.currentView().textCursor()
        
    def setTextCursor(self, cursor, findOpenView=None):
        """Switch to the cursor's document() and set that cursor on its View.
        
        For the findOpenView argument, see setCurrentDocument().
        
        """
        self.setCurrentDocument(cursor.document(), findOpenView)
        self.currentView().setTextCursor(cursor)
    
    def slotViewChanged(self, view):
        curv = self._currentView()
        if curv:
            if curv is view:
                return
            curv.copyAvailable.disconnect(self.updateSelection)
            curv.selectionChanged.disconnect(self.updateSelection)
        view.copyAvailable.connect(self.updateSelection)
        view.selectionChanged.connect(self.updateSelection)
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
            doc.undoAvailable.connect(self.updateDocActions)
            doc.redoAvailable.connect(self.updateDocActions)
            doc.modificationChanged.connect(self.updateWindowTitle)
            doc.urlChanged.connect(self.updateWindowTitle)
            doc.loaded.connect(self.updateDocActions)
            self.updateDocActions()
            self.updateWindowTitle()
        self.updateSelection()
        self.currentViewChanged.emit(view, curv)
        if curd is not doc:
            self.currentDocumentChanged.emit(doc, curd)
    
    def updateSelection(self):
        selection = self.textCursor().hasSelection()
        if selection != self._selectedState:
            self._selectedState = selection
            self.selectionStateChanged.emit(selection)
            ac = self.actionCollection
            ac.edit_copy.setEnabled(selection)
            ac.edit_copy_colored_html.setEnabled(selection)
            ac.edit_cut.setEnabled(selection)
            ac.edit_select_none.setEnabled(selection)
    
    def updateDocActions(self):
        doc = self.currentDocument()
        ac = self.actionCollection
        ac.edit_undo.setEnabled(doc.isUndoAvailable())
        ac.edit_redo.setEnabled(doc.isRedoAvailable())
        
    def updateWindowTitle(self):
        doc = self.currentDocument()
        name = []
        if sessions.currentSession():
            name.append(sessions.currentSession() + ':')
        if doc:
            if doc.url().isEmpty():
                name.append(doc.documentName())
            elif doc.url().toLocalFile():
                name.append(util.homify(doc.url().toLocalFile()))
            else:
                name.append(doc.url().toString())
            if doc.isModified():
                # L10N: state of document in window titlebar
                name.append(_("[modified]"))
        self.setWindowTitle(app.caption(" ".join(name)))
    
    def dropEvent(self, ev):
        if not ev.source() and ev.mimeData().hasUrls():
            ev.accept()
            docs = [self.openUrl(url) for url in ev.mimeData().urls()]
            if docs:
                self.setCurrentDocument(docs[-1])
        
    def dragEnterEvent(self, ev):
        if not ev.source() and ev.mimeData().hasUrls():
            ev.accept()
        
    def closeEvent(self, ev):
        lastWindow = len(app.windows) == 1
        if not lastWindow or self.queryClose():
            self.aboutToClose.emit()
            if lastWindow:
                self.writeSettings()
                self.aboutToCloseLast.emit()
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
        sessions.manager.get(self).saveCurrentSessionIfDesired()
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
        res = QMessageBox.warning(self, _("dialog title", "Close Document"),
            _("The document \"{name}\" has been modified.\n"
            "Do you want to save your changes or discard them?").format(name=doc.documentName()),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if res == QMessageBox.Save:
            return self.saveDocument(doc)
        else:
            return res == QMessageBox.Discard
        
    def createPopupMenu(self):
        """ Adds an entry to the popup menu to show/hide the tab bar. """
        menu = QMainWindow.createPopupMenu(self)
        menu.addSeparator()
        a = menu.addAction(_("Tab Bar"))
        a.setCheckable(True)
        a.setChecked(self.tabBar.isVisible())
        a.toggled.connect(self.tabBar.setVisible)
        return menu
        
    def readSettings(self):
        """ Read a few settings from the application global config. """
        settings = QSettings()
        settings.beginGroup('mainwindow')
        defaultSize = QApplication.desktop().screen().size() * 2 / 3
        self.resize(settings.value("size", defaultSize, QSize))
        self.restoreState(settings.value('state', QByteArray(), QByteArray))
        self.tabBar.setVisible(settings.value('tabbar', True, bool))
        if os.name != "posix" and settings.value('maximized', False, bool):
            self.showMaximized()
        
    def writeSettings(self):
        """ Write a few settings to the application global config. """
        settings = QSettings()
        settings.beginGroup('mainwindow')
        if not self.isFullScreen():
            settings.setValue("size", self.size())
        settings.setValue('state', self.saveState())
        settings.setValue('tabbar', self.tabBar.isVisible())
        settings.setValue('maximized', self.isMaximized())
    
    def readSessionSettings(self, settings):
        """Restore ourselves from session manager settings.
        
        These methods store much more information than the readSettings and
        writeSettings methods. This method tries to restore window size and
        position. Also the objectName() is set, so that the window manager can
        preserve stacking order, etc.
        
        """
        name = settings.value('name', '', type(""))
        if name:
            self.setObjectName(name)
        self.restoreGeometry(settings.value('geometry', QByteArray(), QByteArray))
        self.restoreState(settings.value('state', QByteArray(), QByteArray))
        
    def writeSessionSettings(self, settings):
        """Write our state to the session manager settings.
        
        See readSessionSettings().
        
        """
        settings.setValue('name', self.objectName())
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('state', self.saveState())

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
    
    def currentDirectory(self):
        """Returns the current directory of the current document.
        
        If the document has no filename yet, returns the configured default
        directory, or the user's home directory.
        Is that is not set as well, returns the current directory
        of the application.
        
        """
        import resultfiles
        return (resultfiles.results(self.currentDocument()).currentDirectory()
                or app.basedir() or QDir.homePath() or os.getcwdu())
    
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
        caption = app.caption(_("dialog title", "Open File"))
        directory = os.path.dirname(self.currentDocument().url().toLocalFile()) or app.basedir()
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
        b = backup.backup(filename)
        success = doc.save()
        if not success:
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}").format(url=filename))
        elif b:
            backup.removeBackup(filename)
        return success
            
    def saveDocumentAs(self, doc):
        """ Saves the document, always asking for a name.
        
        Returns True if saving succeeded.
        
        """
        filename = doc.url().toLocalFile()
        if filename:
            filetypes = app.filetypes(os.path.splitext(filename)[1])
        else:
            filename = app.basedir() # default directory to save to
            import documentinfo
            import ly.lex
            filetypes = app.filetypes(ly.lex.extensions[documentinfo.mode(doc)])
        caption = app.caption(_("dialog title", "Save File"))
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
                self.setCurrentDocument(document.Document())
        return close
        
    def saveCurrentDocument(self):
        return self.saveDocument(self.currentDocument())
    
    def saveCurrentDocumentAs(self):
        return self.saveDocumentAs(self.currentDocument())
    
    def saveCopyAs(self):
        import ly.lex
        doc = self.currentDocument()
        if not self.currentView().textCursor().hasSelection():
            import documentinfo
            mode = documentinfo.mode(doc)
            data = doc.encodedText()
            caption = app.caption(_("dialog title", "Save Copy"))
        else:
            import fileinfo
            text = self.currentView().textCursor().selection().toPlainText()
            mode = fileinfo.textmode(text)
            data = util.encode(text)
            caption = app.caption(_("dialog title", "Save Selection"))
        filetypes = app.filetypes(ly.lex.extensions[mode])
        dirname = os.path.dirname(doc.url().toLocalFile()) or app.basedir()
        filename = QFileDialog.getSaveFileName(self, caption, dirname, filetypes)
        if not filename:
            return # cancelled
        try:
            with open(filename, "w") as f:
                f.write(data)
        except (IOError, OSError) as err:
            QMessageBox.warning(self, app.caption(_("Error")),
                _("Can't write to destination:\n\n{url}\n\n{error}").format(
                    url=filename, error=err.strerror))
    
    def closeCurrentDocument(self):
        return self.closeDocument(self.currentDocument())
    
    def reloadCurrentDocument(self):
        """Reload the current document again from disk.
        
        This action can be undone.
        
        """
        d = self.currentDocument()
        if d.load(True) is False:
            QMessageBox.warning(self, app.caption(_("Reload")),
              _("Could not reload the document:\n\n{url}").format(
                url = d.url().toString()))
    
    def reloadAllDocuments(self):
        """Reloads all documents."""
        success = []
        for d in self.historyManager.documents():
            success.append(d.load(True))
        if False in success:
            if True in success:
                msg = _("Some documents could not be reloaded.")
            else:
                msg = _("No document could be reloaded.")
            QMessageBox.warning(self, app.caption(_("Reload")), msg)
    
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
        sessions.manager.get(self).saveCurrentSessionIfDesired()
        if self.queryClose():
            sessions.setCurrentSession(None)
            self.setCurrentDocument(document.Document())
    
    def endProgram(self):
        """Closes all MainWindows."""
        for window in app.windows[:]: # copy
            if window is not self:
                window.close()
        self.close()
    
    def quit(self):
        app.qApp.restart = False
        self.endProgram()
        
    def restart(self):
        app.qApp.restart = True
        self.endProgram()
    
    def insertFromFile(self):
        ext = os.path.splitext(self.currentDocument().url().path())[1]
        filetypes = app.filetypes(ext)
        caption = app.caption(_("dialog title", "Insert From File"))
        directory = os.path.dirname(self.currentDocument().url().toLocalFile()) or app.basedir()
        filename = QFileDialog.getOpenFileName(self, caption, directory, filetypes)
        if filename:
            try:
                data = open(filename).read()
            except (IOError, OSError) as err:
                QMessageBox.warning(self, app.caption(_("Error")),
                    _("Can't read from source:\n\n{url}\n\n{error}").format(
                        url=filename, error=err.strerror))
            else:
                text = util.decode(data)
                self.currentView().textCursor().insertText(text)
        
    def openCurrentDirectory(self):
        helpers.openUrl(QUrl.fromLocalFile(self.currentDirectory()), "directory")
    
    def openCommandPrompt(self):
        helpers.openUrl(QUrl.fromLocalFile(self.currentDirectory()), "shell")
    
    def printSource(self):
        cursor = self.currentView().textCursor()
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle(app.caption(_("dialog title", "Print Source")))
        options = QAbstractPrintDialog.PrintToFile | QAbstractPrintDialog.PrintShowPageSize
        if cursor.hasSelection():
            options |= QAbstractPrintDialog.PrintSelection
        dlg.setOptions(options)
        if dlg.exec_():
            doc = highlighter.htmlCopy(self.currentDocument(), 'printer')
            doc.setMetaInformation(QTextDocument.DocumentTitle, self.currentDocument().url().toString())
            font = doc.defaultFont()
            font.setPointSizeF(font.pointSizeF() * 0.8)
            doc.setDefaultFont(font)
            if dlg.testOption(QAbstractPrintDialog.PrintSelection):
                # cut out not selected text
                start, end = cursor.selectionStart(), cursor.selectionEnd()
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
        import highlight2html
        html = highlight2html.HtmlHighlighter().html_document(doc)
        try:
            with open(filename, "wb") as f:
                f.write(html.encode('utf-8'))
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
        import highlight2html
        h = highlight2html.HtmlHighlighter(inline_style=True)
        html = h.html_selection(cursor)
        data = QMimeData()
        data.setHtml(html)
        #data.setText(html)
        QApplication.clipboard().setMimeData(data)
        
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
        self.writeSettings()
        MainWindow(self).show()

    def scrollUp(self):
        """Scroll up without moving the cursor"""
        sb = self.currentView().verticalScrollBar()
        sb.setValue(sb.value() - 1 if sb.value() else 0)
        
    def scrollDown(self):
        """Scroll down without moving the cursor"""
        sb = self.currentView().verticalScrollBar()
        sb.setValue(sb.value() + 1)
        
    def selectFullLinesUp(self):
        """Select lines upwards, selecting full lines."""
        self.selectFullLines(QTextCursor.Up)
        
    def selectFullLinesDown(self):
        """Select lines downwards, selecting full lines."""
        self.selectFullLines(QTextCursor.Down)
        
    def selectFullLines(self, direction):
        """Select full lines in the direction QTextCursor.Up or Down."""
        view = self.currentView()
        cur = view.textCursor()
        position = cur.position()
        cur.setPosition(cur.anchor())
        cur.movePosition(QTextCursor.StartOfLine)
        cur.setPosition(position, QTextCursor.KeepAnchor)
        cur.movePosition(direction, QTextCursor.KeepAnchor)
        cur.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        view.setTextCursor(cur)
    
    def showManual(self):
        """Shows the user guide, called when user presses F1."""
        import help
        help.help("contents")
    
    def showAbout(self):
        """Shows about dialog."""
        import about
        about.AboutDialog(self).exec_()
    
    def reportBug(self):
        """Opens e-mail composer to send a bug or feature report."""
        import bugreport
        bugreport.email('', _(
            "Please describe the issue or feature request.\n"
            "Provide as much information as possible.\n\n\n"))
    
    def createActions(self):
        self.actionCollection = ac = ActionCollection()
        
        # recent files
        self.menu_recent_files = m = QMenu()
        ac.file_open_recent.setMenu(m)
        m.aboutToShow.connect(self.populateRecentFilesMenu)
        m.triggered.connect(self.slotRecentFilesAction)
        
        # connections
        ac.file_quit.triggered.connect(self.quit, Qt.QueuedConnection)
        ac.file_restart.triggered.connect(self.restart, Qt.QueuedConnection)
        ac.file_new.triggered.connect(self.newDocument)
        ac.file_open.triggered.connect(self.openDocument)
        ac.file_insert_file.triggered.connect(self.insertFromFile)
        ac.file_open_current_directory.triggered.connect(self.openCurrentDirectory)
        ac.file_open_command_prompt.triggered.connect(self.openCommandPrompt)
        ac.file_save.triggered.connect(self.saveCurrentDocument)
        ac.file_save_as.triggered.connect(self.saveCurrentDocumentAs)
        ac.file_save_copy_as.triggered.connect(self.saveCopyAs)
        ac.file_save_all.triggered.connect(self.saveAllDocuments)
        ac.file_reload.triggered.connect(self.reloadCurrentDocument)
        ac.file_reload_all.triggered.connect(self.reloadAllDocuments)
        ac.file_external_changes.triggered.connect(externalchanges.displayChangedDocuments)
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
        ac.edit_select_full_lines_up.triggered.connect(self.selectFullLinesUp)
        ac.edit_select_full_lines_down.triggered.connect(self.selectFullLinesDown)
        ac.edit_find.triggered.connect(self.find)
        ac.edit_replace.triggered.connect(self.replace)
        ac.edit_preferences.triggered.connect(self.showPreferences)
        ac.view_next_document.triggered.connect(self.tabBar.nextDocument)
        ac.view_previous_document.triggered.connect(self.tabBar.previousDocument)
        ac.view_scroll_up.triggered.connect(self.scrollUp)
        ac.view_scroll_down.triggered.connect(self.scrollDown)
        ac.window_new.triggered.connect(self.newWindow)
        ac.window_fullscreen.toggled.connect(self.toggleFullScreen)
        ac.help_manual.triggered.connect(self.showManual)
        ac.help_about.triggered.connect(self.showAbout)
        ac.help_bugreport.triggered.connect(self.reportBug)
        
    def populateRecentFilesMenu(self):
        self.menu_recent_files.clear()
        for url in recentfiles.urls():
            f = url.toLocalFile()
            dirname, basename = os.path.split(f)
            text = "{0}  ({1})".format(basename, util.homify(dirname))
            self.menu_recent_files.addAction(text).url = url
        qutil.addAccelerators(self.menu_recent_files.actions())
    
    def slotRecentFilesAction(self, action):
        """Called when a recent files menu action is triggered."""
        doc = self.openUrl(action.url)
        self.setCurrentDocument(doc)
        
    def createMenus(self):
        menu.createMenus(self)
        # actions that are not in menus
        ac = self.actionCollection
        self.addAction(ac.view_scroll_up)
        self.addAction(ac.view_scroll_down)
        self.addAction(ac.edit_select_full_lines_up)
        self.addAction(ac.edit_select_full_lines_down)
        
    def createToolBars(self):
        ac = self.actionCollection
        self.toolbar_main = t = self.addToolBar('')
        t.setObjectName('toolbar_main')
        t.addAction(ac.file_new)
        t.addAction(ac.file_open)
        t.addSeparator()
        t.addAction(ac.file_save)
        t.addAction(ac.file_save_as)
        t.addSeparator()
        t.addAction(ac.file_close)
        t.addSeparator()
        t.addAction(ac.edit_undo)
        t.addAction(ac.edit_redo)
        t.addSeparator()
        t.addAction(scorewiz.ScoreWizard.instance(self).actionCollection.scorewiz)
        t.addAction(engrave.engraver(self).actionCollection.engrave_runner)
        
        self.toolbar_music = t = self.addToolBar('')
        t.setObjectName('toolbar_music')
        ma = panelmanager.manager(self).musicview.actionCollection
        t.addAction(ma.music_document_select)
        t.addAction(ma.music_print)
        t.addSeparator()
        t.addAction(ma.music_zoom_in)
        t.addAction(ma.music_zoom_combo)
        t.addAction(ma.music_zoom_out)
        t.addSeparator()
        t.addAction(ma.music_prev_page)
        t.addAction(ma.music_pager)
        t.addAction(ma.music_next_page)
        
    def translateUI(self):
        self.toolbar_main.setWindowTitle(_("Main Toolbar"))
        self.toolbar_music.setWindowTitle(_("Music View Toolbar"))


class ActionCollection(actioncollection.ActionCollection):
    name = "main"
    def createActions(self, parent=None):
        self.file_new = QAction(parent)
        self.file_open = QAction(parent)
        self.file_open_recent = QAction(parent)
        self.file_insert_file = QAction(parent)
        self.file_open_current_directory = QAction(parent)
        self.file_open_command_prompt = QAction(parent)
        self.file_save = QAction(parent)
        self.file_save_as = QAction(parent)
        self.file_save_copy_as = QAction(parent)
        self.file_save_all = QAction(parent)
        self.file_reload = QAction(parent)
        self.file_reload_all = QAction(parent)
        self.file_external_changes = QAction(parent)
        self.file_print_source = QAction(parent)
        self.file_close = QAction(parent)
        self.file_close_other = QAction(parent)
        self.file_close_all = QAction(parent)
        self.file_quit = QAction(parent)
        self.file_restart = QAction(parent)
        
        self.export_colored_html = QAction(parent)
        
        self.edit_undo = QAction(parent)
        self.edit_redo = QAction(parent)
        self.edit_cut = QAction(parent)
        self.edit_copy = QAction(parent)
        self.edit_copy_colored_html = QAction(parent)
        self.edit_paste = QAction(parent)
        self.edit_select_all = QAction(parent)
        self.edit_select_current_toplevel = QAction(parent)
        self.edit_select_none = QAction(parent)
        self.edit_select_full_lines_up = QAction(parent)
        self.edit_select_full_lines_down = QAction(parent)
        self.edit_find = QAction(parent)
        self.edit_find_next = QAction(parent)
        self.edit_find_previous = QAction(parent)
        self.edit_replace = QAction(parent)
        self.edit_preferences = QAction(parent)
        
        self.view_next_document = QAction(parent)
        self.view_previous_document = QAction(parent)
        self.view_scroll_up = QAction(parent)
        self.view_scroll_down = QAction(parent)
        
        self.window_new = QAction(parent)
        self.window_fullscreen = QAction(parent)
        self.window_fullscreen.setCheckable(True)
        
        self.help_manual = QAction(parent)
        self.help_whatsthis = QWhatsThis.createAction(parent)
        self.help_about = QAction(parent)
        self.help_bugreport = QAction(parent)
        
        # icons
        self.file_new.setIcon(icons.get('document-new'))
        self.file_open.setIcon(icons.get('document-open'))
        self.file_open_recent.setIcon(icons.get('document-open-recent'))
        self.file_open_current_directory.setIcon(icons.get('folder-open'))
        self.file_open_command_prompt.setIcon(icons.get('utilities-terminal'))
        self.file_save.setIcon(icons.get('document-save'))
        self.file_save_as.setIcon(icons.get('document-save-as'))
        self.file_save_copy_as.setIcon(icons.get('document-save-as'))
        self.file_save_all.setIcon(icons.get('document-save-all'))
        self.file_reload.setIcon(icons.get('reload'))
        self.file_reload_all.setIcon(icons.get('reload-all'))
        self.file_print_source.setIcon(icons.get('document-print'))
        self.file_close.setIcon(icons.get('document-close'))
        self.file_quit.setIcon(icons.get('application-exit'))
        
        self.edit_undo.setIcon(icons.get('edit-undo'))
        self.edit_redo.setIcon(icons.get('edit-redo'))
        self.edit_cut.setIcon(icons.get('edit-cut'))
        self.edit_copy.setIcon(icons.get('edit-copy'))
        self.edit_paste.setIcon(icons.get('edit-paste'))
        self.edit_select_all.setIcon(icons.get('edit-select-all'))
        self.edit_select_current_toplevel.setIcon(icons.get('edit-select'))
        self.edit_find.setIcon(icons.get('edit-find'))
        self.edit_find_next.setIcon(icons.get('go-down-search'))
        self.edit_find_previous.setIcon(icons.get('go-up-search'))
        self.edit_replace.setIcon(icons.get('edit-find-replace'))
        self.edit_preferences.setIcon(icons.get('preferences-system'))
        
        self.view_next_document.setIcon(icons.get('go-next'))
        self.view_previous_document.setIcon(icons.get('go-previous'))
        
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
        self.file_close.setShortcuts(QKeySequence.Close)
        self.file_quit.setShortcuts(QKeySequence.Quit)
        
        self.edit_undo.setShortcuts(QKeySequence.Undo)
        self.edit_redo.setShortcuts(QKeySequence.Redo)
        self.edit_cut.setShortcuts(QKeySequence.Cut)
        self.edit_copy.setShortcuts(QKeySequence.Copy)
        self.edit_paste.setShortcuts(QKeySequence.Paste)
        self.edit_select_all.setShortcuts(QKeySequence.SelectAll)
        self.edit_select_current_toplevel.setShortcut(QKeySequence(Qt.SHIFT+Qt.CTRL+Qt.Key_B))
        self.edit_select_none.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_A))
        self.edit_select_full_lines_up.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_Up))
        self.edit_select_full_lines_down.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_Down))
        self.edit_find.setShortcuts(QKeySequence.Find)
        self.edit_find_next.setShortcuts(QKeySequence.FindNext)
        self.edit_find_previous.setShortcuts(QKeySequence.FindPrevious)
        self.edit_replace.setShortcuts(QKeySequence.Replace)
        self.edit_preferences.setShortcuts(QKeySequence.Preferences)
        
        self.view_next_document.setShortcuts(QKeySequence.Forward)
        self.view_previous_document.setShortcuts(QKeySequence.Back)
        self.view_scroll_up.setShortcut(Qt.CTRL + Qt.Key_Up)
        self.view_scroll_down.setShortcut(Qt.CTRL + Qt.Key_Down)
        
        self.window_fullscreen.setShortcuts([QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_F), QKeySequence(Qt.Key_F11)])
        
        self.help_manual.setShortcuts(QKeySequence.HelpContents)
        
        # roles
        if sys.platform.startswith('darwin'):
            if '.app/Contents/MacOS' in os.path.abspath(os.path.dirname(sys.argv[0])):
                self.file_quit.setMenuRole(QAction.QuitRole)
                self.edit_preferences.setMenuRole(QAction.PreferencesRole)
                self.help_about.setMenuRole(QAction.AboutRole)
            else:
                self.file_quit.setMenuRole(QAction.NoRole)
                self.edit_preferences.setMenuRole(QAction.NoRole)
                self.help_about.setMenuRole(QAction.NoRole)
        
    def translateUI(self):
        self.file_new.setText(_("action: new document", "&New"))
        self.file_open.setText(_("&Open..."))
        self.file_open_recent.setText(_("Open &Recent"))
        self.file_insert_file.setText(_("Insert from &File..."))
        self.file_open_current_directory.setText(_("Open Current Directory"))
        self.file_open_command_prompt.setText(_("Open Command Prompt"))
        self.file_save.setText(_("&Save"))
        self.file_save_as.setText(_("Save &As..."))
        self.file_save_copy_as.setText(_("Save Copy or Selection As..."))
        self.file_save_all.setText(_("Save All"))
        self.file_reload.setText(_("Re&load"))
        self.file_reload_all.setText(_("Reload All"))
        self.file_external_changes.setText(_("Check for External Changes..."))
        self.file_external_changes.setToolTip(_(
            "Opens a window to check whether open documents were changed or "
            "deleted by other programs."))
        self.file_print_source.setText(_("Print Source..."))
        self.file_close.setText(_("&Close"))
        self.file_close_other.setText(_("Close Other Documents"))
        self.file_close_all.setText(_("Close All Documents"))
        self.file_close_all.setToolTip(_("Closes all documents and leaves the current session."))
        self.file_quit.setText(_("&Quit"))
        self.file_restart.setText(_("Restart Frescobaldi"))
        
        self.export_colored_html.setText(_("Export Source as Colored &HTML..."))
        
        self.edit_undo.setText(_("&Undo"))
        self.edit_redo.setText(_("Re&do"))
        self.edit_cut.setText(_("Cu&t"))
        self.edit_copy.setText(_("&Copy"))
        self.edit_copy_colored_html.setText(_("Copy as Colored &HTML"))
        self.edit_paste.setText(_("&Paste"))
        self.edit_select_all.setText(_("Select &All"))
        self.edit_select_current_toplevel.setText(_("Select &Block"))
        self.edit_select_none.setText(_("Select &None"))
        self.edit_select_full_lines_up.setText(_("Select Whole Lines Up"))
        self.edit_select_full_lines_down.setText(_("Select Whole Lines Down"))
        self.edit_find.setText(_("&Find..."))
        self.edit_find_next.setText(_("Find Ne&xt"))
        self.edit_find_previous.setText(_("Find Pre&vious"))
        self.edit_replace.setText(_("&Replace..."))
        self.edit_preferences.setText(_("Pr&eferences..."))
        
        self.view_next_document.setText(_("&Next Document"))
        self.view_previous_document.setText(_("&Previous Document"))
        self.view_scroll_up.setText(_("Scroll Up"))
        self.view_scroll_down.setText(_("Scroll Down"))
        
        self.window_new.setText(_("New &Window"))
        self.window_fullscreen.setText(_("&Fullscreen"))
        
        self.help_manual.setText(_("&User Guide"))
        self.help_whatsthis.setText(_("&What's This?"))
        self.help_bugreport.setText(_("Report a &Bug..."))
        self.help_about.setText(_("&About {appname}...").format(appname=info.appname))
        

