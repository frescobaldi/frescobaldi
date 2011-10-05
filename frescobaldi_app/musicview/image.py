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
Dialog to copy contents from PDF to a raster image.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import util
import qpopplerview
import widgets.imageviewer
import widgets.colorbutton

try:
    import popplerqt4
except ImportError:
    popplerqt4 = None



def copy(musicviewpanel):
    """Shows the dialog."""
    view = musicviewpanel.widget().view
    selection = view.surface().selection()
    
    # get the largest page part that is in the selection
    pages = list(view.surface().pageLayout().pagesAt(selection))
    if not pages:
        return
        
    def key(page):
        size = page.rect().intersected(selection).size()
        return size.width() + size.height()
    page = max(pages, key = key)

    
    dlg = Dialog(musicviewpanel)
    dlg.show()
    dlg.setPage(page, selection)
    dlg.finished.connect(dlg.deleteLater)



class Dialog(QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        
        self.imageViewer = widgets.imageviewer.ImageViewer()
        self.dpiLabel = QLabel()
        self.dpiCombo = QComboBox(insertPolicy=QComboBox.NoInsert, editable=True)
        self.dpiCombo.setValidator(QDoubleValidator(10.0, 1200.0, 4, self.dpiCombo))
        self.dpiCombo.addItems([format(i) for i in 72, 100, 200, 300, 600])
        
        self.colorButton = widgets.colorbutton.ColorButton()
        self.colorButton.setColor(QColor(Qt.white))
        self.crop = QCheckBox()
        self.antialias = QCheckBox(checked=True)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close)
        
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
        controls.addStretch()
        layout.addWidget(widgets.Separator())
        layout.addWidget(self.buttons)

        app.translateUI(self)
        self.readSettings()
        self.finished.connect(self.writeSettings)
        self.dpiCombo.editTextChanged.connect(self.drawImage)
        self.colorButton.colorChanged.connect(self.drawImage)
        self.antialias.toggled.connect(self.drawImage)
        self.crop.toggled.connect(self.cropImage)
        self.buttons.rejected.connect(self.reject)
        util.saveDialogSize(self, "copy_image/dialog/size", QSize(480, 320))
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Copy Raster Image")))
        self.dpiLabel.setText(_("DPI:"))
        self.crop.setText(_("Auto-crop"))
        self.antialias.setText(_("Antialias"))
    
    def readSettings(self):
        s = QSettings()
        s.beginGroup('copy_image')
        self.dpiCombo.setEditText(s.value("dpi", "100"))
        self.colorButton.setColor(s.value("papercolor", QColor(Qt.white)))
        self.crop.setChecked(s.value("autocrop", False) in (True, "true"))
        self.antialias.setChecked(s.value("antialias", True) not in (False, "false"))
    
    def writeSettings(self):
        s = QSettings()
        s.beginGroup('copy_image')
        s.setValue("dpi", self.dpiCombo.currentText())
        s.setValue("papercolor", self.colorButton.color())
        s.setValue("autocrop", self.crop.isChecked())
        s.setValue("antialias", self.antialias.isChecked())
    
    def setPage(self, page, rect):
        self._page = page
        self._rect = rect
        self.drawImage()

    def drawImage(self):
        dpi = float(self.dpiCombo.currentText() or '100')
        dpi = max(dpi, self.dpiCombo.validator().bottom())
        dpi = min(dpi, self.dpiCombo.validator().top())
        options = qpopplerview.RenderOptions()
        options.setPaperColor(self.colorButton.color())
        if self.antialias.isChecked():
            if popplerqt4:
                options.setRenderHint(
                    popplerqt4.Poppler.Document.Antialiasing |
                    popplerqt4.Poppler.Document.TextAntialiasing)
        else:
            options.setRenderHint(0)
        self._image = self._page.image(self._rect, dpi, dpi, options)
        self.cropImage()
    
    def cropImage(self):
        if not self.crop.isChecked():
            self.imageViewer.setImage(self._image)
            return
        img = self._image
        left, top, right, bottom = 0, 0, img.width(), img.height()
        pixel = img.pixel(0, 0)
        # left border
        for x in range(right):
            for y in range(bottom):
                if img.pixel(x, y) != pixel:
                    left = x
                    break
        # top
        for y in range(bottom):
            for x in range(left, right):
                if img.pixel(x, y) != pixel:
                    top = y
                    break
        # right
        for x in range(right-1, left, -1):
            for y in range(top, bottom):
                if img.pixel(x, y) != pixel:
                    right = x + 1
                    break
        # bottom
        for y in range(bottom-1, top, -1):
            for x in range(left, right):
                if img.pixel(x, y) != pixel:
                    bottom = y + 1
                    break
        img = img.copy(QRect(QPoint(top, left), QPoint(bottom, right)))
        self.imageViewer.setImage(img)






