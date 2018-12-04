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
Base ExtensionActionCollection for extensions
"""

from PyQt5.QtWidgets import QMenu

import actioncollection

class ExtensionActionCollection(actioncollection.ActionCollection):
    """An ActionCollection descendant for use with extensions.
    Apart from the added functionality it's noteworthy that
    the 'name' variable is emptied and that the collection is local
    to the extension (i.e. not used in the globa action collection
    manager).
    """

    name = ""

    def __init__(self, extension):
        self._extension = extension
        super(ExtensionActionCollection, self).__init__(extension.mainwindow())
        # Initialize menu actions.
        # By default the Tools menu entry is set to None
        # (causing all actions to be used) while those for
        # the editor and music viewer are empty lists.
        # By overriding configure_menu_actions() any of the menus
        # can be configured manually.
        self._action_lists = {
            'tools': None,
            'editor': [],
            'musicview': [],
            'manuscriptview': []
        }
        # Interface for subclasses to override menus
        self.configure_menu_actions()
        # Interface for subclasses to handle actions
        self.connect_actions()
        # Interface for initializing actions
        self.load_settings()

    def by_text(self):
        """Returns a list with all actions, sorted by the display text,
        ignoring the & mmemonic character."""
        result = list(self._actions.values())
        result.sort(
            key=lambda action: ''.join(c for c in action.text() if c != "&"))
        return result

    def configure_menu_actions(self):
        """Can be used in subclasses to configure the menu action behaviour.
        Calling self.set_menu_action_list(target, actions) each of the menus
        can be configured separately (see comments there)."""
        pass

    def connect_actions(self):
        """Should be implemented when actions have to be connected
        globally during the extension's lifetime. Alternatively
        the actions can also
        """
        pass

    def extension(self):
        return self._extension

    def load_settings(self):
        """Should be implemented to initialize the actions."""
        pass

    def menu_actions(self, target):
        """Returns a list of actions for use in the extension's entry
        in a menu. By default this is a list of all available
        actions, sorted by the display text. For custom sorting or
        a custom selection this method can be overridden."""
        action_list = self._action_lists.get(target, None)
        if action_list is None:
            action_list = self._action_lists[target] = self.by_text()
        return action_list

    def set_menu_action_list(self, target, actions):
        """Specify the contents of a menu.
        Each entry in the _action_lists dictionary can be None or a list.
        If it is None then the self.by_text() method is used to create a flat
        list of all actions, sorted by display name (default for Tools menu). Otherwise a list of actions or submenus can be stored. The context menus
        are initialized to empty lists, meaning by default an extension does
        *not* get an entry in any context menu.
        """
        self._action_lists[target] = actions
