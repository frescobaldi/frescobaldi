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

Currently this makes only sense on Mac OS X.
"""


from PyQt5.QtCore import QEvent, QMimeData, QObject, QPoint, Qt
from PyQt5.QtWidgets import QApplication, QStyle
from PyQt5.QtGui import QDrag

import app


handler = None


class IconDragEventHandler(QObject):
    """Event handler to handle window icon events on Mac OS X."""
    def eventFilter(self, mainwin, ev):
        if ev.type() != QEvent.IconDrag:
            return False
        if not mainwin.isActiveWindow():
            return False
        ev.accept()
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.NoModifier:
            self.startDrag(mainwin, ev)
        elif modifiers == Qt.ControlModifier:
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
        pixmap = mainwin.style().standardPixmap(QStyle.SP_FileIcon, 0, mainwin)
        hotspot = QPoint(pixmap.width() - 5, 5)
        drag.setPixmap(pixmap)
        drag.setHotSpot(hotspot)
        drag.start(Qt.LinkAction | Qt.CopyAction)

    def commandClick(self, mainwin, ev):
        """Called on Command-click the window icon (Mac OS X)."""
        pass


def initialize():
    global handler
    handler = IconDragEventHandler()

@app.mainwindowCreated.connect
def windowCreated(window):
    window.installEventFilter(handler)


