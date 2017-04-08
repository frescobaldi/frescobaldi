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

        layout.addWidget(Versions(self))
        layout.addWidget(Target(self))
        layout.addWidget(Running(self))


class Versions(preferences.Group):
    def __init__(self, page):
        super(Versions, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.instances = InfoList(self)
        self.instances.changed.connect(self.changed)
        self.instances.defaultButton.clicked.connect(self.defaultButtonClicked)
        layout.addWidget(self.instances)
        self.auto = QCheckBox(clicked=self.changed)
        layout.addWidget(self.auto)
        app.translateUI(self)
        userguide.openWhatsThis(self)

    def defaultButtonClicked(self):
        self._defaultCommand = self.instances.listBox.currentItem()._info.command
        for item in self.instances.items():
            item.display()
        self.changed.emit()

    def translateUI(self):
        self.setTitle(_("LilyPond versions to use"))
        self.auto.setText(_("Automatically choose LilyPond version from document"))
        self.auto.setToolTip(_(
            "If checked, the document's version determines the LilyPond version to use.\n"
            "See \"What's This\" for more information."))
        self.auto.setWhatsThis(userguide.html("prefs_lilypond_autoversion") +
            _("See also {link}.").format(link=userguide.link("prefs_lilypond")))

    def loadSettings(self):
        s = settings()
        default = lilypondinfo.default()
        self._defaultCommand = s.value("default", default.command, str)
        self.auto.setChecked(s.value("autoversion", False, bool))
        infos = sorted(lilypondinfo.infos(), key=lambda i: i.version())
        if not infos:
            infos = [default]
        items = [InfoItem(info) for info in infos]
        self.instances.setItems(items)
        for item in items:
            if item._info.command == self._defaultCommand:
                self.instances.setCurrentItem(item)
                break

    def saveSettings(self):
        infos = [item._info for item in self.instances.items()]
        if infos:
            for info in infos:
                if info.command == self._defaultCommand:
                    break
            else:
                self._defaultCommand = infos[0].command
        else:
            infos = [lilypondinfo.default()]
            self._defaultCommand = infos[0].command
        s = settings()
        s.setValue("default", self._defaultCommand)
        s.setValue("autoversion", self.auto.isChecked())
        lilypondinfo.setinfos(infos)
        lilypondinfo.saveinfos()


class InfoList(widgets.listedit.ListEdit):
    def __init__(self, group):
        self.defaultButton = QPushButton()
        super(InfoList, self).__init__(group)
        self.layout().addWidget(self.defaultButton, 3, 1)
        self.layout().addWidget(self.listBox, 0, 0, 5, 1)
        self.listBox.itemSelectionChanged.connect(self._selectionChanged)

    def _selectionChanged(self):
        self.defaultButton.setEnabled(bool(self.listBox.currentItem()))

    def translateUI(self):
        super(InfoList, self).translateUI()
        self.defaultButton.setText(_("Set as &Default"))

    def infoDialog(self):
        try:
            return self._infoDialog
        except AttributeError:
            self._infoDialog = InfoDialog(self)
            return self._infoDialog

    def createItem(self):
        return InfoItem(lilypondinfo.LilyPondInfo("lilypond"))

    def openEditor(self, item):
        dlg = self.infoDialog()
        dlg.loadInfo(item._info)
        dlg.lilypond.lineEdit.setFocus()
        was_default = item._info.command == self.parentWidget()._defaultCommand
        if dlg.exec_():
            item._info = dlg.newInfo()
            if was_default:
                self.parentWidget()._defaultCommand = item._info.command
            return True
        return False

    def itemChanged(self, item):
        item.display()
        self.setCurrentItem(item)


class InfoItem(QListWidgetItem):
    def __init__(self, info):
        super(InfoItem, self).__init__()
        self._info = info

    def display(self):
        text = self._info.prettyName()
        if self._info.version():
            self.setIcon(icons.get("lilypond-run"))
        else:
            self.setIcon(icons.get("dialog-error"))
        if self._info.command == self.listWidget().parentWidget().parentWidget()._defaultCommand:
            text += " [{0}]".format(_("default"))
        self.setText(text)


class InfoDialog(QDialog):
    def __init__(self, parent):
        super(InfoDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        self.tab = QTabWidget()
        tab_general = QWidget()
        tab_toolcommands = QWidget()
        self.tab.addTab(tab_general, "")
        self.tab.addTab(tab_toolcommands, "")

        # general tab
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        tab_general.setLayout(vbox)

        hbox = QHBoxLayout()
        self.lilyname = QLineEdit()
        self.lilynameLabel = l = QLabel()
        l.setBuddy(self.lilyname)
        hbox.addWidget(l)
        hbox.addWidget(self.lilyname)
        vbox.addLayout(hbox)

        self.lilypond = widgets.urlrequester.UrlRequester()
        self.lilypond.setFileMode(QFileDialog.ExistingFile)
        self.lilypondLabel = l = QLabel()
        l.setBuddy(self.lilypond)
        vbox.addWidget(l)
        vbox.addWidget(self.lilypond)

        self.auto = QCheckBox()
        vbox.addWidget(self.auto)
        vbox.addStretch(1)

        # toolcommands tab
        grid = QGridLayout()
        grid.setSpacing(4)
        tab_toolcommands.setLayout(grid)

        self.ly_tool_widgets = {}
        row = 0
        for name, gui in self.toolnames():
            w = QLineEdit()
            l = QLabel()
            l.setBuddy(w)
            grid.addWidget(l, row, 0)
            grid.addWidget(w, row, 1)
            row += 1
            self.ly_tool_widgets[name] = (l, w)

        layout.addWidget(self.tab)
        layout.addWidget(widgets.Separator())
        b = self.buttons = QDialogButtonBox(self)
        layout.addWidget(b)

        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "prefs_lilypond")
        app.translateUI(self)
        qutil.saveDialogSize(self, "/preferences/lilypond/lilypondinfo/dialog/size")

    def toolnames(self):
        """Yield tuples (name, GUI name) for the sub tools we allow to be configured."""
        yield 'convert-ly', _("Convert-ly:")
        yield 'lilypond-book', _("LilyPond-book:")
        yield 'midi2ly', _("Midi2ly:")
        yield 'musicxml2ly', _("MusicXML2ly:")
        yield 'abc2ly', _("ABC2ly:")

    def translateUI(self):
        self.setWindowTitle(app.caption(_("LilyPond")))
        self.lilynameLabel.setText(_("Label:"))
        self.lilynameLabel.setToolTip(_("How this version of LilyPond will be displayed."))
        self.lilypondLabel.setText(_("LilyPond Command:"))
        self.lilypond.lineEdit.setToolTip(_("Name or full path of the LilyPond program."))
        self.auto.setText(_("Include in automatic version selection"))
        self.tab.setTabText(0, _("General"))
        self.tab.setTabText(1, _("Tool Commands"))
        for name, gui in self.toolnames():
            self.ly_tool_widgets[name][0].setText(gui)

    def loadInfo(self, info):
        """Takes over settings for the dialog from the LilyPondInfo object."""
        self.lilyname.setText(info.name)
        self.lilypond.setPath(info.command)
        self.auto.setChecked(info.auto)
        for name, gui in self.toolnames():
            self.ly_tool_widgets[name][1].setText(info.ly_tool(name))

    def newInfo(self):
        """Returns a new LilyPondInfo instance for our settings."""
        if sys.platform.startswith('darwin') and self.lilypond.path().endswith('.app'):
            info = lilypondinfo.LilyPondInfo(
                self.lilypond.path() + '/Contents/Resources/bin/lilypond')
        else:
            info = lilypondinfo.LilyPondInfo(self.lilypond.path())
        if self.lilyname.text() and not self.lilyname.text().isspace():
            info.name = self.lilyname.text()
        info.auto = self.auto.isChecked()
        for name, gui in self.toolnames():
            info.set_ly_tool(name, self.ly_tool_widgets[name][1].text())
        return info


class Running(preferences.Group):
    def __init__(self, page):
        super(Running, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.saveDocument = QCheckBox(clicked=self.changed)
        self.deleteFiles = QCheckBox(clicked=self.changed)
        self.embedSourceCode = QCheckBox(clicked=self.changed)
        self.noTranslation = QCheckBox(clicked=self.changed)
        self.includeLabel = QLabel()
        self.include = widgets.listedit.FilePathEdit()
        self.include.listBox.setDragDropMode(QAbstractItemView.InternalMove)
        self.include.changed.connect(self.changed)
        layout.addWidget(self.saveDocument)
        layout.addWidget(self.deleteFiles)
        layout.addWidget(self.embedSourceCode)
        layout.addWidget(self.noTranslation)
        layout.addWidget(self.includeLabel)
        layout.addWidget(self.include)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Running LilyPond"))
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
            "when LilyPond is started in publish mode.\n"
            "This feature is available since LilyPond 2.19.39."))
        self.noTranslation.setText(_("Run LilyPond with English messages"))
        self.noTranslation.setToolTip(_(
            "If checked, LilyPond's output messages will be in English.\n"
            "This can be useful for bug reports."))
        self.includeLabel.setText(_("LilyPond include path:"))

    def loadSettings(self):
        s = settings()
        self.saveDocument.setChecked(s.value("save_on_run", False, bool))
        self.deleteFiles.setChecked(s.value("delete_intermediate_files", True, bool))
        self.embedSourceCode.setChecked(s.value("embed_source_code", False, bool))
        self.noTranslation.setChecked(s.value("no_translation", False, bool))
        include_path = qsettings.get_string_list(s, "include_path")
        self.include.setValue(include_path)

    def saveSettings(self):
        s = settings()
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


