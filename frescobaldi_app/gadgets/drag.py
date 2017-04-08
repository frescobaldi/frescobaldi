# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Event-filtering objects and helper functions to drag things.
"""


from PyQt5.QtCore import QEvent, QFileInfo, QMimeData, QObject, Qt, QUrl
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QApplication, QFileIconProvider


class ComboDrag(QObject):
    """Enables dragging from a QComboBox.

    Instantiate this with a QComboBox as parent to enable dragging the
    current item.

    By default, drags a filename got from the current index under the
    Qt.EditRole. Change the role by changing the 'role' instance attribute.

    """
    column = 0
    role = Qt.EditRole

    def __init__(self, combobox):
        super(ComboDrag, self).__init__(combobox)
        self._dragpos = None
        combobox.installEventFilter(self)

    def eventFilter(self, combobox, ev):
        if ev.type() == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
            self._dragpos = ev.pos()
            return not combobox.isEditable()
        elif (ev.type() == QEvent.MouseMove and ev.buttons() & Qt.LeftButton
              and combobox.count() >0):
            return self.mouseMoved(combobox, ev.pos()) or False
        elif (ev.type() == QEvent.MouseButtonRelease
            and ev.button() == Qt.LeftButton and not combobox.isEditable()):
            combobox.mousePressEvent(ev)
        return False

    def mouseMoved(self, combobox, pos):
        if (self._dragpos is not None
            and (pos - self._dragpos).manhattanLength()
                >= QApplication.startDragDistance()):
            self.startDrag(combobox)
            return True

    def startDrag(self, combobox):
        index = combobox.model().index(combobox.currentIndex(), self.column)
        filename = combobox.model().data(index, self.role)
        icon = combobox.model().data(index, Qt.DecorationRole)
        dragFile(combobox, filename, icon, Qt.CopyAction)


class Dragger(QObject):
    """Drags anything from any widget.

    Use dragger.installEventFilter(widget) to have it drag.

    """
    def __init__(self, parent=None):
        super(Dragger, self).__init__(parent)
        self._dragpos = None
        if parent:
            parent.installEventFilter(self)

    def eventFilter(self, widget, ev):
        if ev.type() == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
            self._dragpos = ev.pos()
            return True
        elif ev.type() == QEvent.MouseMove and ev.buttons() & Qt.LeftButton:
            return self.mouseMoved(widget, ev.pos()) or False
        return False

    def mouseMoved(self, widget, pos):
        if (self._dragpos is not None
            and (pos - self._dragpos).manhattanLength()
                >= QApplication.startDragDistance()):
            self.startDrag(widget)
            return True

    def startDrag(self, widget):
        """Reimplement to start a drag."""


class FileDragger(Dragger):
    def filename(self):
        """Should return the filename to drag."""

    def startDrag(self, widget):
        filename = self.filename()
        if filename:
            dragFile(widget, filename)


def dragFile(widget, filename, icon=None, dropactions=Qt.CopyAction):
    """Starts dragging the given local file from the widget."""
    if icon is None or icon.isNull():
        icon = QFileIconProvider().icon(QFileInfo(filename))
    drag = QDrag(widget)
    data = QMimeData()
    data.setUrls([QUrl.fromLocalFile(filename)])
    drag.setMimeData(data)
    drag.setPixmap(icon.pixmap(32))
    drag.exec_(dropactions)


