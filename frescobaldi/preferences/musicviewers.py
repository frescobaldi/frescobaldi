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
    QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox,
    QFontComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QSlider, QSpinBox, QVBoxLayout, QWidget)

import app
import qutil
import preferences
import pagedview
import qpageview.constants


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

        self.initialScaleLabel = QLabel()
        layout.addWidget(self.initialScaleLabel, 1, 0)
        self.viewModeGroup = QButtonGroup()
        self.viewModeLayout = QHBoxLayout()
        layout.addLayout(self.viewModeLayout, 1, 1, 1, 3)
        self.viewFixedScale = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFixedScale)
        self.viewModeGroup.setId(self.viewFixedScale, qpageview.constants.FixedScale)
        self.viewModeLayout.addWidget(self.viewFixedScale)
        self.viewFitHeight = QRadioButton(toggled=self.changed)
        self.viewModeLayout.addWidget(self.viewFitHeight)
        self.viewModeGroup.addButton(self.viewFitHeight)
        self.viewModeGroup.setId(self.viewFitHeight, qpageview.constants.FitHeight)
        self.viewFitWidth = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFitWidth)
        self.viewModeGroup.setId(self.viewFitWidth, qpageview.constants.FitWidth)
        self.viewModeLayout.addWidget(self.viewFitWidth)
        self.viewFitBoth = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFitBoth)
        self.viewModeGroup.setId(self.viewFitBoth, qpageview.constants.FitBoth)
        self.viewModeLayout.addWidget(self.viewFitBoth)

        self.initialScaleSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.initialScaleSlider.setSingleStep(50)
        self.initialScaleSlider.setRange(50, 800)
        self.initialScaleSpinBox = QSpinBox()
        self.initialScaleSpinBox.setRange(50, 800)
        self.initialScaleSpinBox.valueChanged.connect(self.initialScaleSlider.setValue)
        self.initialScaleSlider.valueChanged.connect(self.initialScaleSpinBox.setValue)
        layout.addWidget(self.initialScaleSlider, 2, 1, 1, 2)
        layout.addWidget(self.initialScaleSpinBox, 2, 3)

        self.viewFixedScale.toggled.connect(self.initialScaleSlider.setEnabled)
        self.viewFixedScale.toggled.connect(self.initialScaleSpinBox.setEnabled)

        self.magnifierSizeLabel = QLabel()
        self.magnifierSizeSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.magnifierSizeSlider.setSingleStep(50)
        self.magnifierSizeSlider.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox = QSpinBox()
        self.magnifierSizeSpinBox.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox.valueChanged.connect(self.magnifierSizeSlider.setValue)
        self.magnifierSizeSlider.valueChanged.connect(self.magnifierSizeSpinBox.setValue)
        layout.addWidget(self.magnifierSizeLabel, 3, 0)
        layout.addWidget(self.magnifierSizeSlider, 3, 1, 1, 2)
        layout.addWidget(self.magnifierSizeSpinBox, 3, 3)

        self.magnifierScaleLabel = QLabel()
        self.magnifierScaleSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.magnifierScaleSlider.setSingleStep(50)
        self.magnifierScaleSlider.setRange(50, 800)
        self.magnifierScaleSpinBox = QSpinBox()
        self.magnifierScaleSpinBox.setRange(50, 800)
        self.magnifierScaleSpinBox.valueChanged.connect(self.magnifierScaleSlider.setValue)
        self.magnifierScaleSlider.valueChanged.connect(self.magnifierScaleSpinBox.setValue)
        layout.addWidget(self.magnifierScaleLabel, 4, 0)
        layout.addWidget(self.magnifierScaleSlider, 4, 1, 1, 2)
        layout.addWidget(self.magnifierScaleSpinBox, 4, 3)

        self.pageLayoutLabel = QLabel()
        layout.addWidget(self.pageLayoutLabel, 5, 0)
        self.pageLayoutGroup = QButtonGroup()
        self.pageLayoutSingle = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutSingle)
        layout.addWidget(self.pageLayoutSingle, 5, 1, 1, 3)
        self.pageLayoutDoubleRight = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutDoubleRight)
        layout.addWidget(self.pageLayoutDoubleRight, 6, 1, 1, 3)
        self.pageLayoutDoubleLeft = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutDoubleLeft)
        layout.addWidget(self.pageLayoutDoubleLeft, 7, 1, 1, 3)
        self.pageLayoutRaster = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutRaster)
        layout.addWidget(self.pageLayoutRaster, 8, 1, 1, 3)

        self.orientationLabel = QLabel()
        layout.addWidget(self.orientationLabel, 9, 0)
        self.orientationGroup = QButtonGroup()
        self.orientationHorizontal = QRadioButton(toggled=self.changed)
        self.orientationGroup.addButton(self.orientationHorizontal)
        self.orientationGroup.setId(self.orientationHorizontal, qpageview.constants.Horizontal)
        layout.addWidget(self.orientationHorizontal, 9, 1)
        self.orientationVertical = QRadioButton(toggled=self.changed)
        self.orientationGroup.addButton(self.orientationVertical)
        self.orientationGroup.setId(self.orientationVertical, qpageview.constants.Vertical)
        layout.addWidget(self.orientationVertical, 9, 2)
        self.continuousMode = QCheckBox(toggled=self.changed)
        layout.addWidget(self.continuousMode, 9, 3)

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
        self.initialScaleLabel.setText(_("Initial Scale:"))
        self.initialScaleLabel.setToolTip(_(
            "Initial scale when displaying a document."))
        self.viewFixedScale.setText(_("Fixed Scale"))
        self.viewFitHeight.setText(_("Fit Height"))
        self.viewFitWidth.setText(_("Fit Width"))
        self.viewFitBoth.setText(_("Fit Page")) # to match the Music menu
        self.initialScaleSpinBox.setSuffix(_("percent unit sign", "%"))
        self.magnifierSizeLabel.setText(_("Magnifier Size:"))
        self.magnifierSizeLabel.setToolTip(_(
            "Size of the magnifier glass (Ctrl+Click in the Music View)."))
        # L10N: as in "400 pixels", appended after number in spinbox, note the leading space
        self.magnifierSizeSpinBox.setSuffix(_(" pixels"))
        self.magnifierScaleLabel.setText(_("Magnifier Scale:"))
        self.magnifierScaleLabel.setToolTip(_(
            "Magnification of the magnifier."))
        self.magnifierScaleSpinBox.setSuffix(_("percent unit sign", "%"))
        self.orientationLabel.setText(_("Scrolling:"))
        self.orientationHorizontal.setText(_("Horizontal"))
        self.orientationVertical.setText(_("Vertical"))
        self.continuousMode.setText(_("Continuous"))
        self.pageLayoutLabel.setText(_("Page Layout:"))
        self.pageLayoutSingle.setText(_("Single"))
        self.pageLayoutDoubleRight.setText(_("Two Pages (first page right)"))
        self.pageLayoutDoubleLeft.setText(_("Two Pages (first page left)"))
        self.pageLayoutRaster.setText(_("Raster"))

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
        # These are from qpageview.view.ViewProperties
        v = s.value("viewMode", -1, int)
        b = self.viewModeGroup.button(v)
        if b:
            b.setChecked(True)
        if v != qpageview.constants.FixedScale:
            self.initialScaleSlider.setEnabled(False)
            self.initialScaleSpinBox.setEnabled(False)
        self.initialScaleSlider.setValue(round(s.value("zoomFactor", 1.0, float) * 100))
        v = s.value("orientation", -1, int)
        b = self.orientationGroup.button(v)
        if b:
            b.setChecked(True)
        self.continuousMode.setChecked(s.value("continuousMode", True, bool))
        v = s.value("pageLayoutMode", "single")
        if v == "single":
            self.pageLayoutSingle.setChecked(True)
        elif v == "double_right":
            self.pageLayoutDoubleRight.setChecked(True)
        elif v == "double_left":
            self.pageLayoutDoubleLeft.setChecked(True)
        elif v == "raster":
            self.pageLayoutRaster.setChecked(True)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("kinetic_scrolling", self.enableKineticScrolling.isChecked())
        s.setValue("show_scrollbars", self.showScrollbars.isChecked())
        s.setValue("strict_paging", self.enableStrictPaging.isChecked())
        s.setValue("shadow", self.showShadow.isChecked())
        s.setValue("magnifier/size", self.magnifierSizeSlider.value())
        s.setValue("magnifier/scalef", self.magnifierScaleSlider.value() / 100.0)
        # These are from qpageview.view.ViewProperties
        s.setValue("viewMode", self.viewModeGroup.checkedId())
        s.setValue("zoomFactor", self.initialScaleSlider.value() / 100.0)
        s.setValue("orientation", self.orientationGroup.checkedId())
        s.setValue("continuousMode", self.continuousMode.isChecked())
        if self.pageLayoutSingle.isChecked():
            s.setValue("pageLayoutMode", "single")
        elif self.pageLayoutDoubleRight.isChecked():
            s.setValue("pageLayoutMode", "double_right")
        elif self.pageLayoutDoubleLeft.isChecked():
            s.setValue("pageLayoutMode", "double_left")
        elif self.pageLayoutRaster.isChecked():
            s.setValue("pageLayoutMode", "raster")


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
