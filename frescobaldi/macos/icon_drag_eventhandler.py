# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
This handles the QEvent::IconDrag event type sent to the mainwindow when
the window icon is Command-clicked or dragged.

Currently this makes only sense on macOS.
"""


from PyQt6.QtCore import QEvent, QMimeData, QObject, QPoint, Qt
from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtGui import QDrag

import app


handler = None


class IconDragEventHandler(QObject):
    """Event handler to handle window icon events on macOS."""
    def eventFilter(self, mainwin, ev):
        if ev.type() != QEvent.Type.IconDrag:
            return False
        if not mainwin.isActiveWindow():
            return False
        ev.accept()
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.KeyboardModifier.NoModifier:
            self.startDrag(mainwin, ev)
        elif modifiers == Qt.KeyboardModifier.ControlModifier:
            self.commandClick(mainwin, ev)
        else:
            ev.ignore()
        return True

    def startDrag(self, mainwin, ev):
        d = mainwin.currentDocument()
        if not d:
            return
        url = d.url()
        if url.isEmpty():
            return
        drag = QDrag(mainwin)
        data = QMimeData()
        data.setUrls([url])
        drag.setMimeData(data)
        pixmap = mainwin.style().standardPixmap(QStyle.StandardPixmap.SP_FileIcon, 0, mainwin)
        hotspot = QPoint(pixmap.width() - 5, 5)
        drag.setPixmap(pixmap)
        drag.setHotSpot(hotspot)
        drag.start(Qt.DropAction.LinkAction | Qt.DropAction.CopyAction)

    def commandClick(self, mainwin, ev):
        """Called on Command-click the window icon (macOS)."""
        pass


def initialize():
    global handler
    handler = IconDragEventHandler()

@app.mainwindowCreated.connect
def windowCreated(window):
    window.installEventFilter(handler)
