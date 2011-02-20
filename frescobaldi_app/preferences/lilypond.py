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
        layout.addWidget(self.instances)
        self.auto = QCheckBox(clicked=self.changed)
        layout.addWidget(self.auto)
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("LilyPond versions to use"))
        self.auto.setText(_(
            "Enable automatic version selection "
            "(choose LilyPond version from document)"))

    def loadSettings(self):
        self.instances.clear()
        infos = [info.copy() for info in lilypondinfo.infos()]
        if not infos:
            infos = [lilypondinfo.LilyPondInfo("lilypond")]
        infos.sort(key=lambda i: i.version)
        for info in infos:
            self.instances.addItem(LilyPondInfoItem(info))
        
    def saveSettings(self):
        infos = [item._info for item in self.instances.items()]
        lilypondinfo.setinfos(infos)
        lilypondinfo.saveinfos()


class LilyPondInfoList(widgets.listedit.ListEdit):
    def __init__(self, group):
        self.defaultButton = QPushButton()
        super(LilyPondInfoList, self).__init__(group)
        self.layout().addWidget(self.defaultButton, 3, 1)
        self.layout().addWidget(self.listBox, 0, 0, 5, 1)
        
    def translateUI(self):
        super(LilyPondInfoList, self).translateUI()
        self.defaultButton.setText(_("Set as &Default"))
        
    def createItem(self):
        return LilyPondInfoItem(lilypondinfo.LilyPondInfo("lilypond"))
        
    def itemChanged(self, item):
        item.display()
        

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
        self.setText(text)



    