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
Insert pieces of text or templates via keyboard shortcuts, autocomplete
or the Insert menu.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import actioncollection
import actioncollectionmanager
import plugin



class Manager(plugin.MainWindowPlugin):
    """This manages the full Insert menu."""
    def __init__(self, mainwindow):
        self.actions = InsertActions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(self.actions)
        self.actionCollection = ac = ActionCollection(mainwindow)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        self.menu = QMenu(mainwindow, aboutToShow=self.populateMenu)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.menu.setTitle(_("&Insert"))
    
    def actionForName(self, name):
        print "action requested", name
        pass # TODO: implement
    
    def populateMenu(self):
        """Called when the Insert Menu is displayed."""
        m = self.menu
        m.clear()
        # TODO: add templates to the menu
        
        # finally...
        m.addSeparator()
        m.addAction(self.actionCollection.insert_show_editor)


class ActionCollection(actioncollection.ActionCollection):
    name = "insertmenu"
    def createActions(self, parent):
        self.insert_show_editor = QAction(parent)
    
    def translateUI(self):
        self.insert_show_editor.setText(_("Edit &Templates..."))

    def title(self):
        return _("Insert Templates")


class InsertActions(actioncollection.ShortcutCollection):
    """Manages keyboard shortcuts for the Insert module."""
    name = "insert"
    def __init__(self, mgr):
        super(InsertActions, self).__init__(mgr.mainwindow())
        self.manager = weakref.ref(mgr)
    
    def createDefaultShortcuts(self):
        self.setDefaultShortcuts('voice1', [QKeySequence('Alt+1')])
        self.setDefaultShortcuts('voice2', [QKeySequence('Alt+2')])
        self.setDefaultShortcuts('voice3', [QKeySequence('Alt+3')])
        self.setDefaultShortcuts('voice4', [QKeySequence('Alt+4')])
        self.setDefaultShortcuts('1voice', [QKeySequence('Alt+0')])
        self.setDefaultShortcuts('times23', [QKeySequence('Ctrl+3')])

    def realAction(self, name):
        return self.manager().actionForName(name)
        
    def title(self):
        return _("Insert Templates")
    

