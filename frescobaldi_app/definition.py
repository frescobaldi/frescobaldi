# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2014 - 2014 by Wilbert Berendsen
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
Find the definition of variables.
"""


from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QTextCursor

import app
import documentinfo
import ly.music.items
import browseriface


def refnode(cursor):
    """Return the music item at the cursor if that probably is a reference to a definition elsewhere."""
    node = documentinfo.music(cursor.document()).node(cursor.position())
    if (node and node.end_position() >= cursor.selectionEnd()
        and isinstance(node, (
                ly.music.items.UserCommand,
                ly.music.items.MarkupUserCommand,
        ))):
        return node


def target(node):
    """Return the target node (where the node is defined)."""
    value = node.value()
    if value:
        target = value.parent()
        if isinstance(target, ly.music.items.Document):
            target = value # happens with #(define-markup-command ...)
        return target


def goto_definition(mainwindow, cursor=None):
    """Go to the definition of the item the mainwindow's cursor is at.

    Return True if there was a definition.

    """
    if cursor is None:
        cursor = mainwindow.textCursor()
    node = refnode(cursor)
    if node:
        t = target(node)
        if t:
            goto_target(mainwindow, t)
            return True


def goto_target(mainwindow, target):
    """Switch to the document and location where the node target is."""
    lydoc = target.document
    try:
        # this succeeds if this is a document that is currently open
        doc = lydoc.document
    except AttributeError:
        # it is an included file, just load it
        filename = target.document.filename
        doc = app.openUrl(QUrl.fromLocalFile(filename))
    cursor = QTextCursor(doc)
    cursor.setPosition(target.position)
    browseriface.get(mainwindow).setTextCursor(cursor)
    mainwindow.currentView().centerCursor()


