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

"""
The snippets dockwindow.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction, QKeySequence

import actioncollection
import actioncollectionmanager
import app
import panels


class SnippetTool(panels.Panel):
    """A dockwidget for selecting, applying and editing the list of snippets."""
    def __init__(self, mainwindow):
        super(SnippetTool, self).__init__(mainwindow)
        self.hide()
        self.actions = SnippetActions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(self.actions)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+S"))
        ac = self.actionCollection = Actions()
        ac.snippettool_activate.triggered.connect(self.activate)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        mainwindow.addDockWidget(Qt.BottomDockWidgetArea, self)
        
    def translateUI(self):
        self.setWindowTitle(_("Snippets"))
        self.toggleViewAction().setText(_("&Snippets"))
        
    def createWidget(self):
        from . import widget
        return widget.Widget(self)

    def activate(self):
        super(SnippetTool, self).activate()
        self.widget().searchEntry.setFocus()
        self.widget().searchEntry.selectAll()


class Actions(actioncollection.ActionCollection):
    name = "snippettool"
    def createActions(self, parent=None):
        self.snippettool_activate = QAction(parent)
        self.snippettool_activate.setShortcut(QKeySequence("Ctrl+T"))

    def translateUI(self):
        self.snippettool_activate.setText(_("&Snippets..."))


class SnippetActions(actioncollection.ShortcutCollection):
    """Manages keyboard shortcuts for the snippets."""
    name = "snippets"
    def __init__(self, tool):
        super(SnippetActions, self).__init__(tool.mainwindow().centralWidget())
        self.tool = weakref.ref(tool)
    
    def createDefaultShortcuts(self):
        self.setDefaultShortcuts('voice1', [QKeySequence('Alt+1')])
        self.setDefaultShortcuts('voice2', [QKeySequence('Alt+2')])
        self.setDefaultShortcuts('voice3', [QKeySequence('Alt+3')])
        self.setDefaultShortcuts('voice4', [QKeySequence('Alt+4')])
        self.setDefaultShortcuts('1voice', [QKeySequence('Alt+0')])
        self.setDefaultShortcuts('times23', [QKeySequence('Ctrl+3')])

    def realAction(self, name):
        from . import actions
        return actions.action(name)
    
    def triggerAction(self, name):
        from . import actions
        view = self.tool().mainwindow().currentView()
        if view.hasFocus() or self.tool().widget().searchEntry.hasFocus():
            actions.applySnippet(view, name)
            
    def title(self):
        return _("Snippets")


