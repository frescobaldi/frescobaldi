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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import info
import icons
import actioncollection
import document
import viewmanager


class MainWindow(QMainWindow):
    
    currentDocumentChanged = pyqtSignal(document.Document)
    
    def __init__(self, other=None):
        """Creates a new MainWindow.
        
        It adds itself to app.windows to keep a reference.
        It shares the documents list with all other MainWindows. It copies
        some info (like the currently active document) from the 'other' window,
        if given.
        
        """
        QMainWindow.__init__(self)
        
        self._currentDocument = None
        self._currentView = None
        
        # find an unused objectName
        names = set(win.objectName() for win in app.windows)
        for num in itertools.count(1):
            name = "MainWindow{0}".format(num)
            if name not in names:
                self.setObjectName(name)
                break
        
        self.setWindowIcon(icons.get('frescobaldi'))
        app.windows.append(self)
        
        self.createActions()
        
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

        # create other stuff that have their own actions
        
        self.createMenus()
        self.createToolBars()
        
        self.translateUI()
        app.languageChanged.connect(self.translateUI)
        
        self.readSettings()
        
        self.viewManager.viewChanged.connect(self.slotViewChanged)
        self.tabBar.currentDocumentChanged.connect(self.setCurrentDocument)
        
        #TEMP
        import document
        self.setCurrentDocument(document.Document())
        document.Document()
        
    def slotViewChanged(self, view):
        cur = self._currentView
        if cur:
            if cur is view:
                return
            cur.copyAvailable.disconnect(self.updateViewActions)
            cur.selectionChanged.disconnect(self.updateViewActions)
        view.copyAvailable.connect(self.updateViewActions)
        view.selectionChanged.connect(self.updateViewActions)
        self._currentView = view
        self.updateViewActions()
        self.setCurrentDocument(view.document())
    
    def currentView(self):
        return self._currentView
        
    def currentDocument(self):
        return self._currentDocument
        
    def setCurrentDocument(self, doc, findOpenView=False):
        cur = self._currentDocument
        if cur:
            if cur is doc:
                return
            cur.undoAvailable.disconnect(self.updateDocActions)
            cur.redoAvailable.disconnect(self.updateDocActions)
            cur.modificationChanged.disconnect(self.updateDocStatus)
        doc.undoAvailable.connect(self.updateDocActions)
        doc.redoAvailable.connect(self.updateDocActions)
        doc.modificationChanged.connect(self.updateDocStatus)
        self._currentDocument = doc
        self.updateDocActions()
        self.updateDocStatus()
        self.currentDocumentChanged.emit(doc)
        self.viewManager.showDocument(doc, findOpenView)

    def updateViewActions(self):
        view = self._currentView
        ac = self.actionCollection
        selection = view.textCursor().hasSelection()
        ac.edit_copy.setEnabled(selection)
        ac.edit_cut.setEnabled(selection)
        ac.edit_cut_assign.setEnabled(selection)
        ac.edit_select_none.setEnabled(selection)
    
    def updateDocActions(self):
        doc = self._currentDocument
        ac = self.actionCollection
        ac.edit_undo.setEnabled(doc.isUndoAvailable())
        ac.edit_redo.setEnabled(doc.isRedoAvailable())
        
    def updateDocStatus(self):
        doc = self._currentDocument
        #TEMP
        if doc.isModified():
            self.setWindowTitle("modified")
        else:
            self.setWindowTitle("not modified")
        
    def closeEvent(self, ev):
        lastWindow = len(app.windows) == 1
        if not lastWindow or self.queryClose():
            ev.accept()
            app.windows.remove(self)
            if lastWindow:
                self.writeSettings()
        else:
            ev.ignore()

    def queryClose(self):
        return True

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

    def toggleFullScreen(self, enabled):
        if enabled:
            self._maximized = self.isMaximized()
            self.showFullScreen()
        else:
            self.showNormal()
            if self._maximized:
                self.showMaximized()
    
    def selectNone(self):
        cursor = self.currentView().textCursor()
        cursor.clearSelection()
        self.currentView().setTextCursor(cursor)
        
    def createActions(self):
        self.actionCollection = ac = ActionCollection(self)
        
        # recent files
        self.menu_recent_files = m = QMenu()
        ac.file_open_recent.setMenu(m)
        
        # documents submenu
        self.menu_documents = m = QMenu()
        ac.view_document.setMenu(m)
        
        # connections
        ac.file_quit.triggered.connect(self.close)
        ac.edit_undo.triggered.connect(lambda: self.currentDocument().undo())
        ac.edit_redo.triggered.connect(lambda: self.currentDocument().redo())
        ac.edit_select_all.triggered.connect(lambda: self.currentView().selectAll())
        ac.edit_select_none.triggered.connect(self.selectNone)
        ac.window_new.triggered.connect(lambda: MainWindow(self).show())
        ac.window_fullscreen.toggled.connect(self.toggleFullScreen)
        ac.help_whatsthis.triggered.connect(QWhatsThis.enterWhatsThisMode)
        
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
        m.addSeparator()
        m.addAction(ac.file_close)
        m.addAction(ac.file_close_other)
        m.addSeparator()
        m.addAction(ac.file_quit)
        
        self.menu_edit = m = self.menuBar().addMenu('')
        m.addAction(ac.edit_undo)
        m.addAction(ac.edit_redo)
        m.addSeparator()
        m.addAction(ac.edit_cut_assign)
        m.addAction(ac.edit_cut)
        m.addAction(ac.edit_copy)
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
        m.addAction(ac.view_bookmark)
        m.addAction(ac.view_clear_error_marks)
        m.addAction(ac.view_clear_all_marks)
        
        self.menu_lilypond = m = self.menuBar().addMenu('')
        m.addAction(ac.lilypond_run_preview)
        m.addAction(ac.lilypond_run_publish)
        m.addAction(ac.lilypond_run_custom)
        m.addAction(ac.lilypond_cancel)
        
        self.menu_tools = m = self.menuBar().addMenu('')
        
        self.menu_window = m = self.menuBar().addMenu('')
        vm = self.viewManager.actionCollection
        m.addAction(ac.window_new)
        m.addSeparator()
        m.addAction(vm.window_split_horizontal)
        m.addAction(vm.window_split_vertical)
        m.addAction(vm.window_close_view)
        m.addAction(vm.window_next_view)
        m.addAction(vm.window_previous_view)
        m.addSeparator()
        m.addAction(ac.window_fullscreen)
        
        self.menu_sessions = m = self.menuBar().addMenu('')
        m.addAction(ac.session_new)
        m.addAction(ac.session_save)
        m.addSeparator()
        m.addAction(ac.session_manage)
        m.addSeparator()
        m.addAction(ac.session_none)
        
        self.menu_help = m = self.menuBar().addMenu('')
        m.addAction(ac.help_manual)
        m.addAction(ac.help_whatsthis)
        m.addSeparator()
        m.addAction(ac.help_bugreport)
        m.addSeparator()
        m.addAction(ac.help_about)
        
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
        self.actionCollection.translateUI()
        self.menu_file.setTitle(_('&File'))
        self.menu_edit.setTitle(_('&Edit'))
        self.menu_view.setTitle(_('&View'))
        self.menu_lilypond.setTitle(_('&LilyPond'))
        self.menu_tools.setTitle(_('&Tools'))
        self.menu_window.setTitle(_('&Window'))
        self.menu_sessions.setTitle(_('&Sessions'))
        self.menu_help.setTitle(_('&Help'))
        self.toolbar_main.setWindowTitle(_("Main Toolbar"))
        
       
