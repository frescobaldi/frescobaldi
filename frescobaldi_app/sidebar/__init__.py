# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2012 by Wilbert Berendsen
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

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QAction, QApplication

import app
import actioncollection
import actioncollectionmanager
import plugin


class SideBarManager(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        self.actionCollection = ac = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.view_linenumbers.triggered.connect(self.toggleLineNumbers)
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
        
    def updateActions(self):
        manager = self.manager()
        ac = self.actionCollection
        ac.view_linenumbers.setChecked(manager.lineNumbersVisible())
    
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
        viewspace.viewChanged.connect(self.updateView)
        
    def loadSettings(self):
        """Loads the settings from config."""
        s = QSettings()
        s.beginGroup("sidebar")
        line_numbers = s.value("line_numbers", self._line_numbers) in (True, "true")
        self.setLineNumbersVisible(line_numbers)
    
    def saveSettings(self):
        """Saves the settings to config."""
        s = QSettings()
        s.beginGroup("sidebar")
        s.setValue("line_numbers", self.lineNumbersVisible())
    
    def copySettings(self, other):
        """Takes over the settings from another viewspace's manager."""
        self.setLineNumbersVisible(other.lineNumbersVisible())
        
    def setLineNumbersVisible(self, visible):
        """Set whether line numbers are to be shown."""
        if visible == self._line_numbers:
            return
        self._line_numbers = visible
        self.updateView()

    def lineNumbersVisible(self):
        """Returns whether line numbers are shown."""
        return self._line_numbers
    
    def updateView(self):
        """Adjust the sidebar in the current View in the sidebar."""
        view = self.viewSpace().activeView()
        if not view:
            return
        
        def add(widget):
            """Adds a widget to the side of the view."""
            from widgets import borderlayout
            if QApplication.isRightToLeft():
                side = borderlayout.RIGHT
            else:
                side = borderlayout.LEFT
            borderlayout.BorderLayout.get(view).addWidget(widget, side)

        # add of remove the linenumbers widget
        if self._line_numbers:
            if not self._linenumberarea:
                from widgets import linenumberarea
                self._linenumberarea = linenumberarea.LineNumberArea()
            self._linenumberarea.setTextEdit(view)
            add(self._linenumberarea)
        elif self._linenumberarea:
            self._linenumberarea.deleteLater()
            self._linenumberarea = None




class Actions(actioncollection.ActionCollection):
    name = "sidebar"
    def createActions(self, parent):
        self.view_linenumbers = QAction(parent, checkable=True)
    
    def translateUI(self):
        self.view_linenumbers.setText(_("&Line Numbers"))



