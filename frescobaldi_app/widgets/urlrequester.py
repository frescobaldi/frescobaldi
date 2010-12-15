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
UrlRequester, a lineedit with a Browse-button.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
)


class UrlRequester(QWidget):
    """Shows a lineedit and a button to select a file or directory.
    
    The lineEdit, button, and fileDialog attributes represent their
    respective objects.
    
    """
    changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super(UrlRequester, self).__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)
        
        self.lineEdit = QLineEdit()
        layout.addWidget(self.lineEdit)
        self.button = QToolButton(clicked=self.browse)
        layout.addWidget(self.button)
        
        self.fileDialog = QFileDialog(self)
        self.setFileMode(QFileDialog.Directory)
        
        self.lineEdit.textChanged.connect(self.changed)
        
        completer = QCompleter(self.lineEdit)
        model = QFileSystemModel(completer)
        model.setRootPath(QDir.homePath())
        model.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        completer.setModel(model)
        self.lineEdit.setCompleter(completer)
        
        app.translateUI(self)
        
    def translateUI(self):
        pass
    
    def setPath(self, path):
        self.lineEdit.setText(path)
        
    def path(self):
        return self.lineEdit.text()
        
    def setFileMode(self, mode):
        """Sets the mode for the dialog, is a QFileDialog.FileMode value."""
        if mode == QFileDialog.Directory:
            self.button.setIcon(icons.get('document-open-folder'))
        else:
            self.button.setIcon(icons.get('document-open'))
        self.fileDialog.setFileMode(mode)
    
    def browse(self):
        """Opens the dialog."""
        if not self.fileDialog.windowTitle():
            if self.fileDialog.fileMode() == QFileDialog.Directory:
                title = _("Select a directory")
            else:
                title = _("Select a file")
            self.fileDialog.setWindowTitle(app.caption(title))
        self.fileDialog.selectFile(self.path())
        result =  self.fileDialog.exec_()
        if result:
            self.lineEdit.setText(self.fileDialog.selectedFiles()[0])
        

