# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#               2023 by Jean Abou Samra
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

import sys

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (
    QAction, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidgetItem, QPushButton, QTabWidget,
    QVBoxLayout, QWidget
)

import actioncollection
import actioncollectionmanager
import app
import icons
import lilypondinfo
import plugin
import qutil
import userguide
import widgets.listedit
import widgets.urlrequester


def settings():
    s = QSettings()
    # For historical reasons, this uses the same settings group as
    # the LilyPond preferences.
    s.beginGroup("lilypond_settings")
    return s

class LilyPondVersionManager(plugin.MainWindowPlugin):
    """A ``MainWindowPlugin`` to add a menu item for managing LilyPond versions."""

    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.manage_lilypond_versions.triggered.connect(self.openDialog)

    def openDialog(self):
        dlg = VersionsDialog(self.mainwindow())
        dlg.exec()
        dlg.deleteLater()


class Actions(actioncollection.ActionCollection):
    """An ``ActionCollection`` for the action that opens the LilyPond version manager."""

    name = "lilypond_versions"

    def createActions(self, parent=None):
        self.manage_lilypond_versions = QAction(parent)
        self.manage_lilypond_versions.setIcon(icons.get("view-refresh"))

    def translateUI(self):
        self.manage_lilypond_versions.setText(_("&Manage LilyPond versions..."))

class VersionsDialog(QDialog):
    """The LilyPond version manager dialog. It contains an editable list of versions."""

    def __init__(self, page):
        super().__init__(page)
        self.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.instances = InfoList(self)
        self.instances.defaultButton.clicked.connect(self.defaultButtonClicked)
        layout.addWidget(self.instances)

        b = self.buttons = QDialogButtonBox(self)
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(b)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)

        self.loadSettings()
        self.accepted.connect(self.saveSettings)

        app.translateUI(self)

    def defaultButtonClicked(self):
        self._defaultCommand = self.instances.listBox.currentItem()._info.command
        for item in self.instances.items():
            item.display()

    def translateUI(self):
        self.setWindowTitle(_("LilyPond Version Manager"))

    def loadSettings(self):
        s = settings()
        default = lilypondinfo.default()
        self._defaultCommand = s.value("default", default.command, str)
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
        ##### FIXME
        ##### userguide.addButton(b, "prefs_lilypond")
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
