# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2012 by Wilbert Berendsen
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

from PyQt4.QtCore import QSize, Qt
from PyQt4.QtGui import QFontMetrics, QPainter, QWidget


class LineNumberArea(QWidget):
    def __init__(self, textedit):
        super(LineNumberArea, self).__init__(textedit)
        self._width = 0
        self.setAutoFillBackground(True)
        textedit.updateRequest.connect(self.slotUpdateRequest)
        textedit.blockCountChanged.connect(self.updateWidth)
        self.updateWidth()
        
    def textedit(self):
        return self.parent()
        
    def sizeHint(self):
        return QSize(self._width, 50)

    def updateWidth(self):
        fm = QFontMetrics(self.parent().font())
        txt = format(self.parent().blockCount(), 'd')
        self._width = fm.width(txt) + 3
        self.adjustSize()

    def slotUpdateRequest(self, rect, dy):
        if (dy):
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

    def paintEvent(self, ev):
        edit = self.parent()
        painter = QPainter(self)
        painter.setFont(edit.font())
        height = QFontMetrics(edit.font()).height()
        block = edit.firstVisibleBlock()
        while block.isValid():
            geom = edit.blockBoundingGeometry(block)
            geom.translate(edit.contentOffset())
            if geom.top() >= ev.rect().bottom():
                break
            if block.isVisible() and geom.bottom() > ev.rect().top() + 1:
                txt = format(block.blockNumber() + 1, 'd')
                painter.drawText(0, geom.top(), self.width() - 1, height,
                    Qt.AlignRight, txt)
            block = block.next()

