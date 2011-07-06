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
The Score Wizard dialog.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app


class ScoreWizardDialog(QDialog):
    def __init__(self, mainwindow):
        super(ScoreWizardDialog, self).__init__(mainwindow)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.tabBar = QTabBar()
        self.stack = QStackedWidget()
        b = QDialogButtonBox()
        b.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        layout.addWidget(self.tabBar)
        layout.addWidget(self.stack)
        layout.addWidget(b)
        
        self.tabs = []
        self.header = Header(self)
        self.tabs.append(self.header)
        self.parts = Parts(self)
        self.tabs.append(self.parts)
        self.settings = Settings(self)
        self.tabs.append(self.settings)
        self.preview = Preview(self)
        self.tabs.append(self.preview)
        
        for t in self.tabs:
            self.tabBar.addTab('')
        self.tabBar.setCurrentIndex(0)
        self.stack.setCurrentWidget(self.tabs[0].widget())
        self.tabBar.currentChanged.connect(self.slotCurrentChanged)
        
        app.translateUI(self)
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Score Setup Wizard")))
        for n, tab in enumerate(self.tabs):
            self.tabBar.setTabText(n, tab.title())
    
    def slotCurrentChanged(self, i):
        self.stack.setCurrentWidget(self.tabs[i].widget())
        
            

class Tab(object):
    def __init__(self, dialog):
        self._dialog = dialog
        self._widget = None
        
    def title(self):
        """Should return a title."""

    def widget(self):
        if self._widget is None:
            self._widget = self.createWidget(self._dialog)
            self._dialog.stack.addWidget(self._widget)
        return self._widget

    def createWidget(self, dialog):
        """Should return the widget for this tab."""
        

class Header(Tab):
    def title(self):
        return _("&Titles and Headers")

    def createWidget(self, dialog):
        from . import header
        return header.HeaderWidget(dialog)

        
class Parts(Tab):
    def title(self):
        return _("&Parts")

    def createWidget(self, dialog):
        from . import score
        return score.PartsWidget(dialog)


class Settings(Tab):
    def title(self):
        return _("&Score settings")
    
    def createWidget(self, dialog):
        from . import settings
        return settings.SettingsWidget(dialog)


class Preview(Tab):
    def title(self):
        return _("Pre&view")
    
    def createWidget(self, dialog):
        from . import preview
        return preview.PreviewWidget(dialog)


