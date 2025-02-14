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
Music View preferences.
"""


import platform
import re

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFontComboBox,
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget)

import app
import qutil
import preferences
import pagedview
import qpageview.cupsprinter


class MusicViewers(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super().__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(MusicView(self))
        layout.addWidget(Printing(self))
        layout.addStretch(1)


class MusicView(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.enableKineticScrolling = QCheckBox(toggled=self.changed)
        layout.addWidget(self.enableKineticScrolling, 0, 0)
        self.showScrollbars = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showScrollbars, 0, 1)
        self.enableStrictPaging = QCheckBox(toggled=self.changed)
        layout.addWidget(self.enableStrictPaging, 0, 2)
        self.showShadow = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showShadow, 0, 3)

        self.magnifierSizeLabel = QLabel()
        self.magnifierSizeSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.magnifierSizeSlider.setSingleStep(50)
        self.magnifierSizeSlider.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox = QSpinBox()
        self.magnifierSizeSpinBox.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox.valueChanged.connect(self.magnifierSizeSlider.setValue)
        self.magnifierSizeSlider.valueChanged.connect(self.magnifierSizeSpinBox.setValue)
        layout.addWidget(self.magnifierSizeLabel, 1, 0)
        layout.addWidget(self.magnifierSizeSlider, 1, 1, 1, 2)
        layout.addWidget(self.magnifierSizeSpinBox, 1, 3)

        self.magnifierScaleLabel = QLabel()
        self.magnifierScaleSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.magnifierScaleSlider.setSingleStep(50)
        self.magnifierScaleSlider.setRange(50, 800)
        self.magnifierScaleSpinBox = QSpinBox()
        self.magnifierScaleSpinBox.setRange(50, 800)
        self.magnifierScaleSpinBox.valueChanged.connect(self.magnifierScaleSlider.setValue)
        self.magnifierScaleSlider.valueChanged.connect(self.magnifierScaleSpinBox.setValue)
        layout.addWidget(self.magnifierScaleLabel, 2, 0)
        layout.addWidget(self.magnifierScaleSlider, 2, 1, 1, 2)
        layout.addWidget(self.magnifierScaleSpinBox, 2, 3)

        app.translateUI(self)

    def translateUI(self):
        # L10N: "Kinetic Scrolling" is a checkbox label, as in "Enable Kinetic Scrolling"
        self.enableKineticScrolling.setText(_("Kinetic Scrolling"))
        self.showScrollbars.setText(_("Show Scrollbars"))
        self.enableStrictPaging.setText(_("Strict Paging"))
        self.enableStrictPaging.setToolTip(_(
            "If checked, PageUp and PageDown always page to the previous or next page instead of scrolling."))
        self.showShadow.setText(_("Shadow"))
        self.showShadow.setToolTip(_(
            "If checked, Frescobaldi draws a shadow around the pages."))
        self.setTitle(_("Display of Music"))
        self.magnifierSizeLabel.setText(_("Magnifier Size:"))
        self.magnifierSizeLabel.setToolTip(_(
            "Size of the magnifier glass (Ctrl+Click in the Music View)."))
        # L10N: as in "400 pixels", appended after number in spinbox, note the leading space
        self.magnifierSizeSpinBox.setSuffix(_(" pixels"))
        self.magnifierScaleLabel.setText(_("Magnifier Scale:"))
        self.magnifierScaleLabel.setToolTip(_(
            "Magnification of the magnifier."))
        self.magnifierScaleSpinBox.setSuffix(_("percent unit sign", "%"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        kineticScrollingActive = s.value("kinetic_scrolling", True, bool)
        self.enableKineticScrolling.setChecked(kineticScrollingActive)
        showScrollbars = s.value("show_scrollbars", True, bool)
        self.showScrollbars.setChecked(showScrollbars)
        strictPaging = s.value("strict_paging", False, bool)
        self.enableStrictPaging.setChecked(strictPaging)
        shadow = s.value("shadow", True, bool)
        self.showShadow.setChecked(shadow)
        self.magnifierSizeSlider.setValue(s.value("magnifier/size", 350, int))
        self.magnifierScaleSlider.setValue(round(s.value("magnifier/scalef", 3.0, float) * 100))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("kinetic_scrolling", self.enableKineticScrolling.isChecked())
        s.setValue("show_scrollbars", self.showScrollbars.isChecked())
        s.setValue("strict_paging", self.enableStrictPaging.isChecked())
        s.setValue("shadow", self.showShadow.isChecked())
        s.setValue("magnifier/size", self.magnifierSizeSlider.value())
        s.setValue("magnifier/scalef", self.magnifierScaleSlider.value() / 100.0)


class Printing(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)
        self.resolutionLabel = QLabel()
        self.resolution = QComboBox(editable=True, editTextChanged=page.changed)
        self.resolution.addItems("300 600 1200".split())
        self.resolution.lineEdit().setInputMask("9000")

        layout.addWidget(self.resolutionLabel, 0, 0)
        layout.addWidget(self.resolution, 0, 1)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Printing of Music"))
        self.resolutionLabel.setText(_("Resolution:"))
        self.resolution.setToolTip(_(
            "Set the resolution if Frescobaldi prints using raster images."))

    def loadSettings(self):
        s = QSettings()
        with qutil.signalsBlocked(self.resolution):
            self.resolution.setEditText(format(s.value("printing/dpi", 300, int)))

    def saveSettings(self):
        s = QSettings()
        s.setValue("printing/dpi", int(self.resolution.currentText()))
