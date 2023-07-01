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
LilyPond preferences page
"""


import os
import sys

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem,
    QPushButton, QRadioButton, QTabWidget, QVBoxLayout, QWidget)

import app
import userguide
import qutil
import icons
import preferences
import lilypondinfo
import qsettings
import widgets.listedit
import widgets.urlrequester


def settings():
    s = QSettings()
    s.beginGroup("lilypond_settings")
    return s


class LilyPondPrefs(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(LilyPondPrefs, self).__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(Target(self))
        layout.addWidget(Running(self))


class Running(preferences.Group):
    def __init__(self, page):
        super(Running, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.autoVersion = QCheckBox(clicked=self.changed)
        self.saveDocument = QCheckBox(clicked=self.changed)
        self.deleteFiles = QCheckBox(clicked=self.changed)
        self.embedSourceCode = QCheckBox(clicked=self.changed)
        self.noTranslation = QCheckBox(clicked=self.changed)
        self.includeLabel = QLabel()
        self.include = widgets.listedit.FilePathEdit()
        self.include.listBox.setDragDropMode(QAbstractItemView.InternalMove)
        self.include.changed.connect(self.changed)
        layout.addWidget(self.autoVersion)
        layout.addWidget(self.saveDocument)
        layout.addWidget(self.deleteFiles)
        layout.addWidget(self.embedSourceCode)
        layout.addWidget(self.noTranslation)
        layout.addWidget(self.includeLabel)
        layout.addWidget(self.include)
        app.translateUI(self)
        userguide.openWhatsThis(self)

    def translateUI(self):
        self.setTitle(_("Running LilyPond"))
        self.autoVersion.setText(_("Automatically choose LilyPond version from document"))
        self.autoVersion.setToolTip(_(
            "If checked, the document's version determines the LilyPond version to use.\n"
            "See \"What's This\" for more information."))
        self.autoVersion.setWhatsThis(userguide.html("prefs_lilypond_autoversion") +
            _("See also {link}.").format(link=userguide.link("prefs_lilypond")))
        self.saveDocument.setText(_("Save document if possible"))
        self.saveDocument.setToolTip(_(
            "If checked, the document is saved when it is local and modified.\n"
            "Otherwise a temporary file is used to run LilyPond."))
        self.deleteFiles.setText(_("Delete intermediate output files"))
        self.deleteFiles.setToolTip(_(
            "If checked, LilyPond will delete intermediate PostScript files."))
        self.embedSourceCode.setText(_("Embed Source Code files in publish mode"))
        self.embedSourceCode.setToolTip(_(
            "If checked, the LilyPond source files will be embedded in the PDF\n"
            "when LilyPond is started in publish mode."))
        self.noTranslation.setText(_("Run LilyPond with English messages"))
        self.noTranslation.setToolTip(_(
            "If checked, LilyPond's output messages will be in English.\n"
            "This can be useful for bug reports."))
        self.includeLabel.setText(_("LilyPond include path:"))

    def loadSettings(self):
        s = settings()
        self.autoVersion.setChecked(s.value("autoversion", False, bool))
        self.saveDocument.setChecked(s.value("save_on_run", False, bool))
        self.deleteFiles.setChecked(s.value("delete_intermediate_files", True, bool))
        self.embedSourceCode.setChecked(s.value("embed_source_code", False, bool))
        self.noTranslation.setChecked(s.value("no_translation", False, bool))
        include_path = qsettings.get_string_list(s, "include_path")
        self.include.setValue(include_path)

    def saveSettings(self):
        s = settings()
        s.setValue("autoversion", self.autoVersion.isChecked())
        s.setValue("save_on_run", self.saveDocument.isChecked())
        s.setValue("delete_intermediate_files", self.deleteFiles.isChecked())
        s.setValue("embed_source_code", self.embedSourceCode.isChecked())
        s.setValue("no_translation", self.noTranslation.isChecked())
        s.setValue("include_path", self.include.value())


class Target(preferences.Group):
    def __init__(self, page):
        super(Target, self).__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.targetPDF = QRadioButton(toggled=page.changed)
        self.targetSVG = QRadioButton(toggled=page.changed)
        self.openDefaultView = QCheckBox(clicked=page.changed)

        layout.addWidget(self.targetPDF, 0, 0)
        layout.addWidget(self.targetSVG, 0, 1)
        layout.addWidget(self.openDefaultView, 1, 0, 1, 5)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Default output format"))
        self.targetPDF.setText(_("PDF"))
        self.targetPDF.setToolTip(_(
            "Create PDF (Portable Document Format) documents by default."))
        self.targetSVG.setText(_("SVG"))
        self.targetSVG.setToolTip(_(
            "Create SVG (Scalable Vector Graphics) documents by default."))
        self.openDefaultView.setText(_("Open default viewer after successful compile"))
        self.openDefaultView.setToolTip(_(
            "Shows the PDF or SVG music view when a compile job finishes "
            "successfully."))

    def loadSettings(self):
        s = settings()
        target = s.value("default_output_target", "pdf", str)
        if target == "svg":
            self.targetSVG.setChecked(True)
            self.targetPDF.setChecked(False)
        else:
            self.targetSVG.setChecked(False)
            self.targetPDF.setChecked(True)
        self.openDefaultView.setChecked(s.value("open_default_view", True, bool))

    def saveSettings(self):
        s = settings()
        if self.targetSVG.isChecked():
            target = "svg"
        else:
            target = "pdf"
        s.setValue("default_output_target", target)
        s.setValue("open_default_view", self.openDefaultView.isChecked())
