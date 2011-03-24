# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
A button to select a color.
"""


from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QApplication, QColor, QColorDialog, QPalette, QPushButton


import app


class ColorButton(QPushButton):
    
    colorChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super(ColorButton, self).__init__(parent)
        
        self.setFixedSize(self.sizeHint())
        app.translateUI(self)
        self._color = QColor()
        self.clicked.connect(self.openDialog)
    
    def translateUI(self):
        self.setToolTip(_("Click to select a different color."))
        
    def color(self):
        return self._color
    
    def setColor(self, color):
        self._color = color
        p = QApplication.palette()
        if color.isValid():
            p.setColor(QPalette.Button, color)
        self.setPalette(p)

    def clear(self):
        self.setColor(QColor())
        self.colorChanged.emit()
        
    def openDialog(self):
        color = self._color if self._color.isValid() else QColor(Qt.white)
        color = QColorDialog.getColor(color, self)
        if color.isValid():
            self.setColor(color)
            self.colorChanged.emit()

