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
A lineedit with a clear button.
"""



from PyQt5.QtCore import QEvent, QSize, Qt
from PyQt5.QtWidgets import QLineEdit, QStyle, QToolButton

import icons

class LineEdit(QLineEdit):
    """A QLineEdit with a clear button. No additional methods."""
    def __init__(self, *args, **kwargs):
        super(LineEdit, self).__init__(*args, **kwargs)
        self._clearButton = b = QToolButton(self, iconSize=QSize(16,16), autoRaise=True)
        b.setFixedSize(QSize(16, 16))
        b.setStyleSheet("QToolButton { border: none; }")
        b.clicked.connect(self.clear)
        b.setCursor(Qt.ArrowCursor)
        b.setFocusPolicy(Qt.NoFocus)
        self.textChanged.connect(self._updateClearButton)
        self._updateLayoutDirection()
        self._updateClearButton()

    def _updateLayoutDirection(self):
        b = self._clearButton
        if self.layoutDirection() == Qt.RightToLeft:
            self.setTextMargins(b.width(), 0, 0, 0)
            b.setIcon(icons.get('edit-clear-locationbar-ltr'))
        else:
            self.setTextMargins(0, 0, b.width(), 0)
            b.setIcon(icons.get('edit-clear-locationbar-rtl'))

    def _updateClearButton(self):
        b = self._clearButton
        if self.text():
            frame = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
            y = max(0, (self.height() - b.height()) / 2)
            if self.layoutDirection() == Qt.RightToLeft:
                x = frame + 2
            else:
                x = self.rect().right() - b.width() - frame - 2
            b.move(x, y)
            b.show()
        else:
            b.hide()

    def resizeEvent(self, ev):
        super(LineEdit, self).resizeEvent(ev)
        if self.text():
            self._updateClearButton()

    def changeEvent(self, ev):
        super(LineEdit, self).changeEvent(ev)
        if ev.type() == QEvent.LayoutDirectionChange:
            self._updateLayoutDirection()
            self._updateClearButton()


