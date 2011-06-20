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
Place snippets in menu.

If a snippet defines the variable 'menu' it is placed in the menu, sorted
on its internal action name and grouped by the value of the 'menu' variable.

TODO:
- provide submenus
- caching (keep actions alive?)

"""

from __future__ import unicode_literals

from PyQt4.QtGui import QMenu

import app
import util
import panels


class InsertMenu(QMenu):
    def __init__(self, parent=None):
        super(InsertMenu, self).__init__(parent)
        
        self.aboutToShow.connect(self.populate)
        self.aboutToHide.connect(self.clearMenu)
        self.triggered.connect(self.slotTriggered)
        tool = panels.manager(self.mainwindow()).snippettool
        self.addAction(tool.actionCollection.snippettool_activate)
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("&Insert"))
    
    def mainwindow(self):
        return self.parent().window()
        
    def populate(self):
        """Inserts all snippets that have a menu variable in the menu.
        
        The snippets are inserted before the "Snippets..." action that
        is inserted at construction.
        
        If the 'menu' snippet variable also has a value, it is used
        to group snippets with the same value, sorted on internal id.
        Groups are separated with a separator.
        
        """
        from . import model, snippets, actions
        tool = panels.manager(self.mainwindow()).snippettool
        last = tool.actionCollection.snippettool_activate
        groups = {}
        for name in sorted(model.model().names()):
            menu = snippets.get(name).variables.get('menu')
            if menu:
                groups.setdefault(menu, []).append(
                    actions.action(name, self, tool.snippetActions))
        for group in sorted(groups):
            for action in groups[group]:
                self.insertAction(last, action)
            self.insertSeparator(last)
        util.addAccelerators(self.actions())
        
    def clearMenu(self):
        """Deletes the actions on menu hide, excepts the "Snippets..." action."""
        for a in self.actions()[:-1]:
            a.deleteLater()
    
    def slotTriggered(self, action):
        """Called when an action is triggered."""
        name = action.objectName()
        if name:
            from . import insert
            view = self.mainwindow().currentView()
            view.setFocus()
            insert.insert(name, view)


