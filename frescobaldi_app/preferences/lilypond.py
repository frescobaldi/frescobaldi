# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
LilyPond preferences page
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import preferences
import lilypondinfo
import widgets.listedit
import widgets.urlrequester


class LilyPondPrefs(preferences.GroupsPage):
    def __init__(self, dialog):
        super(LilyPondPrefs, self).__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(LilyPondVersions(self))
        layout.addStretch(1)


class LilyPondVersions(preferences.Group):
    def __init__(self, page):
        super(LilyPondVersions, self).__init__(page)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.instances = LilyPondInfoList(self)
        self.instances.changed.connect(self.changed)
        self.instances.defaultButton.clicked.connect(self.defaultButtonClicked)
        layout.addWidget(self.instances)
        self.auto = QCheckBox(clicked=self.changed)
        layout.addWidget(self.auto)
        app.translateUI(self)
    
    def defaultButtonClicked(self):
        self._defaultCommand = self.instances.listBox.currentItem()._info.command
        for item in self.instances.items():
            item.display()
        self.changed.emit()
            
    def translateUI(self):
        self.setTitle(_("LilyPond versions to use"))
        self.auto.setText(_(
            "Enable automatic version selection "
            "(choose LilyPond version from document)"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("lilypond_version")
        self._defaultCommand = s.value("default", "lilypond")
        self.auto.setChecked(s.value("autoversion", True) in (True, "true"))
        infos = sorted(lilypondinfo.infos(), key=lambda i: i.version)
        if not infos:
            infos = [lilypondinfo.LilyPondInfo("lilypond")]
        items = [LilyPondInfoItem(info) for info in infos]
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
            infos = lilypondinfo.LilyPondInfo("lilypond")
            self._defaultCommand = "lilypond"
        s = QSettings()
        s.beginGroup("lilypond_version")
        s.setValue("default", self._defaultCommand)
        s.setValue("autoversion", self.auto.isChecked())
        lilypondinfo.setinfos(infos)
        lilypondinfo.saveinfos()


class LilyPondInfoList(widgets.listedit.ListEdit):
    def __init__(self, group):
        self.defaultButton = QPushButton()
        super(LilyPondInfoList, self).__init__(group)
        self.layout().addWidget(self.defaultButton, 3, 1)
        self.layout().addWidget(self.listBox, 0, 0, 5, 1)
        self.listBox.itemSelectionChanged.connect(self._selectionChanged)
        
    def _selectionChanged(self):
        self.defaultButton.setEnabled(bool(self.listBox.currentItem()))
        
    def translateUI(self):
        super(LilyPondInfoList, self).translateUI()
        self.defaultButton.setText(_("Set as &Default"))
    
    def lilyPondInfoDialog(self):
        try:
            return self._lilyPondInfoDialog
        except AttributeError:
            self._lilyPondInfoDialog = LilyPondInfoDialog(self)
            return self._lilyPondInfoDialog

    def createItem(self):
        return LilyPondInfoItem(lilypondinfo.LilyPondInfo("lilypond"))
    
    def openEditor(self, item):
        dlg = self.lilyPondInfoDialog()
        dlg.loadInfo(item._info)
        if dlg.exec_():
            item._info = dlg.newInfo()
            return True
        return False

    def itemChanged(self, item):
        item.display()
        self.setCurrentItem(item)
        

class LilyPondInfoItem(QListWidgetItem):
    def __init__(self, info):
        super(LilyPondInfoItem, self).__init__()
        self._info = info
    
    def display(self):
        text = self._info.command
        if self._info.version:
            text += " ({0})".format(self._info.versionString)
            self.setIcon(icons.get("lilypond-run"))
        else:
            self.setIcon(icons.get("dialog-error"))
        if self._info.command == self.listWidget().parentWidget().parentWidget()._defaultCommand:
            text += " [{0}]".format(_("default"))
        self.setText(text)


class LilyPondInfoDialog(QDialog):
    def __init__(self, parent):
        super(LilyPondInfoDialog, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        grid = QGridLayout()
        layout.addLayout(grid)
        
        self.lilypond = widgets.urlrequester.UrlRequester()
        self.lilypond.setFileMode(QFileDialog.ExistingFile)
        self.lilypondLabel = l = QLabel()
        l.setBuddy(self.lilypond)
        grid.addWidget(l, 0, 0, 1, 2)
        grid.addWidget(self.lilypond, 1, 0, 1, 2)
        
        self.convert_ly = QLineEdit()
        self.convert_lyLabel = l = QLabel()
        l.setBuddy(self.convert_ly)
        grid.addWidget(l, 2, 0)
        grid.addWidget(self.convert_ly, 2, 1)
        
        self.lilypond_book = QLineEdit()
        self.lilypond_bookLabel = l = QLabel()
        l.setBuddy(self.lilypond_book)
        grid.addWidget(l, 3, 0)
        grid.addWidget(self.lilypond_book, 3, 1)
        
        self.auto = QCheckBox()
        grid.addWidget(self.auto, 4, 1)
        
        layout.addWidget(widgets.Separator())
        b = self.buttons = QDialogButtonBox(self)
        layout.addWidget(b)
        
        b.setStandardButtons(QDialogButtonBox.Help | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        app.translateUI(self)
        
    def translateUI(self):
        self.setWindowTitle(app.caption(_("LilyPond")))
        self.lilypondLabel.setText(_("LilyPond Command:"))
        self.lilypond.lineEdit.setToolTip(_("Name or full path of the LilyPond program."))
        self.convert_lyLabel.setText(_("Convert-ly:"))
        self.lilypond_bookLabel.setText(_("LilyPond-book:"))
        self.auto.setText(_("Include in automatic version selection"))
        
    def loadInfo(self, info):
        """Takes over settings for the dialog from the LilyPondInfo object."""
        self.lilypond.setPath(info.command)
        self.convert_ly.setText(info.convert_ly)
        self.lilypond_book.setText(info.lilypond_book)
        self.auto.setChecked(info.auto)

    def newInfo(self):
        """Returns a new LilyPondInfo instance for our settings."""
        info = lilypondinfo.LilyPondInfo(self.lilypond.path())
        info.auto = self.auto.isChecked()
        info.convert_ly = self.convert_ly.text()
        info.lilypond_book = self.lilypond_book.text()
        return info


