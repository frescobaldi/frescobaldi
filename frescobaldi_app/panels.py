# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Base class and stubs and logic for Panels (QDockWidgets).

When the panel must be shown its widget is instantiated.
"""

import weakref

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDockWidget, QLabel

import actioncollection
import actioncollectionmanager
import app
import plugin


def manager(mainwindow):
    return PanelManager.instance(mainwindow)
    

class PanelManager(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        # instantiate the panel stubs here
        import quickinsert
        self.quickinsert = quickinsert.QuickInsertPanel(mainwindow)
        import musicview
        self.musicview = musicview.MusicViewPanel(mainwindow)
        import logtool
        self.logtool = logtool.LogTool(mainwindow)
        import helpbrowser
        self.helpbrowser = helpbrowser.HelpBrowser(mainwindow)
        
        self.createActions()
        
        # make some default arrangements
        mainwindow.tabifyDockWidget(self.musicview, self.helpbrowser)

    def createActions(self):
        self.actionCollection = Actions(self)
        actioncollectionmanager.manager(self.mainwindow()).addActionCollection(self.actionCollection)

    def addActionsToMenu(self, menu):
        """Adds all toggleViewActions to the given menu."""
        menu.addAction(self.actionCollection.panel_quickinsert)
        menu.addAction(self.actionCollection.panel_musicview)
        menu.addAction(self.actionCollection.panel_logtool)
        menu.addAction(self.actionCollection.panel_helpbrowser)


class Actions(actioncollection.ActionCollection):
    """Manages the keyboard shortcuts to hide/show the plugins."""
    name = "panels"
    
    def createActions(self, manager):
        # add the actions for the plugins
        self.panel_quickinsert = manager.quickinsert.toggleViewAction()
        self.panel_musicview = manager.musicview.toggleViewAction()
        self.panel_logtool = manager.logtool.toggleViewAction()
        self.panel_helpbrowser = manager.helpbrowser.toggleViewAction()


class Panel(QDockWidget):
    """Base class for Panels.
    
    You should implement __init__(), createWidget() and translateUI().
    On the first call to sizeHint() our widget is created.
    
    """
    def __init__(self, mainwindow):
        """You should implement this method to set a title and add yourself to the mainwindow.
        
        First call this super method as it calls the Qt constructor.
        
        """
        super(Panel, self).__init__(mainwindow)
        self.visibilityChanged.connect(self.widget)
        app.translateUI(self)
    
    def mainwindow(self):
        return self.parentWidget()
        
    def sizeHint(self):
        """This is always called when the panel needs to be shown. Instantiate if not already done."""
        self.widget()
        return super(Panel, self).sizeHint()
    
    def widget(self):
        """Ensures that our widget() is created and returns it."""
        w = super(Panel, self).widget()
        if not w:
            self.visibilityChanged.disconnect(self.widget)
            w = self.createWidget()
            self.setWidget(w)
        return w
        
    def createWidget(self):
        """Re-implement this to return the widget for this tool."""
        return QLabel("<test>", self)
        
    def activate(self):
        """Really shows the dock widget, even if tabified."""
        self.show()
        if self.mainwindow().tabifiedDockWidgets(self) or self.isFloating():
            self.raise_()

