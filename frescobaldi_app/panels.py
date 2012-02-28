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
        self.loadTool("quickinsert.QuickInsertPanel")
        self.loadTool("musicview.MusicViewPanel")
        self.loadTool("logtool.LogTool")
        self.loadTool("docbrowser.HelpBrowser")
        self.loadTool("snippet.tool.SnippetTool")
        self.loadTool("miditool.MidiTool")
        self.loadTool("charmap.CharMap")
        self.loadTool("doclist.DocumentList")
        
        self.createActions()
        # make some default arrangements
        mainwindow.tabifyDockWidget(self.musicview, self.docbrowser)
    
    def loadTool(self, name):
        """Loads the named tool.
        
        The name consists of a module name and the class name of the Panel
        subclass to instantiate.
        
        The instance is saved in an attribute 'name', with dots and the class
        name removed. So if you call self.loadTool("foo.bar.FooBar"), you can
        find the instantiated FooBar panel in the 'foobar' attribute.
        
        """
        module_name, class_name = name.rsplit('.', 1)
        __import__(module_name)
        module = sys.modules[module_name]
        attribute_name = module_name.replace('.', '')
        cls = vars(module)[class_name]
        panel = cls(self.mainwindow())
        self._panels.append((attribute_name, panel))
        setattr(self, attribute_name, panel)

    def createActions(self):
        self.actionCollection = Actions(self)
        actioncollectionmanager.manager(self.mainwindow()).addActionCollection(self.actionCollection)

    def addActionsToMenu(self, menu):
        """Adds all toggleViewActions to the given menu."""
        for name, panel in self._panels:
            menu.addAction(panel.toggleViewAction())


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
    
    This QDockWidget subclass implements lazy loading of the panel's widget.
    When one of sizeHint() or showEvent() is called for the first time, the
    widget is created by calling createWidget().
    
    """
    def __init__(self, mainwindow):
        """Implement this method to add yourself to the mainwindow.
        
        First call this super method as it calls the Qt constructor.
        
        """
        super(Panel, self).__init__(mainwindow)
        self.setObjectName(self.__class__.__name__.lower())
        app.translateUI(self)
    
    def mainwindow(self):
        """Returns the MainWindow."""
        return self.parentWidget()
        
    def sizeHint(self):
        """Re-implemented to force creation of our widget."""
        self.widget()
        return super(Panel, self).sizeHint()
    
    def widget(self):
        """Ensures that our widget() is created and returns it."""
        w = super(Panel, self).widget()
        if not w:
            w = self.createWidget()
            self.setWidget(w)
        return w
    
    def showEvent(self, ev):
        """Re-implemented to force creation of widget."""
        self.widget()
        
    def createWidget(self):
        """Implement this to return the widget for this tool."""
        return QLabel("<test>", self)
        
    def activate(self):
        """Really shows the dock widget, even if tabified or floating."""
        self.show()
        if self.mainwindow().tabifiedDockWidgets(self) or self.isFloating():
            self.raise_()
    
    def translateUI(self):
        """Implement to set a title for the widget and its toggleViewAction."""
        raise NotImplementedError(
            "Please implement this method to at least set a title "
            "for the dockwidget and its toggleViewAction().")


