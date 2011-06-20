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
- provide possibility for submenus
- caching (keep actions alive?)

"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import panels

class InsertMenu(QMenu):
    def __init__(self, parent=None):
        super(InsertMenu, self).__init__(parent)
        
        self.aboutToShow.connect(self.populate)
        self.aboutToHide.connect(self.clearMenu, Qt.QueuedConnection)
        self.triggered.connect(self.slotTriggered)
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("&Insert"))
    
    def mainwindow(self):
        return self.parent().window()
        
    def populate(self):
        self.clear()
        from . import model, snippets, actions
        ac = panels.manager(self.mainwindow()).snippettool.snippetActions
        groups = {}
        for name in sorted(model.model().names()):
            menu = snippets.get(name).variables.get('menu')
            if menu:
                groups.setdefault(menu, []).append(actions.action(name, self, ac))
        for n, group in enumerate(sorted(groups)):
            if n:
                self.addSeparator()
            for action in groups[group]:
                self.addAction(action)
    
    def clearMenu(self):
        self.clear()
    
    def slotTriggered(self, action):
        name = action.objectName()
        if name:
            from . import insert
            view = self.mainwindow().currentView()
            view.setFocus()
            insert.insert(name, view)


