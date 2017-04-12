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
Per-tool preferences.
"""


import re

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFontComboBox,
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget)

import app
import userguide
import qutil
import preferences
import popplerview
import widgets.dialog
import widgets.listedit
import documentstructure


class Tools(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(Tools, self).__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(LogTool(self))
        layout.addWidget(MusicView(self))
        layout.addWidget(CharMap(self))
        layout.addWidget(DocumentList(self))
        layout.addWidget(Outline(self))
        layout.addStretch(1)


class LogTool(preferences.Group):
    def __init__(self, page):
        super(LogTool, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fontLabel = QLabel()
        self.fontChooser = QFontComboBox(currentFontChanged=self.changed)
        self.fontSize = QDoubleSpinBox(valueChanged=self.changed)
        self.fontSize.setRange(6.0, 32.0)
        self.fontSize.setSingleStep(0.5)
        self.fontSize.setDecimals(1)

        box = QHBoxLayout()
        box.addWidget(self.fontLabel)
        box.addWidget(self.fontChooser, 1)
        box.addWidget(self.fontSize)
        layout.addLayout(box)

        self.showlog = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showlog)

        self.rawview = QCheckBox(toggled=self.changed)
        layout.addWidget(self.rawview)

        self.hideauto = QCheckBox(toggled=self.changed)
        layout.addWidget(self.hideauto)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("LilyPond Log"))
        self.fontLabel.setText(_("Font:"))
        self.showlog.setText(_("Show log when a job is started"))
        self.rawview.setText(_("Display plain log output"))
        self.rawview.setToolTip(_(
            "If checked, Frescobaldi will not shorten filenames in the log output."""))
        self.hideauto.setText(_("Hide automatic engraving jobs"))
        self.hideauto.setToolTip(_(
            "If checked, Frescobaldi will not show the log for automatically\n"
            "started engraving jobs (LilyPond->Auto-engrave)."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("log")
        font = QFont(s.value("fontfamily", "monospace", str))
        font.setPointSizeF(s.value("fontsize", 9.0, float))
        with qutil.signalsBlocked(self.fontChooser, self.fontSize):
            self.fontChooser.setCurrentFont(font)
            self.fontSize.setValue(font.pointSizeF())
        self.showlog.setChecked(s.value("show_on_start", True, bool))
        self.rawview.setChecked(s.value("rawview", True, bool))
        self.hideauto.setChecked(s.value("hide_auto_engrave", False, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("log")
        s.setValue("fontfamily", self.fontChooser.currentFont().family())
        s.setValue("fontsize", self.fontSize.value())
        s.setValue("show_on_start", self.showlog.isChecked())
        s.setValue("rawview", self.rawview.isChecked())
        s.setValue("hide_auto_engrave", self.hideauto.isChecked())


class MusicView(preferences.Group):
    def __init__(self, page):
        super(MusicView, self).__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.newerFilesOnly = QCheckBox(toggled=self.changed)
        layout.addWidget(self.newerFilesOnly, 0, 0, 1, 3)

        self.magnifierSizeLabel = QLabel()
        self.magnifierSizeSlider = QSlider(Qt.Horizontal, valueChanged=self.changed)
        self.magnifierSizeSlider.setSingleStep(50)
        self.magnifierSizeSlider.setRange(*popplerview.MagnifierSettings.sizeRange)
        self.magnifierSizeSpinBox = QSpinBox()
        self.magnifierSizeSpinBox.setRange(*popplerview.MagnifierSettings.sizeRange)
        self.magnifierSizeSpinBox.valueChanged.connect(self.magnifierSizeSlider.setValue)
        self.magnifierSizeSlider.valueChanged.connect(self.magnifierSizeSpinBox.setValue)
        layout.addWidget(self.magnifierSizeLabel, 1, 0)
        layout.addWidget(self.magnifierSizeSlider, 1, 1)
        layout.addWidget(self.magnifierSizeSpinBox, 1, 2)

        self.magnifierScaleLabel = QLabel()
        self.magnifierScaleSlider = QSlider(Qt.Horizontal, valueChanged=self.changed)
        self.magnifierScaleSlider.setSingleStep(50)
        self.magnifierScaleSlider.setRange(*popplerview.MagnifierSettings.scaleRange)
        self.magnifierScaleSpinBox = QSpinBox()
        self.magnifierScaleSpinBox.setRange(*popplerview.MagnifierSettings.scaleRange)
        self.magnifierScaleSpinBox.valueChanged.connect(self.magnifierScaleSlider.setValue)
        self.magnifierScaleSlider.valueChanged.connect(self.magnifierScaleSpinBox.setValue)
        layout.addWidget(self.magnifierScaleLabel, 2, 0)
        layout.addWidget(self.magnifierScaleSlider, 2, 1)
        layout.addWidget(self.magnifierScaleSpinBox, 2, 2)

        self.enableKineticScrolling = QCheckBox(toggled=self.changed)
        layout.addWidget(self.enableKineticScrolling)
        self.showScrollbars = QCheckBox(toggled=self.changed)
        layout.addWidget(self.showScrollbars)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Music View"))
        self.newerFilesOnly.setText(_("Only load updated PDF documents"))
        self.newerFilesOnly.setToolTip(_(
            "If checked, Frescobaldi will not open PDF documents that are not\n"
            "up-to-date (i.e. the source file has been modified later)."))
        self.magnifierSizeLabel.setText(_("Magnifier Size:"))
        self.magnifierSizeLabel.setToolTip(_(
            "Size of the magnifier glass (Ctrl+Click in the Music View)."))
        # L10N: as in "400 pixels", appended after number in spinbox, note the leading space
        self.magnifierSizeSpinBox.setSuffix(_(" pixels"))
        self.magnifierScaleLabel.setText(_("Magnifier Scale:"))
        self.magnifierScaleLabel.setToolTip(_(
            "Magnification of the magnifier."))
        self.magnifierScaleSpinBox.setSuffix(_("percent unit sign", "%"))
        # L10N: "Kinetic Scrolling" is a checkbox label, as in "Enable Kinetic Scrolling"
        self.enableKineticScrolling.setText(_("Kinetic Scrolling"))
        self.showScrollbars.setText(_("Show Scrollbars"))

    def loadSettings(self):
        s = popplerview.MagnifierSettings.load()
        self.magnifierSizeSlider.setValue(s.size)
        self.magnifierScaleSlider.setValue(s.scale)

        s = QSettings()
        s.beginGroup("musicview")
        newerFilesOnly = s.value("newer_files_only", True, bool)
        self.newerFilesOnly.setChecked(newerFilesOnly)
        kineticScrollingActive = s.value("kinetic_scrolling", True, bool)
        self.enableKineticScrolling.setChecked(kineticScrollingActive)
        showScrollbars = s.value("show_scrollbars", True, bool)
        self.showScrollbars.setChecked(showScrollbars)

    def saveSettings(self):
        s = popplerview.MagnifierSettings()
        s.size = self.magnifierSizeSlider.value()
        s.scale = self.magnifierScaleSlider.value()
        s.save()

        s = QSettings()
        s.beginGroup("musicview")
        s.setValue("newer_files_only", self.newerFilesOnly.isChecked())
        s.setValue("kinetic_scrolling", self.enableKineticScrolling.isChecked())
        s.setValue("show_scrollbars", self.showScrollbars.isChecked())


class CharMap(preferences.Group):
    def __init__(self, page):
        super(CharMap, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fontLabel = QLabel()
        self.fontChooser = QFontComboBox(currentFontChanged=self.changed)
        self.fontSize = QDoubleSpinBox(valueChanged=self.changed)
        self.fontSize.setRange(6.0, 32.0)
        self.fontSize.setSingleStep(0.5)
        self.fontSize.setDecimals(1)

        box = QHBoxLayout()
        box.addWidget(self.fontLabel)
        box.addWidget(self.fontChooser, 1)
        box.addWidget(self.fontSize)
        layout.addLayout(box)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Special Characters"))
        self.fontLabel.setText(_("Font:"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("charmaptool")
        font = self.font()
        family = s.value("fontfamily", "", str)
        if family:
            font.setFamily(family)
        font.setPointSizeF(s.value("fontsize", font.pointSizeF(), float))
        with qutil.signalsBlocked(self.fontChooser, self.fontSize):
            self.fontChooser.setCurrentFont(font)
            self.fontSize.setValue(font.pointSizeF())

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("charmaptool")
        s.setValue("fontfamily", self.fontChooser.currentFont().family())
        s.setValue("fontsize", self.fontSize.value())


class DocumentList(preferences.Group):
    def __init__(self, page):
        super(DocumentList, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.groupCheck = QCheckBox(toggled=self.changed)
        layout.addWidget(self.groupCheck)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Documents"))
        self.groupCheck.setText(_("Group documents by directory"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("document_list")
        self.groupCheck.setChecked(s.value("group_by_folder", False, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("document_list")
        s.setValue("group_by_folder", self.groupCheck.isChecked())


class Outline(preferences.Group):
    def __init__(self, page):
        super(Outline, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel()
        self.patternList = OutlinePatterns()
        self.patternList.listBox.setDragDropMode(QAbstractItemView.InternalMove)
        self.defaultButton = QPushButton(clicked=self.reloadDefaults)
        self.patternList.layout().addWidget(self.defaultButton, 3, 1)
        self.patternList.layout().addWidget(self.patternList.listBox, 0, 0, 5, 1)
        self.patternList.changed.connect(self.changed)
        layout.addWidget(self.label)
        layout.addWidget(self.patternList)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Outline"))
        self.defaultButton.setText(_("Default"))
        self.defaultButton.setToolTip(_("Restores the built-in outline patterns."))
        self.label.setText(_("Patterns to match in text that are shown in outline:"))

    def reloadDefaults(self):
        self.patternList.setValue(documentstructure.default_outline_patterns)

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("documentstructure")
        try:
            patterns = s.value("outline_patterns", documentstructure.default_outline_patterns, str)
        except TypeError:
            patterns = []
        self.patternList.setValue(patterns)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("documentstructure")
        if self.patternList.value() != documentstructure.default_outline_patterns:
            s.setValue("outline_patterns", self.patternList.value())
        else:
            s.remove("outline_patterns")


class OutlinePatterns(widgets.listedit.ListEdit):
    def openEditor(self, item):
        dlg = widgets.dialog.TextDialog(None,
            _("Enter a regular expression to match:"),
            app.caption("Outline"))
        userguide.addButton(dlg.buttonBox(), "outline_configure")
        dlg.setValidateFunction(is_regex)
        dlg.setText(item.text())
        if dlg.exec_():
            item.setText(dlg.text())
            return True
        return False


def is_regex(text):
    """Return True if text is a valid regular expression."""
    try:
        re.compile(text, re.M)
    except re.error:
        return False
    return True