class TabBar(QTabBar):
    """The tabbar above the editor window."""
    
    currentDocumentChanged = pyqtSignal(document.Document)
    
    def __init__(self, parent=None):
        super(TabBar, self).__init__(parent)
        
        mainwin = self.window()
        self.docs = []
        for doc in app.documents:
            self.addDocument(doc)
            if doc is mainwin.currentDocument():
                self.setCurrentDocument(doc)
        
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        mainwin.currentDocumentChanged.connect(self.setCurrentDocument)
        self.currentChanged.connect(self.slotCurrentChanged)
        self.tabMoved.connect(self.slotTabMoved)
        self.setTabsClosable(True) # TODO: make configurable
        self.setMovable(True)      # TODO: make configurable
        self.setExpanding(False)
        
    def addDocument(self, doc):
        if doc not in self.docs:
            self.docs.append(doc)
            self.blockSignals(True)
            self.addTab('')
            self.blockSignals(False)
            self.setDocumentStatus(doc)
            #doc.urlChanged.connect(self.setDocumentStatus)
            #doc.captionChanged.connect(self.setDocumentStatus)

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
            self.setTabIcon(index, icons.get('text-plain'))
            self.setTabText(index, str(id(doc))) #TEMP: doc.documentName())
    
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
        self.docs[index].close()
    
    def slotTabMoved(self, index_from, index_to):
        """ Called when the user moved a tab. """
        doc = self.docs.pop(index_from)
        self.docs.insert(index_to, doc)
        
        

