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
Manages the Panels (Tools).
"""

from __future__ import unicode_literals

import sys

import actioncollection
import actioncollectionmanager
import plugin


def manager(mainwindow):
    return PanelManager.instance(mainwindow)
    

class PanelManager(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        """Instantiate the Panel Manager.
        
        In this method you should also load the modules that implement
        panel tools.
        
        """
        self._panels = []
        
        # add the the panel stubs here
        self.loadPanel("quickinsert.QuickInsertPanel")
        self.loadPanel("musicview.MusicViewPanel")
        self.loadPanel("logtool.LogTool")
        self.loadPanel("docbrowser.HelpBrowser")
        self.loadPanel("snippet.tool.SnippetTool")
        self.loadPanel("miditool.MidiTool")
        self.loadPanel("charmap.CharMap")
        self.loadPanel("doclist.DocumentList")
        self.loadPanel("outline.OutlinePanel")
        self.loadPanel("preview_mode.PreviewOptions")
        
        self.createActions()
        # make some default arrangements
        mainwindow.tabifyDockWidget(self.musicview, self.docbrowser)
    
    def loadPanel(self, name):
        """Loads the named Panel.
        
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


