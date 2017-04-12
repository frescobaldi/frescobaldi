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
Provides a browser-like interface for switching documents and cursor positions.

Remembers the current position and view when jumping to another location.
Provides buttons to go back or forward.

"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import app
import actioncollection
import actioncollectionmanager
import plugin
import icons


class Position(object):
    cursor = None
    find_open_view = None


def get(mainwindow):
    """Returns the BrowserIface instance for the specified MainWindow."""
    return BrowserIface.instance(mainwindow)


class BrowserIface(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.go_back.triggered.connect(self.goBack)
        ac.go_forward.triggered.connect(self.goForward)
        app.documentClosed.connect(self._documentClosed)
        self._history = [Position()]
        self._index = 0    # the index points to the current position
        self.updateActions()

    def goBack(self):
        """Called when the user activates the go_back action."""
        if self._index > 0:
            self._history[self._index].cursor = self.mainwindow().textCursor()
            self._index -= 1
            p = self._history[self._index]
            self.mainwindow().setTextCursor(p.cursor, p.find_open_view)
            self.updateActions()

    def goForward(self):
        """Called when the user activates the go_forward action."""
        if self._index < len(self._history) - 1:
            self._history[self._index].cursor = self.mainwindow().textCursor()
            self._index += 1
            p = self._history[self._index]
            self.mainwindow().setTextCursor(p.cursor, p.find_open_view)
            self.updateActions()

    def setTextCursor(self, cursor, findOpenView=None):
        """Move to the new cursor position and remember the current one."""
        self._remember(findOpenView)
        self.mainwindow().setTextCursor(cursor, findOpenView)

    def setCurrentDocument(self, doc, findOpenView=None):
        """Switch to a different document and remember the current cursor position."""
        self._remember(findOpenView)
        self.mainwindow().setCurrentDocument(doc, findOpenView)

    def updateActions(self):
        """Update the actions depending on current position in history."""
        self.actionCollection.go_back.setEnabled(self._index > 0)
        self.actionCollection.go_forward.setEnabled(self._index < len(self._history) - 1)

    def _remember(self, findOpenView):
        """(Internal) Remember the current cursor position and whether a new view was requested."""
        pos = self._history[self._index]
        pos.cursor = self.mainwindow().textCursor()
        pos.find_open_view = findOpenView
        self._index += 1
        del self._history[self._index:]
        self._history.append(Position())
        self.updateActions()

    def _documentClosed(self, doc):
        """(Internal) Called when a document is closed.

        Removes the positions in the history of that document.

        """
        for i, pos in reversed(list(enumerate(self._history))):   # copy
            if pos.cursor and doc is pos.cursor.document():
                del self._history[i]
                if self._index > i:
                    self._index -= 1
        if not self._history:
            self._history = [Position()]
        if self._index > len(self._history) - 1:
            self._index = len(self._history) - 1
        self.updateActions()


class Actions(actioncollection.ActionCollection):
    name = "browseriface"
    def createActions(self, parent):
        self.go_back = QAction(parent)
        self.go_forward = QAction(parent)

        self.go_back.setIcon(icons.get('go-previous'))
        self.go_forward.setIcon(icons.get('go-next'))

        self.go_back.setShortcut(QKeySequence(Qt.ALT + Qt.Key_Backspace))
        self.go_forward.setShortcut(QKeySequence(Qt.ALT + Qt.Key_End))

    def translateUI(self):
        self.go_back.setText(_("Go to previous position"))
        self.go_back.setIconText(_("Back"))
        self.go_forward.setText(_("Go to next position"))
        self.go_forward.setIconText(_("Forward"))