class ActionCollection(actioncollection.ActionCollection):
    def __init__(self, mainwindow):
        self.file_new = QAction(mainwindow)
        self.file_open = QAction(mainwindow)
        self.file_open_recent = QAction(mainwindow)
        self.file_open_current_directory = QAction(mainwindow)
        self.file_save = QAction(mainwindow)
        self.file_save_as = QAction(mainwindow)
        self.file_save_all = QAction(mainwindow)
        self.file_print_source = QAction(mainwindow)
        self.file_print_music = QAction(mainwindow)
        self.file_close = QAction(mainwindow)
        self.file_close_other = QAction(mainwindow)
        self.file_quit = QAction(mainwindow)
        
        self.edit_undo = QAction(mainwindow)
        self.edit_redo = QAction(mainwindow)
        self.edit_cut_assign = QAction(mainwindow)
        self.edit_cut = QAction(mainwindow)
        self.edit_copy = QAction(mainwindow)
        self.edit_paste = QAction(mainwindow)
        self.edit_select_all = QAction(mainwindow)
        self.edit_select_current_toplevel = QAction(mainwindow)
        self.edit_select_none = QAction(mainwindow)
        self.edit_find = QAction(mainwindow)
        self.edit_find_next = QAction(mainwindow)
        self.edit_find_previous = QAction(mainwindow)
        self.edit_replace = QAction(mainwindow)
        self.edit_preferences = QAction(mainwindow)
        
        self.view_next_document = QAction(mainwindow)
        self.view_previous_document = QAction(mainwindow)
        self.view_document = QAction(mainwindow)
        self.view_bookmark = QAction(mainwindow)
        self.view_bookmark.setCheckable(True)
        self.view_clear_error_marks = QAction(mainwindow)
        self.view_clear_all_marks = QAction(mainwindow)
        
        self.lilypond_runner = QAction(mainwindow)
        self.lilypond_run_preview = QAction(mainwindow)
        self.lilypond_run_publish = QAction(mainwindow)
        self.lilypond_run_custom = QAction(mainwindow)
        self.lilypond_cancel = QAction(mainwindow)
        
        self.window_new = QAction(mainwindow)
        self.window_fullscreen = QAction(mainwindow)
        self.window_fullscreen.setCheckable(True)
        
        self.session_new = QAction(mainwindow)
        self.session_save = QAction(mainwindow)
        self.session_manage = QAction(mainwindow)
        self.session_none = QAction(mainwindow)
        
        self.help_manual = QAction(mainwindow)
        self.help_whatsthis = QAction(mainwindow)
        self.help_about = QAction(mainwindow)
        self.help_bugreport = QAction(mainwindow)
        
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
        
        self.session_new.setIcon(icons.get('document-new'))
        self.session_save.setIcon(icons.get('document-save'))
        self.session_manage.setIcon(icons.get('view-choose'))
        
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
        self.file_print_music.setText(_("&Print &Music..."))
        self.file_print_source.setText(_("Print Source..."))
        self.file_close.setText(_("&Close"))
        self.file_close_other.setText(_("Close Other Documents"))
        self.file_quit.setText(_("&Quit"))

        self.edit_undo.setText(_("&Undo"))
        self.edit_redo.setText(_("Re&do"))
        self.edit_cut_assign.setText(_("Cut and Assign..."))
        self.edit_cut.setText(_("Cu&t"))
        self.edit_copy.setText(_("&Copy"))
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
        self.view_bookmark.setText(_("&Mark Current Line"))
        self.view_clear_error_marks.setText(_("Clear &Error Marks"))
        self.view_clear_all_marks.setText(_("Clear &All Marks"))
        
        self.lilypond_runner.setText(_("LilyPond"))
        self.lilypond_run_preview.setText(_("Run &LilyPond (preview)"))
        self.lilypond_run_publish.setText(_("Run LilyPond (&publish)"))
        self.lilypond_run_custom.setText(_("Run LilyPond (&custom)"))
        self.lilypond_cancel.setText(_("Interrupt LilyPond &Job"))
        
        self.window_new.setText(_("&New Window"))
        self.window_fullscreen.setText(_("&Fullscreen"))
        
        self.session_new.setText(_("&New..."))
        self.session_save.setText(_("&Save"))
        self.session_manage.setText(_("&Manage..."))
        self.session_none.setText(_("None"))
        
        self.help_manual.setText(_("&User Guide"))
        self.help_whatsthis.setText(_("&What's This?"))
        self.help_bugreport.setText(_("Report a &Bug..."))
        self.help_about.setText(_("&About {name}").format(name=info.description))
        

