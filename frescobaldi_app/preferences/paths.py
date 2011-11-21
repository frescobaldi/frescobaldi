# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons
import widgets.listedit
import widgets.dialog
import preferences


class Paths(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Paths, self).__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(HyphenPaths(self))
        layout.addWidget(LilyDocPaths(self))
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
        self.listedit.setValue(s.value("paths", []) or [])
        
    def saveSettings(self):
        s = QSettings()
        s.beginGroup("hyphenation")
        paths = self.listedit.value()
        if paths:
            s.setValue("paths", paths)
        else:
            s.remove("paths")


class LilyDocPaths(preferences.Group):
    def __init__(self, page):
        super(LilyDocPaths, self).__init__(page)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.paths = LilyDocPathsList()
        self.paths.changed.connect(self.changed)
        layout.addWidget(self.paths)
        
        app.translateUI(self)
    
    def translateUI(self):
        self.setTitle(_("LilyPond Documentation"))
    
    def loadSettings(self):
        s = QSettings()
        s.beginGroup("documentation")
        self.paths.setValue(s.value("paths", []) or [])
        
    def saveSettings(self):
        s = QSettings()
        s.beginGroup("documentation")
        paths = self.paths.value()
        if paths:
            s.setValue("paths", paths)
        else:
            s.remove("paths")


class LilyDocPathsList(widgets.listedit.ListEdit):
    def openEditor(self, item):
        
        dlg = widgets.dialog.Dialog(self,
            _("Please enter a local path or a URL:"),
            app.caption("LilyPond Documentation"),
            icon = icons.get('lilypond-run'))
        urlreq = widgets.urlrequester.UrlRequester()
        urlreq.lineEdit.setCompleter(QCompleter([
            "http://lilypond.org/doc/v2.12/",
            "http://lilypond.org/doc/v2.14/",
            "http://lilypond.org/doc/v2.15/",
            ], urlreq.lineEdit))
        dlg.setMainWidget(urlreq)
        urlreq.setMinimumWidth(320)
        urlreq.lineEdit.setFocus()
        if dlg.exec_():
            item.setText(urlreq.path())
            return True
        return False


