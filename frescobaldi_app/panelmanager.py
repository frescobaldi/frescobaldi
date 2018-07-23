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
Manages the Panels (Tools).
"""


import sys
import collections

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMenu

import actioncollection
import actioncollectionmanager
import plugin
import app


def manager(mainwindow):
    return PanelManager.instance(mainwindow)


class PanelManager(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        """Instantiate the Panel Manager.

        In this method you should also load the modules that implement
        panel tools.

        """
        self._panels = []
        self._submenus = collections.OrderedDict([
            ('viewers', {
                'menu': QMenu(_('&Viewers')),
                'panels': []
            }),
            ('coding', {
                'menu': QMenu(_('&Coding')),
                'panels': []
            }),
            ('structure', {
                'menu': QMenu(_('&Structure')),
                'panels': []
            }),
            ('midi', {
                'menu': QMenu(_('&MIDI')),
                'panels': []
            }),
            ])

        # add the the panel stubs here
        self.loadPanel("musicview.MusicViewPanel", "viewers")
        self.loadPanel("svgview.SvgViewPanel", "viewers")
        self.loadPanel("viewers.manuscript.ManuscriptViewPanel", "viewers")
        self.loadPanel("docbrowser.HelpBrowser", "viewers")
        self.loadPanel("logtool.LogTool", "viewers")
        self.loadPanel("layoutcontrol.LayoutControlOptions", "viewers")
        self.loadPanel("quickinsert.QuickInsertPanel", "coding")
        self.loadPanel("charmap.CharMap", "coding")
        self.loadPanel("snippet.tool.SnippetTool", "coding")
        self.loadPanel("doclist.DocumentList", "structure")
        self.loadPanel("outline.OutlinePanel", "structure")
        self.loadPanel("miditool.MidiTool", "midi")
        self.loadPanel("midiinput.tool.MidiInputTool", "midi")

        # The Object editor is highly experimental and should be
        # commented out for stable releases.
        if app.is_git_controlled() or QSettings().value("experimental-features", False, bool):
            self.loadPanel("objecteditor.ObjectEditor", "coding")
        self.createActions()

        # make some default arrangements
        mainwindow.tabifyDockWidget(self.musicview, self.docbrowser)
        mainwindow.tabifyDockWidget(self.musicview, self.svgview)


    def loadPanel(self, name, submenu=None):
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
        attribute_name = module_name.split('.')[-1] if "viewers" in name else module_name.replace('.', '')
        cls = vars(module)[class_name]
        panel = cls(self.mainwindow())
        self._panels.append((attribute_name, panel))
        setattr(self, attribute_name, panel)
        if submenu:
            self._submenus[submenu]['panels'].append(panel)

    def createActions(self):
        self.actionCollection = Actions(self)
        actioncollectionmanager.manager(self.mainwindow()).addActionCollection(self.actionCollection)

    def addActionsToMenu(self, menu):
        """Adds all toggleViewActions to the given menu."""
        added_panels = []

        for submenu in self._submenus:
            sm = self._submenus[submenu]
            for panel in sm['panels']:
                sm['menu'].addAction(panel.toggleViewAction())
                added_panels.append(panel)
            menu.addMenu(sm['menu'])

        for name, panel in self._panels:
            if not panel in added_panels:
                menu.addAction(panel.toggleViewAction())

    def panels_at(self, area):
        """Return the list of panels at the specified Qt.DockWidgetArea.

        Each entry is the (name, panel) tuple. Floating or hidden panels are
        not returned, but tabbed panels are.

        """
        result = []
        for name, panel in self._panels:
            if (self.mainwindow().dockWidgetArea(panel) == area
                and not panel.isFloating()
                and (panel.isVisible() or self.mainwindow().tabifiedDockWidgets(panel))):
                result.append((name, panel))
        return result


class Actions(actioncollection.ActionCollection):
    """Manages the keyboard shortcuts to hide/show the plugins."""
    name = "panels"

    def createActions(self, manager):
        # add the actions for the plugins
        for name, panel in manager._panels:
            setattr(self, 'panel_' + name, panel.toggleViewAction())
