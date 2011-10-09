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

"""
A basic Dialog class.
"""

from __future__ import unicode_literals

import functools
import operator

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import Separator

standardicons = {
    'info': QStyle.SP_MessageBoxInformation,
    'warning': QStyle.SP_MessageBoxWarning,
    'critical': QStyle.SP_MessageBoxCritical,
    'question': QStyle.SP_MessageBoxQuestion,
}

standardbuttons = {
    'ok': QDialogButtonBox.Ok,
    'open': QDialogButtonBox.Open,
    'save': QDialogButtonBox.Save,
    'cancel': QDialogButtonBox.Cancel,
    'close': QDialogButtonBox.Close,
    'discard': QDialogButtonBox.Discard,
    'apply': QDialogButtonBox.Apply,
    'reset': QDialogButtonBox.Reset,
    'restoredefaults': QDialogButtonBox.RestoreDefaults,
    'help': QDialogButtonBox.Help,
    'saveall': QDialogButtonBox.SaveAll,
    'yes': QDialogButtonBox.Yes,
    'yestoall': QDialogButtonBox.YesToAll,
    'no': QDialogButtonBox.No,
    'notoall': QDialogButtonBox.NoToAll,
    'abort': QDialogButtonBox.Abort,
    'retry': QDialogButtonBox.Retry,
    'ignore': QDialogButtonBox.Ignore,
}


class Dialog(QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self._icon = QIcon()
        self._iconSize = QSize(64, 64)
        self._buttonOrientation = Qt.Horizontal
        self._separator = True
        self._separatorWidget = Separator()
        self._mainWidget = QWidget()
        self._pixmap = QPixmap()
        self._pixmapLabel = QLabel(self)
        self._textLabel = QLabel(self)
        self._buttonBox = b = QDialogButtonBox(self)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        b.helpRequested.connect(self.helpRequest)
        layout = QGridLayout()
        layout.setSpacing(10)
        self.setLayout(layout)
        self.setStandardButtons(['ok', 'cancel'])
        self.reLayout()
        
    def helpRequest(self):
        pass
    
    def setButtonOrientation(self, orientation):
        if orientation != self._buttonOrientation:
            self._buttonOrientation = orientation
            self._buttonBox.setOrientation(orientation)
            self.reLayout()
    
    def buttonOrientation(self):
        return self._buttonOrientation
        
    def setIcon(self, icon):
        """Sets the icon.
        
        Maybe:
        - None or QIcon()
        - one of 'info', 'warning', 'critical', 'question'
        - a QStyle.StandardPixmap
        - a QIcon.
        
        """
        if icon in standardicons:
            icon = standardicons[icon]
        if isinstance(icon, QStyle.StandardPixmap):
            icon = self.style().standardIcon(icon)
        if icon is None:
            icon = QIcon()
        self._icon = icon
        self.setPixmap(icon.pixmap(self._iconSize))
    
    def icon(self):
        return self._icon
        
    def setIconSize(self, size):
        changed = size != self._iconSize
        self._iconSize = size
        if changed and not self._icon.isNull():
            self.setPixmap(self._icon.pixmap(size))
    
    def iconSize(self):
        return self._iconSize
        
    def setPixmap(self, pixmap):
        changed = self._pixmap.isNull() != pixmap.isNull()
        self._pixmap = pixmap
        self._pixmapLabel.setPixmap(pixmap)
        if not pixmap.isNull():
            self._pixmapLabel.setFixedSize(pixmap.size())
        if changed:
            self.reLayout()
        
    def pixmap(self):
        return self._pixmap
    
    def setText(self, text):
        self._textLabel.setText(text)
    
    def text(self):
        return self._textLabel.text()
    
    def buttonBox(self):
        return self._buttonBox
    
    def setStandardButtons(self, buttons):
        if isinstance(buttons, (set, tuple, list)):
            buttons = functools.reduce(operator.or_,
                map(standardbuttons.get, buttons),
                QDialogButtonBox.StandardButtons())
        self._buttonBox.setStandardButtons(buttons)
        
    def setSeparator(self, enabled):
        changed = self._separator != enabled
        self._separator = enabled
        if changed:
            self.reLayout()
            
    def setMainWidget(self, widget):
        self._mainWidget = widget
        self.reLayout()
    
    def mainWidget(self):
        return self._mainWidget
    
    def reLayout(self):
        layout = self.layout()
        while layout.takeAt(0):
            pass
        
        if not self._pixmap.isNull():
            col = 1
            layout.addWidget(self._pixmapLabel, 0, 0, 2, 1)
        else:
            layout.setColumnStretch(1, 0)
            col = 0
        layout.setColumnStretch(col, 1)
        self._pixmapLabel.setVisible(not self._pixmap.isNull())    
        layout.addWidget(self._textLabel, 0, col)
        layout.addWidget(self._mainWidget, 1, col)
        if self._buttonOrientation == Qt.Horizontal:
            if self._separator:
                layout.addWidget(self._separatorWidget, 2, 0, 1, col+1)
            layout.addWidget(self._buttonBox, 3, 0, 1, col+1)
        else:
            if self._separator:
                layout.addWidget(self._separatorWidget, 0, col+1, 2, 1)
            layout.addWidget(self._buttonBox, 0, col+2, 2, 1)
        self._separatorWidget.setVisible(self._separator)
            
