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

        self.arthurBackend = QCheckBox(toggled=self.changed)
        layout.addWidget(self.arthurBackend, 1, 0, 1, 4)

        self.magnifierSizeLabel = QLabel()
        self.magnifierSizeSlider = QSlider(Qt.Horizontal, valueChanged=self.changed)
        self.magnifierSizeSlider.setSingleStep(50)
        self.magnifierSizeSlider.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox = QSpinBox()
        self.magnifierSizeSpinBox.setRange(pagedview.Magnifier.MIN_SIZE, pagedview.Magnifier.MAX_SIZE)
        self.magnifierSizeSpinBox.valueChanged.connect(self.magnifierSizeSlider.setValue)
        self.magnifierSizeSlider.valueChanged.connect(self.magnifierSizeSpinBox.setValue)
        layout.addWidget(self.magnifierSizeLabel, 2, 0)
        layout.addWidget(self.magnifierSizeSlider, 2, 1, 1, 2)
        layout.addWidget(self.magnifierSizeSpinBox, 2, 3)

        self.magnifierScaleLabel = QLabel()
        self.magnifierScaleSlider = QSlider(Qt.Horizontal, valueChanged=self.changed)
        self.magnifierScaleSlider.setSingleStep(50)
        self.magnifierScaleSlider.setRange(50, 800)
        self.magnifierScaleSpinBox = QSpinBox()
        self.magnifierScaleSpinBox.setRange(50, 800)
        self.magnifierScaleSpinBox.valueChanged.connect(self.magnifierScaleSlider.setValue)
        self.magnifierScaleSlider.valueChanged.connect(self.magnifierScaleSpinBox.setValue)
        layout.addWidget(self.magnifierScaleLabel, 3, 0)
        layout.addWidget(self.magnifierScaleSlider, 3, 1, 1, 2)
        layout.addWidget(self.magnifierScaleSpinBox, 3, 3)

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
        self.arthurBackend.setText(_("Use vector based backend (Arthur) for rendering PDF documents on screen (experimental!)"))
        self.arthurBackend.setToolTip(_(
            "If checked, Frescobaldi will use the Arthur backend of the Poppler\n"
            "library for PDF rendering on screen. The Arthur backend is faster\n"
            "than the default Splash backend, but more experimental."))
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
        useArthur = s.value("arthurbackend", False, bool)
        self.arthurBackend.setChecked(useArthur)
        self.magnifierSizeSlider.setValue(s.value("magnifier/size", 350, int))
        self.magnifierScaleSlider.setValue(round(s.value("magnifier/scalef", 3.0, float) * 100))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("kinetic_scrolling", self.enableKineticScrolling.isChecked())
        s.setValue("show_scrollbars", self.showScrollbars.isChecked())
        s.setValue("strict_paging", self.enableStrictPaging.isChecked())
        s.setValue("shadow", self.showShadow.isChecked())
        s.setValue("arthurbackend", self.arthurBackend.isChecked())
        s.setValue("magnifier/size", self.magnifierSizeSlider.value())
        s.setValue("magnifier/scalef", self.magnifierScaleSlider.value() / 100.0)


class Printing(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)
        self.printArthurBackend = QCheckBox(toggled=self.changed)
        self.useCups = QCheckBox(toggled=self.changed)
        self.resolutionLabel = QLabel()
        self.resolution = QComboBox(editable=True, editTextChanged=page.changed)
        self.resolution.addItems("300 600 1200".split())
        self.resolution.lineEdit().setInputMask("9000")

        layout.addWidget(self.printArthurBackend, 0, 0, 1, 2)
        layout.addWidget(self.useCups, 1, 0, 1, 2)
        layout.addWidget(self.resolutionLabel, 2, 0)
        layout.addWidget(self.resolution, 2, 1)

        app.translateUI(self)

        if not qpageview.cupsprinter.handle():
            self.useCups.setEnabled(False)

    def translateUI(self):
        self.setTitle(_("Printing of Music"))
        self.printArthurBackend.setText(_("Use vector based backend (Arthur) for printing PDF documents"))
        self.printArthurBackend.setToolTip(_(
            "If checked, Frescobaldi will use the Arthur backend of the Poppler\n"
            "library for printing PDF documents. A big advantage of the Arthur backend\n"
            "is that it is vector-based, in contrast to the default Splash backend,\n"
            "which is raster-based. But Arthur is more experimental."))
        self.useCups.setText(_("Print PDF documents directly to CUPS if available."))
        self.useCups.setToolTip(_(
            "If checked, Frescobaldi tries to print a PDF document directly using\n"
            "the CUPS server, if available."))
        self.resolutionLabel.setText(_("Resolution:"))
        self.resolution.setToolTip(_(
            "Set the resolution if Frescobaldi prints using raster images."))

    def loadSettings(self):
        s = QSettings()
        useArthurPrint = s.value("printing/arthurbackend_print", True, bool)
        self.printArthurBackend.setChecked(useArthurPrint)
        # see comment in pagedview and warning messages in musicview/__init__
        # and viewers/__init__ for the rationale for the default value
        self.useCups.setChecked(s.value("printing/directcups",
                False if platform.system() == "Darwin" else True,
                bool))
        with qutil.signalsBlocked(self.resolution):
            self.resolution.setEditText(format(s.value("printing/dpi", 300, int)))

    def saveSettings(self):
        s = QSettings()
        s.setValue("printing/arthurbackend_print", self.printArthurBackend.isChecked())
        s.setValue("printing/directcups", self.useCups.isChecked())
        s.setValue("printing/dpi", int(self.resolution.currentText()))
