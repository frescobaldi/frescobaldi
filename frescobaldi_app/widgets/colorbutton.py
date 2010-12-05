# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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


from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QColor, QColorDialog, QPalette, QPushButton


from .. import (
    app,
)


class ColorButton(QPushButton):
    
    colorChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super(ColorButton, self).__init__(parent)
        
        self.setFixedSize(self.sizeHint())
        app.languageChanged.connect(self.translateUI)
        self.translateUI()
        self._color = QColor()
        self.clicked.connect(self.openDialog)
    
    def translateUI(self):
        self.setToolTip(_("Click to select a different color."))
        
    def color(self):
        return self._color
    
    def setColor(self, color):
        self._color = color
        p = self.palette()
        p.setColor(QPalette.Button, color)
        self.setPalette(p)

    def openDialog(self):
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self.setColor(color)
            self.colorChanged.emit()

