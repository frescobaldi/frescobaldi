# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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
ActionCollection is a class to keep a list of actions as attributes.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app


class ActionCollection:
    
    def __init__(self, parent=None):
        """Should define all actions in this collection as instance attributes."""
        self.createActions(parent)
        self._actions = dict(self.__dict__)
        self.storeDefaults()
        self.translateUI()
        app.languageChanged.connect(self.translateUI)
        
    def createActions(self, parent=None):
        """Should add actions as instance attributes.
        
        The QActions should get icons and shortcuts. Texts should be set
        in translateUI().
        
        """
        pass

    def translateUI(self):
        """Should (re)translate all the titles of the actions."""
        pass
    
    def storeDefaults(self):
        """Should preset default QKeySequence values for actions.
        
        The default implementation just reads the shortcuts set in
        createActions().
        
        """
        self._defaults = dict(
            (name, action.shortcuts())
            for name, action in self._actions.items()
            if action.shortcuts())

    def load(self, settings):
        """Reads keyboard shortcuts from a QSettings object."""
        settings.begingroup(self.name)
        keys = settings.allKeys()
        for name in self._actions:
            if name in keys:
                shortcuts = [QKeySequence(s) for s in settings.value(name) or []]
            else:
                shortcuts = self._defaults.get(name) or []
            self._actions[name].setShortcuts(shortcuts)
        settings.endgroup()


