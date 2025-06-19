# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2019 by Wilbert Berendsen
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
Dialog to copy contents from PDF to a raster image.
"""


import os

from PyQt6.QtCore import QSettings, QSize, Qt
from PyQt6.QtGui import QColor, QDoubleValidator
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout)

import app
import qutil
import icons
import qpageview.backgroundjob
import qpageview.imageview
import qpageview.export
import widgets.colorbutton


def copy_image(parent_widget, page, rect=None, filename=None):
    """Shows the dialog to copy a PDF page to a raster image.

    If rect is given, only that part of the page is copied.

    """
    dlg = Dialog(parent_widget)
    dlg.show()
    dlg.setPage(page, rect, filename)
    dlg.finished.connect(dlg.deleteLater)


class Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filename = None
        self._page = None
        self._rect = None
        self._exporter = None
        self.runJob = qpageview.backgroundjob.SingleRun()
        self.imageViewer = qpageview.imageview.ImageView()
        self.dpiLabel = QLabel()
        self.dpiCombo = QComboBox(insertPolicy=QComboBox.InsertPolicy.NoInsert, editable=True)
        self.dpiCombo.lineEdit().setCompleter(None)
        self.dpiCombo.setValidator(QDoubleValidator(10.0, 1200.0, 4, self.dpiCombo))
        self.dpiCombo.addItems([format(i) for i in (72, 100, 200, 300, 600, 1200)])

        self.colorCheck = QCheckBox(checked=False)
        self.colorButton = widgets.colorbutton.ColorButton()
        self.colorButton.setColor(QColor(Qt.GlobalColor.white))
        self.grayscale = QCheckBox(checked=False)
        self.crop = QCheckBox()
        self.antialias = QCheckBox(checked=True)
        self.scaleup = QCheckBox(checked=False)
        self.dragfile = QPushButton(icons.get("image-x-generic"), None, None)
        self.copyfile = QPushButton(icons.get('edit-copy'), None, None)
        self.dragdata = QPushButton(icons.get("image-x-generic"), None, None)
        self.copydata = QPushButton(icons.get('edit-copy'), None, None)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.saveButton = self.buttons.addButton('', QDialogButtonBox.ButtonRole.ApplyRole)
        self.saveButton.setIcon(icons.get('document-save'))

        layout = QVBoxLayout()
        self.setLayout(layout)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.imageViewer)

        controls = QGridLayout()
        hlayout.addLayout(controls)
        controls.addWidget(self.dpiLabel, 0, 0)
        controls.addWidget(self.dpiCombo, 0, 1)
        colorLayout = QHBoxLayout()
        colorLayout.setContentsMargins(0, 0, 0, 0)
        colorLayout.addWidget(self.colorCheck)
        colorLayout.addWidget(self.colorButton)
        controls.addLayout(colorLayout, 2, 0, 1, 2)
        controls.addWidget(self.grayscale, 3, 0, 1, 2)
        controls.addWidget(self.crop, 4, 0, 1, 2)
        controls.addWidget(self.antialias, 5, 0, 1, 2)
        controls.addWidget(self.scaleup, 6, 0, 1, 2)
        controls.addWidget(self.copydata, 8, 0, 1, 2)
        controls.addWidget(self.copyfile, 9, 0, 1, 2)
        controls.addWidget(self.dragdata, 10, 0, 1, 2)
        controls.addWidget(self.dragfile, 11, 0, 1, 2)
        controls.setRowStretch(7, 1)

        layout.addLayout(hlayout)
        layout.addWidget(widgets.Separator())
        layout.addWidget(self.buttons)

        app.translateUI(self)
        self.readSettings()
        self.finished.connect(self.writeSettings)
        self.dpiCombo.editTextChanged.connect(self.updateExport)
        self.colorCheck.toggled.connect(self.updateExport)
        self.colorButton.colorChanged.connect(self.updateExport)
        self.grayscale.toggled.connect(self.updateExport)
        self.scaleup.toggled.connect(self.updateExport)
        self.crop.toggled.connect(self.updateExport)
        self.antialias.toggled.connect(self.updateExport)
        self.buttons.rejected.connect(self.reject)
        self.copydata.clicked.connect(self.copyDataToClipboard)
        self.copyfile.clicked.connect(self.copyFileToClipboard)
        self.dragdata.pressed.connect(self.dragData)
        self.dragfile.pressed.connect(self.dragFile)
        self.dragdata.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dragfile.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.saveButton.clicked.connect(self.saveAs)
        qutil.saveDialogSize(self, "copy_image/dialog/size", QSize(480, 320))

    def translateUI(self):
        self.setCaption()
        self.dpiLabel.setText(_("DPI:"))
        self.colorCheck.setText(_("Background:"))
        self.colorButton.setToolTip(_("Paper Color"))
        self.grayscale.setText(_("Gray"))
        self.grayscale.setToolTip(_("Convert image to grayscale."))
        self.crop.setText(_("Auto-crop"))
        self.antialias.setText(_("Antialias"))
        self.scaleup.setText(_("Scale 2x"))
        self.scaleup.setToolTip(_(
            "Render twice as large and scale back down\n"
            "(recommended for small DPI values)."))
        self.dragdata.setText(_("Drag"))
        self.dragfile.setText(_("Drag File"))
        self.copydata.setText(_("&Copy"))
        self.copyfile.setText(_("Copy &File"))
        self.saveButton.setText(_("&Save As..."))
        self.imageViewer.setWhatsThis(_(
            #xgettext:no-python-format
            "<p>\n"
            "Clicking toggles the display between 100% size and window size. "
            "Drag to copy the image to another application. "
            "Drag with Ctrl (or {command}) to scroll a large image.\n"
            "</p>\n"
            "<p>\n"
            "You can also drag the small picture icon in the bottom right, "
            "which drags the actual file on disk, e.g. to an e-mail message.\n"
            "</p>").format(command="\u2318"))
        self.updateFileTypeUITexts()

    def updateFileTypeUITexts(self):
        """Update the texts in buttons that carry file type information.

        Called from translateUI() and from updateExport().

        """
        self.dragdata.setToolTip(_("Drag the image to embed in a document."))
        self.dragfile.setToolTip(_("Drag the image as a PNG file."))
        self.copydata.setToolTip(_("Copy the image to the clipboard."))
        self.copyfile.setToolTip(_("Copy the image to the clipboard as a PNG file."))

    def readSettings(self):
        s = QSettings()
        s.beginGroup('copy_image')
        # 300 dpi is standard print resolution
        self.dpiCombo.setEditText(s.value("dpi", "300", str))
        color = s.value("papercolor", QColor(), QColor)
        self.colorButton.setColor(color if color.isValid() else Qt.GlobalColor.white)
        self.colorCheck.setChecked(color.isValid())
        self.grayscale.setChecked(s.value("grayscale", False, bool))
        self.crop.setChecked(s.value("autocrop", False, bool))
        self.antialias.setChecked(s.value("antialias", True, bool))
        self.scaleup.setChecked(s.value("scaleup", False, bool))

    def writeSettings(self):
        s = QSettings()
        s.beginGroup('copy_image')
        s.setValue("dpi", self.dpiCombo.currentText())
        color = self.colorButton.color() if self.colorCheck.isChecked() else QColor()
        s.setValue("papercolor", color)
        s.setValue("grayscale", self.grayscale.isChecked())
        s.setValue("autocrop", self.crop.isChecked())
        s.setValue("antialias", self.antialias.isChecked())
        s.setValue("scaleup", self.scaleup.isChecked())

    def setCaption(self):
        if self._filename:
            filename = os.path.basename(self._filename)
        else:
            filename = _("<unknown>")
        title = _("Image from {filename}").format(filename = filename)
        self.setWindowTitle(app.caption(title))

    def setPage(self, page, rect, filename):
        page = page.copy()
        if page.renderer:
            page.renderer = page.renderer.copy()
        self._page = page
        self._rect = rect
        self._filename = filename
        self.setCaption()
        self.updateExport()

    def updateExport(self):
        e = self._exporter = qpageview.export.ImageExporter(self._page, self._rect)
        e.filename = self._filename

        # update the enabled state of buttons
        self.dpiCombo.setEnabled(e.supportsResolution)
        self.colorCheck.setEnabled(e.supportsPaperColor)
        self.colorButton.setEnabled(e.supportsPaperColor and self.colorCheck.isChecked())
        self.grayscale.setEnabled(e.supportsGrayscale)
        self.crop.setEnabled(e.supportsAutocrop)
        self.antialias.setEnabled(e.supportsAntialiasing)
        self.scaleup.setEnabled(e.supportsOversample)

        # update the preferences of the exporter
        if e.supportsResolution:
            e.resolution = float(self.dpiCombo.currentText() or '300')
        if e.supportsPaperColor and self.colorCheck.isChecked():
            e.paperColor = self.colorButton.color()
        if e.supportsGrayscale:
            e.grayscale = self.grayscale.isChecked()
        if e.supportsAntialiasing:
            e.antialiasing = self.antialias.isChecked()
        if e.supportsAutocrop:
            e.autocrop = self.crop.isChecked()
        if e.supportsOversample:
            e.oversample = 2 if self.scaleup.isChecked() else 1

        # disable button actions
        self.dragfile.setEnabled(False)
        self.copyfile.setEnabled(False)
        self.dragdata.setEnabled(False)
        self.copydata.setEnabled(False)
        self.saveButton.setEnabled(False)

        # set filetype info in button tooltips
        self.updateFileTypeUITexts()

        # run the export job in a background thread
        self.runJob(e.document, self.exportDone)
        self.setCursor(Qt.CursorShape.WaitCursor)

    def exportDone(self, document):
        self.unsetCursor()
        self.imageViewer.setDocument(document)
        if self.imageViewer.viewMode() is not qpageview.FitBoth:
            self.imageViewer.zoomNaturalSize()
        # re-enable button actions
        self.dragfile.setEnabled(True)
        self.copyfile.setEnabled(True)
        self.dragdata.setEnabled(True)
        self.copydata.setEnabled(True)
        self.saveButton.setEnabled(True)

    def copyDataToClipboard(self):
        self._exporter.copyData()

    def copyFileToClipboard(self):
        self._exporter.copyFile()

    def dragData(self):
        self._exporter.dragData(self)
        self.dragdata.setDown(False)

    def dragFile(self):
        self._exporter.dragFile(self)
        self.dragfile.setDown(False)

    def saveAs(self):
        typeFilter = _("PNG Image (*.png)")
        filename = self._exporter.suggestedFilename()
        filename = QFileDialog.getSaveFileName(self,
            _("Save Image As"), filename, filter=typeFilter)[0]
        if filename:
            try:
                self._exporter.save(filename)
            except OSError:
                QMessageBox.critical(self, _("Error"), _(
                    "Could not save the image."))


