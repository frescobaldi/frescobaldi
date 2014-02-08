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
This handles the QEvent::FileOpen event type sent to the QApplication when
a file is clicked in the file manager.

Currently this makes only sense on Mac OS X.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QEvent, QObject
from PyQt4.QtGui import QApplication

import app


def openUrl(url):
    """Open Url.
    
    If there is an active MainWindow, the document is made the current
    document in that window. If there is no MainWindow at all, it is
    created.
    
    """
    if not app.windows:
        import mainwindow
        mainwindow.MainWindow().show()
    win = QApplication.activeWindow()
    if win not in app.windows:
        win = app.windows[0]
    doc = win.openUrl(url)
    if doc:
        win.setCurrentDocument(doc)


class FileOpenEventHandler(QObject):
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.FileOpen:
            openUrl(ev.url())
            return True
        return False


handler = FileOpenEventHandler()
app.qApp.installEventFilter(handler)


