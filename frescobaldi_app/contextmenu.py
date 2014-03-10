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
The contextmenu of the editor.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QAction

import icons
import util
import app


def contextmenu(view):
    cursor = view.textCursor()
    menu = view.createStandardContextMenu()
    mainwindow = view.window()
    
    # create the actions in the actions list
    actions = []
    
    actions.extend(open_files(cursor, menu, mainwindow))
    
    if cursor.hasSelection():
        import panelmanager
        actions.append(panelmanager.manager(mainwindow).snippettool.actionCollection.copy_to_snippet)
        actions.append(mainwindow.actionCollection.edit_copy_colored_html)
    
    # now add the actions to the standard menu
    if actions:
        first_action = menu.actions()[0] if menu.actions() else None
        if first_action:
            first_action = menu.insertSeparator(first_action)
            menu.insertActions(first_action, actions)
        else:
            menu.addActions(actions)
    return menu


def open_files(cursor, menu, mainwindow):
    """Return a list of actions (maybe empty) for files at the cursor to open."""
    def action(filename):
        url = QUrl.fromLocalFile(filename)
        a = QAction(menu)
        a.setText(_("Open \"{url}\"").format(url=util.homify(filename)))
        a.setIcon(icons.get('document-open'))
        @a.triggered.connect
        def open_doc():
            d = mainwindow.openUrl(url)
            mainwindow.setCurrentDocument(d)
        return a
    import open_file_at_cursor
    return list(map(action, open_file_at_cursor.filenames_at_cursor(cursor)))

