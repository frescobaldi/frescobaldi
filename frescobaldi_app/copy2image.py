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
Dialog to copy contents from PDF to a raster image.
"""


import collections
import os
import tempfile

from PyQt5.QtCore import QSettings, QSize, Qt
from PyQt5.QtGui import QBitmap, QColor, QDoubleValidator, QRegion
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                             QDialogButtonBox, QFileDialog, QHBoxLayout,
                             QLabel, QMessageBox, QPushButton, QVBoxLayout)

import app
import util
import qutil
import icons
import qpopplerview
import widgets.imageviewer
import widgets.colorbutton
import gadgets.drag

try:
    import popplerqt5
except ImportError:
    popplerqt5 = None


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
        super(Dialog, self).__init__(parent)
        self._filename = None
        self._page = None
        self._rect = None
        self.imageViewer = widgets.imageviewer.ImageViewer()
        self.dpiLabel = QLabel()
        self.dpiCombo = QComboBox(insertPolicy=QComboBox.NoInsert, editable=True)
        self.dpiCombo.lineEdit().setCompleter(None)
        self.dpiCombo.setValidator(QDoubleValidator(10.0, 1200.0, 4, self.dpiCombo))
        self.dpiCombo.addItems([format(i) for i in (72, 100, 200, 300, 600, 1200)])

        self.colorButton = widgets.colorbutton.ColorButton()
        self.colorButton.setColor(QColor(Qt.white))
        self.crop = QCheckBox()
        self.antialias = QCheckBox(checked=True)
        self.scaleup = QCheckBox(checked=False)
        self.dragfile = QPushButton(icons.get("image-x-generic"), None, None)
        self.fileDragger = FileDragger(self.dragfile)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self.copyButton = self.buttons.addButton('', QDialogButtonBox.ApplyRole)
        self.copyButton.setIcon(icons.get('edit-copy'))
        self.saveButton = self.buttons.addButton('', QDialogButtonBox.ApplyRole)
        self.saveButton.setIcon(icons.get('document-save'))

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.imageViewer)

        controls = QHBoxLayout()
        layout.addLayout(controls)
        controls.addWidget(self.dpiLabel)
        controls.addWidget(self.dpiCombo)
        controls.addWidget(self.colorButton)
        controls.addWidget(self.crop)
        controls.addWidget(self.antialias)
        controls.addWidget(self.scaleup)
        controls.addStretch()
        controls.addWidget(self.dragfile)
        layout.addWidget(widgets.Separator())
        layout.addWidget(self.buttons)

        app.translateUI(self)
        self.readSettings()
        self.finished.connect(self.writeSettings)
        self.dpiCombo.editTextChanged.connect(self.drawImage)
        self.colorButton.colorChanged.connect(self.drawImage)
        self.antialias.toggled.connect(self.drawImage)
        self.scaleup.toggled.connect(self.drawImage)
        self.crop.toggled.connect(self.cropImage)
        self.buttons.rejected.connect(self.reject)
        self.copyButton.clicked.connect(self.copyToClipboard)
        self.saveButton.clicked.connect(self.saveAs)
        qutil.saveDialogSize(self, "copy_image/dialog/size", QSize(480, 320))

    def translateUI(self):
        self.setCaption()
        self.dpiLabel.setText(_("DPI:"))
        self.colorButton.setToolTip(_("Paper Color"))
        self.crop.setText(_("Auto-crop"))
        self.antialias.setText(_("Antialias"))
        self.scaleup.setText(_("Scale 2x"))
        self.scaleup.setToolTip(_(
            "Render twice as large and scale back down\n"
            "(recommended for small DPI values)."))
        self.dragfile.setText(_("Drag"))
        self.dragfile.setToolTip(_("Drag the image as a PNG file."))
        self.copyButton.setText(_("&Copy to Clipboard"))
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

    def readSettings(self):
        s = QSettings()
        s.beginGroup('copy_image')
        self.dpiCombo.setEditText(s.value("dpi", "100", str))
        self.colorButton.setColor(s.value("papercolor", QColor(Qt.white), QColor))
        self.crop.setChecked(s.value("autocrop", False, bool))
        self.antialias.setChecked(s.value("antialias", True, bool))
        self.scaleup.setChecked(s.value("scaleup", False, bool))

    def writeSettings(self):
        s = QSettings()
        s.beginGroup('copy_image')
        s.setValue("dpi", self.dpiCombo.currentText())
        s.setValue("papercolor", self.colorButton.color())
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
        self._page = page
        self._rect = rect
        self._filename = filename
        self.fileDragger.basename = os.path.splitext(os.path.basename(self._filename))[0]
        self.setCaption()
        self.drawImage()

    def drawImage(self):
        dpi = float(self.dpiCombo.currentText() or '100')
        dpi = max(dpi, self.dpiCombo.validator().bottom())
        dpi = min(dpi, self.dpiCombo.validator().top())
        options = qpopplerview.RenderOptions()
        options.setPaperColor(self.colorButton.color())
        if self.antialias.isChecked():
            if popplerqt5:
                options.setRenderHint(
                    popplerqt5.Poppler.Document.Antialiasing |
                    popplerqt5.Poppler.Document.TextAntialiasing)
        else:
            options.setRenderHint(0)
        m = 2 if self.scaleup.isChecked() else 1
        i = self._page.image(self._rect, dpi * m, dpi * m , options)
        if m == 2:
            i = i.scaled(i.size() / 2, transformMode=Qt.SmoothTransformation)
        self._image = i
        self.cropImage()

    def cropImage(self):
        image = self._image
        if self.crop.isChecked():
            image = image.copy(autoCropRect(image))
        self.imageViewer.setImage(image)
        self.fileDragger.setImage(image)

    def copyToClipboard(self):
        QApplication.clipboard().setImage(self.imageViewer.image())

    def saveAs(self):
        if self._filename and not self.imageViewer.image().isNull():
            filename = os.path.splitext(self._filename)[0] + ".png"
        else:
            filename = 'image.png'
        filename = QFileDialog.getSaveFileName(self,
            _("Save Image As"), filename)[0]
        if filename:
            if not self.imageViewer.image().save(filename):
                QMessageBox.critical(self, _("Error"), _(
                    "Could not save the image."))
            else:
                self.fileDragger.currentFile = filename


class FileDragger(gadgets.drag.FileDragger):
    """Creates an image file on the fly as soon as a drag is started."""
    image = None
    basename = None
    currentFile = None

    def setImage(self, image):
        self.image = image
        self.currentFile = None

    def filename(self):
        if self.currentFile:
            return self.currentFile
        elif not self.image:
            return
        # save the image as a PNG file
        d = util.tempdir()
        basename = self.basename or 'image'
        basename += '.png'
        filename = os.path.join(d, basename)
        self.image.save(filename)
        self.currentFile = filename
        return filename


def autoCropRect(image):
    """Returns a QRect specifying the contents of the QImage.

    Edges of the image are trimmed if they have the same color.

    """
    # pick the color at most of the corners
    colors = collections.defaultdict(int)
    w, h = image.width(), image.height()
    for x, y in (0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1):
        colors[image.pixel(x, y)] += 1
    most = max(colors, key=colors.get)
    # let Qt do the masking work
    mask = image.createMaskFromColor(most)
    return QRegion(QBitmap.fromImage(mask)).boundingRect()


