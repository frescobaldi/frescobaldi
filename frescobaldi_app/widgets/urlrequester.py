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

import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QWidget
)

import app
import icons


class UrlRequester(QWidget):
    """Shows a lineedit and a button to select a file or directory.

    The lineEdit, button, and fileDialog attributes represent their
    respective objects.

    """
    changed = pyqtSignal()
    editingFinished = pyqtSignal()

    def __init__(
        self,
        parent=None,
        fileMode=QFileDialog.Directory,
        mustExist=False
    ):
        super(UrlRequester, self).__init__(parent)

        self._fileDialog = None
        self._dialogTitle = None
        self._mustExist = mustExist
        self._originalPath = ''

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        self.lineEdit = QLineEdit()
        layout.addWidget(self.lineEdit)
        self.button = QToolButton(clicked=self.browse)
        layout.addWidget(self.button)

        self.lineEdit.textChanged.connect(self._changed)
        self.lineEdit.editingFinished.connect(self._editingFinished)
        self._browse_clicked = False
        self.setFileMode(fileMode)
        app.translateUI(self)

    def translateUI(self):
        self.button.setToolTip(_("Open file dialog"))

    def _changed(self):
        """
        Emit the `changed` signal.
        If the `mustExist` property is set validate the current value
        and color the line edit.
        """
        if self.mustExist():
            if os.path.exists(self.path()):
                self.lineEdit.setStyleSheet('')
            else:
                # TODO: Apply the "Error" color of the current theme
                self.lineEdit.setStyleSheet('color:red')
        self.changed.emit()

    def _editingFinished(self):
        """Emit the editingFinished signal - if validation passes.

        If the focus changes from the lineEdit to the fileDialog
        no signal is emitted.

        If mustExist=True and the file doesn't exist, reset to the value
        before editing and suppress the signal.

        Only emit the signal if the path has actually changed.
        """
        if self._browse_clicked:
            self.fileDialog().setDirectory(self.lineEdit.text())
        elif self.mustExist() and not os.path.exists(self.path()):
            self.setPath(self._originalPath)
        elif self.path() != self._originalPath:
            self._originalPath = self.path()
            self.editingFinished.emit()

    def fileDialog(self, create=False):
        """Returns the QFileDialog, if already instantiated.

        If create is True, the dialog is instantiated anyhow.

        """
        if create and self._fileDialog is None:
            self._fileDialog = QFileDialog(self)
        return self._fileDialog

    def setPath(self, path):
        self._originalPath = path
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

    def mustExist(self):
        return self._mustExist

    def setMustExist(self, value):
        self._mustExist = value

    def setDialogTitle(self, title):
        self._dialogTitle = title
        if self._fileDialog:
            self._fileDialog.setWindowTitle(title)

    def dialogTitle(self):
        return self._dialogTitle

    def browse(self):
        """Opens the dialog."""
        # Suppress the editingFinished signal from the LineEdit
        self._browse_clicked = True
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
        self._browse_clicked = False
        if result:
            new = dlg.selectedFiles()[0]
            self.lineEdit.setText(new)
            self._editingFinished()
