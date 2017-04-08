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
A line number area to be used in a QPlainTextEdit.
"""

from PyQt5.QtCore import QEvent, QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QFontMetrics, QMouseEvent, QPainter
from PyQt5.QtWidgets import QApplication, QWidget


class LineNumberArea(QWidget):
    def __init__(self, textedit=None):
        super(LineNumberArea, self).__init__(textedit)
        self._textedit = None
        self.setAutoFillBackground(True)
        self.setTextEdit(textedit)

    def setTextEdit(self, edit):
        """Sets a QPlainTextEdit instance to show linenumbers for, or None."""
        if self._textedit:
            self._textedit.updateRequest.disconnect(self.slotUpdateRequest)
            self._textedit.blockCountChanged.disconnect(self.updateWidth)
        self._textedit = edit
        if edit:
            edit.updateRequest.connect(self.slotUpdateRequest)
            edit.blockCountChanged.connect(self.updateWidth)
            self.updateWidth()
        else:
            self._width = 0
        self.update()

    def textEdit(self):
        """Returns our QPlainTextEdit."""
        return self._textedit

    def sizeHint(self):
        return QSize(self._width, 50)

    def updateWidth(self):
        fm = QFontMetrics(self._textedit.font())
        text = format(self._textedit.blockCount(), 'd')
        self._width = fm.width(text) + 3
        self.adjustSize()

    def slotUpdateRequest(self, rect, dy):
        if (dy):
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

    def paintEvent(self, ev):
        edit = self._textedit
        if not edit:
            return
        painter = QPainter(self)
        painter.setFont(edit.font())
        rect = QRect(0, 0, self.width() - 2, QFontMetrics(edit.font()).height())
        block = edit.firstVisibleBlock()
        while block.isValid():
            geom = edit.blockBoundingGeometry(block)
            geom.translate(edit.contentOffset())
            if geom.top() >= ev.rect().bottom():
                break
            if block.isVisible() and geom.bottom() > ev.rect().top() + 1:
                rect.moveTop(geom.top())
                text = format(block.blockNumber() + 1, 'd')
                painter.drawText(rect, Qt.AlignRight, text)
            block = block.next()

    def event(self, ev):
        if self._textedit:
            if ((ev.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease)
                 and ev.button() == Qt.LeftButton)
                or (ev.type() == QEvent.MouseMove and ev.buttons() & Qt.LeftButton)):
                new = QMouseEvent(ev.type(), QPoint(0, ev.y()),
                    ev.button(), ev.buttons(), ev.modifiers())
                return QApplication.sendEvent(self._textedit.viewport(), new)
            elif ev.type() == QEvent.Wheel:
                return QApplication.sendEvent(self._textedit.viewport(), ev)
        return super(LineNumberArea, self).event(ev)



