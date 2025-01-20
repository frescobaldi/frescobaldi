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

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFontComboBox, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout, QWidget)

import app
import userguide
import qutil
import preferences
import widgets.dialog
import widgets.listedit
import documentstructure


class Tools(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super().__init__(dialog)

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
        super().__init__(page)

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
            "If checked, Frescobaldi will not shorten filenames in the log output."))
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
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.newerFilesOnly = QCheckBox(toggled=self.changed)
        layout.addWidget(self.newerFilesOnly)

        self.documentProperties = QCheckBox(toggled=self.changed)
        layout.addWidget(self.documentProperties)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Music View"))
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


class CharMap(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

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
        super().__init__(page)

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
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel()
        self.patternList = OutlinePatterns()
        self.patternList.listBox.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.defaultButton = QPushButton(clicked=self.reloadDefaults)
        self.patternList.layout().addWidget(self.defaultButton, 3, 1)
        self.patternList.layout().addWidget(self.patternList.listBox, 0, 0, 5, 1)
        self.patternList.changed.connect(self.changed)
        self.labelComments = QLabel()
        self.patternListComments = OutlinePatterns()
        self.patternListComments.listBox.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.defaultButtonComments = QPushButton(clicked=self.reloadDefaultsComments)
        self.patternListComments.layout().addWidget(self.defaultButtonComments, 3, 1)
        self.patternListComments.layout().addWidget(self.patternListComments.listBox, 0, 0, 5, 1)
        self.patternListComments.changed.connect(self.changed)
        layout.addWidget(self.label)
        layout.addWidget(self.patternList)
        layout.addWidget(self.labelComments)
        layout.addWidget(self.patternListComments)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Outline"))
        self.defaultButton.setText(_("Default"))
        self.defaultButton.setToolTip(_("Restores the built-in outline patterns."))
        self.label.setText(_("Patterns to match in text (excluding comments) that are shown in outline:"))
        self.defaultButtonComments.setText(_("Default"))
        self.defaultButtonComments.setToolTip(_("Restores the built-in outline patterns."))
        self.labelComments.setText(_("Patterns to match in text (including comments) that are shown in outline:"))

    def reloadDefaults(self):
        self.patternList.setValue(documentstructure.default_outline_patterns)

    def reloadDefaultsComments(self):
        self.patternListComments.setValue(documentstructure.default_outline_patterns_comments)

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("documentstructure")
        try:
            patterns = s.value("outline_patterns", documentstructure.default_outline_patterns, str)
        except TypeError:
            patterns = []
        try:
            patterns_comments = s.value("outline_patterns_comments", documentstructure.default_outline_patterns_comments, str)
        except TypeError:
            patterns_comments = []
        self.patternList.setValue(patterns)
        self.patternListComments.setValue(patterns_comments)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("documentstructure")
        if self.patternList.value() != documentstructure.default_outline_patterns:
            s.setValue("outline_patterns", self.patternList.value())
        else:
            s.remove("outline_patterns")
        if self.patternListComments.value() != documentstructure.default_outline_patterns_comments:
            s.setValue("outline_patterns_comments", self.patternListComments.value())
        else:
            s.remove("outline_patterns_comments")


class OutlinePatterns(widgets.listedit.ListEdit):
    def openEditor(self, item):
        dlg = widgets.dialog.TextDialog(self,
            _("Enter a regular expression to match:"),
            app.caption("Outline"))
        userguide.addButton(dlg.buttonBox(), "outline_configure")
        dlg.setValidateFunction(is_regex)
        dlg.setText(item.text())
        if dlg.exec():
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
