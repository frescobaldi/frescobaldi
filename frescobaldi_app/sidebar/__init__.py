# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
The sidebar in the editor View.
"""


import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QAction, QApplication

import app
import actioncollection
import actioncollectionmanager
import plugin


class SideBarManager(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        self.actionCollection = ac = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.view_linenumbers.triggered.connect(self.toggleLineNumbers)
        ac.folding_enable.triggered.connect(self.toggleFolding)
        ac.folding_fold_current.triggered.connect(self.foldCurrent)
        ac.folding_fold_top.triggered.connect(self.foldTop)
        ac.folding_unfold_current.triggered.connect(self.unfoldCurrent)
        ac.folding_fold_all.triggered.connect(self.foldAll)
        ac.folding_unfold_all.triggered.connect(self.unfoldAll)
        mainwindow.viewManager.activeViewSpaceChanged.connect(self.updateActions)
        app.viewSpaceCreated.connect(self.newViewSpace)
        # there is always one ViewSpace, initialize it
        self.manager().loadSettings()
        self.updateActions()

    def manager(self, viewspace=None):
        """Returns the ViewSpaceSideBarManager for the (current) ViewSpace."""
        if viewspace is None:
            viewspace  = self.mainwindow().viewManager.activeViewSpace()
        return ViewSpaceSideBarManager.instance(viewspace)

    def toggleLineNumbers(self):
        manager = self.manager()
        manager.setLineNumbersVisible(not manager.lineNumbersVisible())
        manager.saveSettings()

    def toggleFolding(self):
        """Toggle folding in the current view."""
        viewspace = self.mainwindow().viewManager.activeViewSpace()
        manager = self.manager(viewspace)
        enable = not manager.foldingVisible()
        document = viewspace.document()

        # do it for all managers that display our document
        for m in manager.instances():
            if m.viewSpace().document() is document:
                m.setFoldingVisible(enable)
        # and also update in other windows
        for i in self.instances():
            i.updateActions()
        manager.saveSettings()
        # unfold the document if disabled
        if not enable:
            self.folder().unfold_all()

    def folder(self):
        """Get the Folder for the current document."""
        import folding
        return folding.Folder.get(self.mainwindow().currentDocument())

    def foldCurrent(self):
        """Fold current region."""
        self.folder().fold(self.mainwindow().textCursor().block())

    def foldTop(self):
        """Fold current region to toplevel."""
        self.folder().fold(self.mainwindow().textCursor().block(), -1)

    def unfoldCurrent(self):
        """Unfold current region."""
        block = self.mainwindow().textCursor().block()
        folder = self.folder()
        folder.ensure_visible(block)
        folder.unfold(block)

    def foldAll(self):
        """Fold the whole document."""
        self.folder().fold_all()

    def unfoldAll(self):
        """Unfold the whole document."""
        self.folder().unfold_all()

    def updateActions(self):
        manager = self.manager()
        ac = self.actionCollection
        ac.view_linenumbers.setChecked(manager.lineNumbersVisible())
        folding = manager.foldingVisible()
        ac.folding_enable.setChecked(folding)
        ac.folding_fold_current.setEnabled(folding)
        ac.folding_fold_top.setEnabled(folding)
        ac.folding_unfold_current.setEnabled(folding)
        ac.folding_fold_all.setEnabled(folding)
        ac.folding_unfold_all.setEnabled(folding)

    def newViewSpace(self, viewspace):
        viewmanager = viewspace.manager()
        if viewmanager and viewmanager.window() is self.mainwindow():
            # let the new viewspace take over the settings of the currently
            # active viewspace
            self.manager(viewspace).copySettings(self.manager())


class ViewSpaceSideBarManager(plugin.ViewSpacePlugin):
    """Manages SideBar settings and behaviour for one ViewSpace."""
    def __init__(self, viewspace):
        self._line_numbers = False
        self._linenumberarea = None
        self._folding = False
        self._foldingarea = None
        viewspace.viewChanged.connect(self.updateView)

    def loadSettings(self):
        """Loads the settings from config."""
        s = QSettings()
        s.beginGroup("sidebar")
        line_numbers = s.value("line_numbers", self._line_numbers, bool)
        self.setLineNumbersVisible(line_numbers)
        folding = s.value("folding", self._folding, bool)
        self.setFoldingVisible(folding)

    def saveSettings(self):
        """Saves the settings to config."""
        s = QSettings()
        s.beginGroup("sidebar")
        s.setValue("line_numbers", self.lineNumbersVisible())
        s.setValue("folding",self.foldingVisible())

    def copySettings(self, other):
        """Takes over the settings from another viewspace's manager."""
        self.setLineNumbersVisible(other.lineNumbersVisible())
        self.setFoldingVisible(other.foldingVisible())

    def setLineNumbersVisible(self, visible):
        """Set whether line numbers are to be shown."""
        if visible == self._line_numbers:
            return
        self._line_numbers = visible
        self.updateView()

    def lineNumbersVisible(self):
        """Returns whether line numbers are shown."""
        return self._line_numbers

    def setFoldingVisible(self, visible):
        """Set whether folding indicators are to be shown."""
        if visible == self._folding:
            return
        self._folding = visible
        self.updateView()

    def foldingVisible(self):
        """Return whether folding indicators are to be shown."""
        return self._folding

    def updateView(self):
        """Adjust the sidebar in the current View in the sidebar."""
        view = self.viewSpace().activeView()
        if not view:
            return

        def add(widget):
            """Adds a widget to the side of the view."""
            from gadgets import borderlayout
            if QApplication.isRightToLeft():
                side = borderlayout.RIGHT
            else:
                side = borderlayout.LEFT
            borderlayout.BorderLayout.get(view).addWidget(widget, side)

        # add or remove the folding widget
        if self._folding:
            if not self._foldingarea:
                import folding
                self._foldingarea = folding.FoldingArea()
                self._foldingarea.setPalette(QApplication.palette())
            add(self._foldingarea)
            self._foldingarea.setTextEdit(view)
        elif self._foldingarea:
            self._foldingarea.deleteLater()
            self._foldingarea = None

        # add of remove the linenumbers widget
        if self._line_numbers:
            if not self._linenumberarea:
                from widgets import linenumberarea
                self._linenumberarea = linenumberarea.LineNumberArea()
            add(self._linenumberarea)
            self._linenumberarea.setTextEdit(view)
        elif self._linenumberarea:
            self._linenumberarea.deleteLater()
            self._linenumberarea = None

        # display horizontal lines where text is collapsed
        if self._folding:
            import folding
            view.viewport().installEventFilter(folding.line_painter)
        else:
            # don't import the folding module if it was not loaded anyway
            folding = sys.modules.get('folding')
            if folding:
                view.viewport().removeEventFilter(folding.line_painter)


class Actions(actioncollection.ActionCollection):
    name = "sidebar"
    def createActions(self, parent):
        self.view_linenumbers = QAction(parent, checkable=True)
        self.folding_enable = QAction(parent, checkable=True)
        self.folding_fold_current = QAction(parent)
        self.folding_fold_top = QAction(parent)
        self.folding_unfold_current = QAction(parent)
        self.folding_fold_all = QAction(parent)
        self.folding_unfold_all = QAction(parent)

    def translateUI(self):
        self.view_linenumbers.setText(_("&Line Numbers"))
        self.folding_enable.setText(_("&Enable Folding"))
        self.folding_fold_current.setText(_("&Fold Current Region"))
        self.folding_fold_top.setText(_("Fold &Top Region"))
        self.folding_unfold_current.setText(_("&Unfold Current Region"))
        self.folding_fold_all.setText(_("Fold &All"))
        self.folding_unfold_all.setText(_("U&nfold All"))


