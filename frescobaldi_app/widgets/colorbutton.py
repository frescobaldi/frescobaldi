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
A button to select a color.
"""


from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (
    QColorDialog, QPushButton, QStyle, QStyleOptionButton,
    qDrawShadeRect)


class ColorButton(QPushButton):
    """A PushButton displaying a color.

    When clicked, opens a color dialog to change the color.

    """
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super(ColorButton, self).__init__(parent)

        self.setFixedSize(self.sizeHint())
        self._color = QColor()
        self.clicked.connect(self.openDialog)

    def color(self):
        """Returns the currently set color."""
        return self._color

    def setColor(self, color):
        """Sets the current color. Maybe QColor() to indicate 'unset'."""
        if self._color != color:
            self._color = color
            self.update()
            self.colorChanged.emit(color)

    def clear(self):
        """Unsets the current color (setting it to QColor())."""
        self.setColor(QColor())

    def openDialog(self):
        """Called when clicked, opens a dialog to change the color."""
        color = self._color if self._color.isValid() else QColor(Qt.white)
        color = QColorDialog.getColor(color, self)
        if color.isValid():
            self.setColor(color)

    def paintEvent(self, ev):
        """Reimplemented to display a colored rectangle."""
        QPushButton.paintEvent(self, ev)
        if not self._color.isValid():
            return
        style = self.style()
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        r = style.subElementRect(QStyle.SE_PushButtonContents, opt, self)
        shift = style.pixelMetric(QStyle.PM_ButtonMargin, opt, self) // 2
        r.adjust(shift, shift, -shift, -shift)
        if self.isChecked() or self.isDown():
            dx = style.pixelMetric(QStyle.PM_ButtonShiftHorizontal, opt, self)
            dy = style.pixelMetric(QStyle.PM_ButtonShiftVertical, opt, self)
            r.translate(dx, dy)
        p = QPainter(self)
        qDrawShadeRect(p, r, self.palette(), True, 1, 0, self._color)

