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
UrlRequester, a lineedit with a Browse-button.
"""


from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLineEdit, QToolButton, QWidget)

import app
import icons


class UrlRequester(QWidget):
    """Shows a lineedit and a button to select a file or directory.

    The lineEdit, button, and fileDialog attributes represent their
    respective objects.

    """
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super(UrlRequester, self).__init__(parent)

        self._fileDialog = None
        self._dialogTitle = None
        self._fileMode = None

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        self.lineEdit = QLineEdit()
        layout.addWidget(self.lineEdit)
        self.button = QToolButton(clicked=self.browse)
        layout.addWidget(self.button)

        self.lineEdit.textChanged.connect(self.changed)
        self.setFileMode(QFileDialog.Directory)
        app.translateUI(self)

    def translateUI(self):
        self.button.setToolTip(_("Open file dialog"))

    def fileDialog(self, create = False):
        """Returns the QFileDialog, if already instantiated.

        If create is True, the dialog is instantiated anyhow.

        """
        if create and self._fileDialog is None:
            self._fileDialog = QFileDialog(self)
        return self._fileDialog

    def setPath(self, path):
        self.lineEdit.setText(path)

    def path(self):
        return self.lineEdit.text()

    def setFileMode(self, mode):
        """Sets the mode for the dialog, is a QFileDialog.FileMode value."""
        if mode == QFileDialog.Directory:
            self.button.setIcon(icons.get('folder-open'))
        else:
            self.button.setIcon(icons.get('document-open'))
        self._fileMode = mode

    def fileMode(self):
        return self._fileMode

    def setDialogTitle(self, title):
        self._dialogTitle = title
        if self._fileDialog:
            self._fileDialog.setWindowTitle(title)

    def dialogTitle(self):
        return self._dialogTitle

    def browse(self):
        """Opens the dialog."""
        dlg = self.fileDialog(True)
        dlg.setFileMode(self._fileMode)
        if self._dialogTitle:
            title = self._dialogTitle
        elif self.fileMode() == QFileDialog.Directory:
            title = _("Select a directory")
        else:
            title = _("Select a file")
        dlg.setWindowTitle(app.caption(title))
        dlg.selectFile(self.path())
        result = dlg.exec_()
        if result:
            self.lineEdit.setText(dlg.selectedFiles()[0])


