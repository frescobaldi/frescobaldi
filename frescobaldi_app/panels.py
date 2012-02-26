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
Base class and stubs and logic for Panels (QDockWidgets).

When the panel must be shown its widget is instantiated.
"""

from __future__ import unicode_literals

import sys
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
        """Instantiate the Panel Manager.
        
        In this method you can also load the modules that implement
        panel tools.
        
        """
        self._panels = []
        
        # add the the panel stubs here
        self.loadModule("quickinsert")
        self.loadModule("musicview")
        self.loadModule("logtool")
        self.loadModule("docbrowser")
        self.loadModule("snippet.tool")
        self.loadModule("miditool")
        self.loadModule("charmap")
        self.loadModule("doclist")
        
        self.createActions()
        # make some default arrangements
        mainwindow.tabifyDockWidget(self.musicview, self.docbrowser)
    
    def loadModule(self, name):
        """Loads the specified module.
        
        The Panel subclass is automatically found and instantiated, and
        the instance is saved in an attribute 'name', with dots removed.
        So if you call self.loadModule("foo.bar"), you can find the instantiated
        panel in the 'foobar' attribute.
        
        """
        __import__(name)
        module = sys.modules[name]
        name = name.replace('.', '')
        
        for cls in vars(module).values():
            if isinstance(cls, type) and issubclass(cls, Panel):
                panel = cls(self.mainwindow())
                break
        self._panels.append((name, panel))
        setattr(self, name, panel)

    def createActions(self):
        self.actionCollection = Actions(self)
        actioncollectionmanager.manager(self.mainwindow()).addActionCollection(self.actionCollection)

    def addActionsToMenu(self, menu):
        """Adds all toggleViewActions to the given menu."""
        for name, panel in self._panels:
            action = getattr(self.actionCollection, 'panel_' + name)
            menu.addAction(action)


class Actions(actioncollection.ActionCollection):
    """Manages the keyboard shortcuts to hide/show the plugins."""
    name = "panels"
    
    def createActions(self, manager):
        # add the actions for the plugins
        for name, panel in manager._panels:
            setattr(self, 'panel_' + name, panel.toggleViewAction())


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
        self.setObjectName(self.__class__.__name__.lower())
        self.visibilityChanged.connect(self.slotVisibilityChanged)
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
            w = self.createWidget()
            self.setWidget(w)
            self.visibilityChanged.disconnect(self.slotVisibilityChanged)
        return w
    
    def slotVisibilityChanged(self, visible):
        if visible:
            self.widget()
        
    def createWidget(self):
        """Re-implement this to return the widget for this tool."""
        return QLabel("<test>", self)
        
    def activate(self):
        """Really shows the dock widget, even if tabified."""
        self.show()
        if self.mainwindow().tabifiedDockWidgets(self) or self.isFloating():
            self.raise_()

