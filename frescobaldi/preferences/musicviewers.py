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

        layout.addWidget(Documents(self))
        layout.addWidget(PageScaling(self))
        layout.addWidget(PageLayout(self))
        layout.addWidget(Scrolling(self))
        layout.addWidget(ViewerOptions(self))
        layout.addWidget(Magnifier(self))
        layout.addWidget(Printing(self))
        layout.addStretch(1)


class Documents(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.newerFilesOnly = QCheckBox(toggled=self.changed)
        layout.addWidget(self.newerFilesOnly)

        self.documentProperties = QCheckBox(toggled=self.changed)
        layout.addWidget(self.documentProperties)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Documents"))
        self.newerFilesOnly.setText(_("Only load updated PDF documents"))
        self.newerFilesOnly.setToolTip(_(
            "If checked, Frescobaldi will not open PDF documents that are not\n"
            "up-to-date (i.e. the source file has been modified later)."))
        self.documentProperties.setText(_("Remember View settings per-document"))
        self.documentProperties.setToolTip(_(
            "If checked, every document in the Music View will remember its\n"
            "own layout setting, zoom factor, etc. If unchecked, the View will\n"
            "not change its settings when a different document is displayed."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        self.newerFilesOnly.setChecked(s.value("newer_files_only", True, bool))
        self.documentProperties.setChecked(s.value("document_properties", True, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("newer_files_only", self.newerFilesOnly.isChecked())
        s.setValue("document_properties", self.documentProperties.isChecked())


class PageScaling(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.viewModeGroup = QButtonGroup()

        self.viewFixedScale = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFixedScale)
        self.viewModeGroup.setId(self.viewFixedScale, qpageview.constants.FixedScale)
        layout.addWidget(self.viewFixedScale, 0, 0, 1, 1)

        self.viewFitHeight = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFitHeight)
        self.viewModeGroup.setId(self.viewFitHeight, qpageview.constants.FitHeight)
        layout.addWidget(self.viewFitHeight, 1, 0, 1, 1)

        self.viewFitWidth = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFitWidth)
        self.viewModeGroup.setId(self.viewFitWidth, qpageview.constants.FitWidth)
        layout.addWidget(self.viewFitWidth, 2, 0, 1, 1)

        self.viewFitBoth = QRadioButton(toggled=self.changed)
        self.viewModeGroup.addButton(self.viewFitBoth)
        self.viewModeGroup.setId(self.viewFitBoth, qpageview.constants.FitBoth)
        layout.addWidget(self.viewFitBoth, 3, 0, 1, 1)

        self.initialScaleSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.initialScaleSlider.setSingleStep(50)
        self.initialScaleSlider.setRange(50, 800)
        self.initialScaleSpinBox = QSpinBox()
        self.initialScaleSpinBox.setRange(50, 800)
        self.initialScaleSpinBox.valueChanged.connect(self.initialScaleSlider.setValue)
        self.initialScaleSlider.valueChanged.connect(self.initialScaleSpinBox.setValue)
        layout.addWidget(self.initialScaleSlider, 0, 1, 1, 2)
        layout.addWidget(self.initialScaleSpinBox, 0, 3)

        self.viewFixedScale.toggled.connect(self.toggleFixedScaleControls)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Page scaling"))
        self.viewFixedScale.setText(_("Fixed scale:"))
        self.viewFitHeight.setText(_("Fit height"))
        self.viewFitWidth.setText(_("Fit width"))
        self.viewFitBoth.setText(_("Fit page")) # to match the Music menu
        self.initialScaleSpinBox.setSuffix(_("percent unit sign", "%"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        # These are from qpageview.view.ViewProperties
        v = s.value("viewMode", qpageview.constants.FixedScale, int)
        b = self.viewModeGroup.button(v)
        if b:
            b.setChecked(True)
        self.toggleFixedScaleControls(v == qpageview.constants.FixedScale)
        self.initialScaleSlider.setValue(round(s.value("zoomFactor", 1.0, float) * 100))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        # These are from qpageview.view.ViewProperties
        s.setValue("viewMode", self.viewModeGroup.checkedId())
        s.setValue("zoomFactor", self.initialScaleSlider.value() / 100.0)

    def toggleFixedScaleControls(self, enabled):
        self.initialScaleSlider.setEnabled(enabled)
        self.initialScaleSpinBox.setEnabled(enabled)


class PageLayout(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.pageLayoutGroup = QButtonGroup()

        self.pageLayoutSingle = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutSingle)
        layout.addWidget(self.pageLayoutSingle)

        self.pageLayoutDoubleRight = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutDoubleRight)
        layout.addWidget(self.pageLayoutDoubleRight)

        self.pageLayoutDoubleLeft = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutDoubleLeft)
        layout.addWidget(self.pageLayoutDoubleLeft)

        self.pageLayoutRaster = QRadioButton(toggled=self.changed)
        self.pageLayoutGroup.addButton(self.pageLayoutRaster)
        layout.addWidget(self.pageLayoutRaster)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Page layout"))
        self.pageLayoutSingle.setText(_("Single"))
        self.pageLayoutDoubleRight.setText(_("Two pages (first page right)"))
        self.pageLayoutDoubleLeft.setText(_("Two pages (first page left)"))
        self.pageLayoutRaster.setText(_("Grid layout"))
        self.pageLayoutRaster.setToolTip(_("The layout of pages (horizontal or vertical) adjusts dynamically based on the zoom level and the available space in the Music View. Continuous scrolling option must be checked."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        # These are from qpageview.view.ViewProperties
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
        # These are from qpageview.view.ViewProperties
        if self.pageLayoutSingle.isChecked():
            s.setValue("pageLayoutMode", "single")
        elif self.pageLayoutDoubleRight.isChecked():
            s.setValue("pageLayoutMode", "double_right")
        elif self.pageLayoutDoubleLeft.isChecked():
            s.setValue("pageLayoutMode", "double_left")
        elif self.pageLayoutRaster.isChecked():
            s.setValue("pageLayoutMode", "raster")


class Scrolling(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.orientationLabel = QLabel()
        layout.addWidget(self.orientationLabel, 0, 0)
        self.orientationGroup = QButtonGroup()
        self.orientationHorizontal = QRadioButton(toggled=self.changed)
        self.orientationGroup.addButton(self.orientationHorizontal)
        self.orientationGroup.setId(self.orientationHorizontal, qpageview.constants.Horizontal)
        layout.addWidget(self.orientationHorizontal, 0, 1)
        self.orientationVertical = QRadioButton(toggled=self.changed)
        self.orientationGroup.addButton(self.orientationVertical)
        self.orientationGroup.setId(self.orientationVertical, qpageview.constants.Vertical)
        layout.addWidget(self.orientationVertical, 0, 2)

        self.continuousMode = QCheckBox(toggled=self.changed)
        layout.addWidget(self.continuousMode, 1, 0, 1, 4)

        self.enableKineticScrolling = QCheckBox(toggled=self.changed)
        layout.addWidget(self.enableKineticScrolling, 2, 0, 1, 4)

        self.enableStrictPaging = QCheckBox(toggled=self.changed)
        layout.addWidget(self.enableStrictPaging, 3, 0, 1, 4)

        app.translateUI(self)

    def translateUI(self):
        # L10N: "Kinetic Scrolling" is a checkbox label, as in "Enable Kinetic Scrolling"
        self.setTitle(_("Scrolling"))
        self.orientationLabel.setText(_("Orientation:"))
        self.orientationHorizontal.setText(_("Horizontal"))
        self.orientationVertical.setText(_("Vertical"))
        self.continuousMode.setText(_("Continuous scrolling"))
        self.enableKineticScrolling.setText(_("Kinetic scrolling"))
        self.enableStrictPaging.setText(
            _("Use Page Up and Page Down keys to change pages"))
        self.enableStrictPaging.setToolTip(_(
            "If checked, PageUp and PageDown always page to the previous or next page instead of scrolling."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        kineticScrollingActive = s.value("kinetic_scrolling", True, bool)
        self.enableKineticScrolling.setChecked(kineticScrollingActive)
        strictPaging = s.value("strict_paging", False, bool)
        self.enableStrictPaging.setChecked(strictPaging)
        # These are from qpageview.view.ViewProperties
        v = s.value("orientation", qpageview.constants.Vertical, int)
        b = self.orientationGroup.button(v)
        if b:
            b.setChecked(True)
        self.continuousMode.setChecked(s.value("continuousMode", True, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("kinetic_scrolling", self.enableKineticScrolling.isChecked())
        s.setValue("strict_paging", self.enableStrictPaging.isChecked())
        # These are from qpageview.view.ViewProperties
        s.setValue("orientation", self.orientationGroup.checkedId())
        s.setValue("continuousMode", self.continuousMode.isChecked())


class ViewerOptions(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.showScrollbars = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showScrollbars)

        self.showShadow = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showShadow)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Viewer options"))
        self.showScrollbars.setText(_("Show scrollbars"))
        self.showShadow.setText(_("Show shadow under pages"))
        self.showShadow.setToolTip(_(
            "If checked, Frescobaldi draws a shadow around the pages."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        showScrollbars = s.value("show_scrollbars", True, bool)
        self.showScrollbars.setChecked(showScrollbars)
        shadow = s.value("shadow", True, bool)
        self.showShadow.setChecked(shadow)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("show_scrollbars", self.showScrollbars.isChecked())
        s.setValue("shadow", self.showShadow.isChecked())


class Magnifier(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.magnifierSizeLabel = QLabel()
        self.magnifierSizeSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.magnifierSizeSlider.setSingleStep(50)
        self.magnifierSizeSlider.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox = QSpinBox()
        self.magnifierSizeSpinBox.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox.valueChanged.connect(self.magnifierSizeSlider.setValue)
        self.magnifierSizeSlider.valueChanged.connect(self.magnifierSizeSpinBox.setValue)
        layout.addWidget(self.magnifierSizeLabel, 0, 0)
        layout.addWidget(self.magnifierSizeSlider, 0, 1, 1, 2)
        layout.addWidget(self.magnifierSizeSpinBox, 0, 3)

        self.magnifierScaleLabel = QLabel()
        self.magnifierScaleSlider = QSlider(Qt.Orientation.Horizontal, valueChanged=self.changed)
        self.magnifierScaleSlider.setSingleStep(50)
        self.magnifierScaleSlider.setRange(50, 800)
        self.magnifierScaleSpinBox = QSpinBox()
        self.magnifierScaleSpinBox.setRange(50, 800)
        self.magnifierScaleSpinBox.valueChanged.connect(self.magnifierScaleSlider.setValue)
        self.magnifierScaleSlider.valueChanged.connect(self.magnifierScaleSpinBox.setValue)
        layout.addWidget(self.magnifierScaleLabel, 1, 0)
        layout.addWidget(self.magnifierScaleSlider, 1, 1, 1, 2)
        layout.addWidget(self.magnifierScaleSpinBox, 1, 3)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Magnifier"))
        self.magnifierSizeLabel.setText(_("Size:"))
        self.magnifierSizeLabel.setToolTip(_(
            "Size of the magnifier glass (Ctrl+Click in the Music View)."))
        # L10N: as in "400 pixels", appended after number in spinbox, note the leading space
        self.magnifierSizeSpinBox.setSuffix(_(" pixels"))
        self.magnifierScaleLabel.setText(_("Scale:"))
        self.magnifierScaleLabel.setToolTip(_(
            "Magnification of the magnifier."))
        self.magnifierScaleSpinBox.setSuffix(_("percent unit sign", "%"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        self.magnifierSizeSlider.setValue(s.value("magnifier/size", 350, int))
        self.magnifierScaleSlider.setValue(round(s.value("magnifier/scalef", 3.0, float) * 100))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
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
        self.setTitle(_("Printing"))
        self.resolutionLabel.setText(_("Resolution:"))
        self.resolution.setToolTip(_(
            "Set the resolution to be sent to the printer."))

    def loadSettings(self):
        s = QSettings()
        with qutil.signalsBlocked(self.resolution):
            self.resolution.setEditText(format(s.value("printing/dpi", 300, int)))

    def saveSettings(self):
        s = QSettings()
        s.setValue("printing/dpi", int(self.resolution.currentText()))
