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
Paths preferences page
"""


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QVBoxLayout

import app
import widgets.listedit
import preferences
import qsettings


class Paths(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Paths, self).__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(HyphenPaths(self))
        layout.addStretch(1)


class HyphenPaths(preferences.Group):
    def __init__(self, page):
        super(HyphenPaths, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.listedit = widgets.listedit.FilePathEdit()
        self.listedit.changed.connect(self.changed)
        layout.addWidget(self.listedit)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Folders containing hyphenation dictionaries"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("hyphenation")
        paths = qsettings.get_string_list(s, "paths")
        self.listedit.setValue(paths)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("hyphenation")
        paths = self.listedit.value()
        if paths:
            s.setValue("paths", paths)
        else:
            s.remove("paths")


