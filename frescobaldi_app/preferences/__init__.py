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
The Preferences Dialog.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
    widgets,
    )


_prefsindex = 0 # global setting for selected prefs page but not saved on exit


class PreferencesDialog(QDialog):
    
    def __init__(self, mainwindow):
        super(PreferencesDialog, self).__init__(mainwindow)
        self.mainwindow = mainwindow
        
        self.setWindowTitle(app.caption(_("Preferences")))
        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)
        
        
        # listview to the left, stacked widget to the right
        top = QHBoxLayout()
        layout.addLayout(top)
        
        self.pagelist = QListWidget(self)
        self.stack = QStackedWidget(self)
        top.addWidget(self.pagelist, 0)
        top.addWidget(self.stack, 2)
        
        layout.addWidget(widgets.Separator(self))
        
        b = self.buttons = QDialogButtonBox(self)
        b.setStandardButtons(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
            | QDialogButtonBox.Apply
            | QDialogButtonBox.Reset
            | QDialogButtonBox.Help)
        layout.addWidget(b)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        b.button(QDialogButtonBox.Apply).clicked.connect(self.saveSettings)
        b.button(QDialogButtonBox.Reset).clicked.connect(self.loadSettings)
        
        # fill the pagelist
        self.pagelist.setIconSize(QSize(32, 32))
        self.pages = []
        for item in (
            General,
            LilyPond,
            Shortcuts,
                ):
            self.pagelist.addItem(item())
        self.pagelist.setFixedWidth(self.pagelist.sizeHintForColumn(0) + 12)
        self.pagelist.currentItemChanged.connect(self.slotCurrentItemChanged)
        
        # read our size and selected page
        self.resize(QSettings().value("prefsize", QSize(500, 300)))
        self.pagelist.setCurrentRow(_prefsindex)
        
    def done(self, result):
        if result:
            self.saveSettings()
        # save our size and selected page
        global _prefsindex
        _prefsindex = self.pagelist.currentRow()
        QSettings().setValue("prefsize", self.size())
        super(PreferencesDialog, self).done(result)
        
    def loadSettings(self):
        """Loads the settings on init or reset."""
        for page in self.pages:
            page.loadSettings()
            
    def saveSettings(self):
        """Saves the settings and applies them."""
        for page in self.pages:
            page.saveSettings()
        
        # emit the signal
        app.settingsChanged()
    
    def slotCurrentItemChanged(self, item):
        item.activate()
        

class PrefsItemBase(QListWidgetItem):
    def __init__(self):
        super(PrefsItemBase, self).__init__()
        self._widget = None
        self.setup()
    
    def activate(self):
        dlg = self.listWidget().parentWidget()
        if self._widget is None:
            self._widget = self.widget(dlg)
            dlg.stack.addWidget(self._widget)
            self._widget.loadSettings()
        dlg.stack.setCurrentWidget(self._widget)


class General(PrefsItemBase):
    def setup(self):
        self.setText(_("General Preferences"))
        self.setIcon(icons.get("configure"))

    def widget(self, dlg):
        return QLabel("General prefs,\nto be implemented")
        

class LilyPond(PrefsItemBase):
    def setup(self):
        self.setText(_("LilyPond Preferences"))
        self.setIcon(icons.get("lilypond-run"))
        
    def widget(self, dlg):
        return QLabel("LilyPond prefs,\nto be implemented")


class Shortcuts(PrefsItemBase):
    def setup(self):
        self.setText(_("Keyboard Shortcuts"))
        self.setIcon(icons.get("configure-shortcuts"))
        
    def widget(self, dlg):
        import shortcuts
        return shortcuts.Shortcuts(dlg)
        

class Page(QWidget):
    """Base class for settings pages."""
    def __init__(self, dialog):
        QWidget.__init__(self)
        self.dialog = dialog
        dialog.pages.append(self)
        
    def loadSettings(self):
        """Should load settings from config into our widget."""
        
    def saveSettings(self):
        """Should write settings from our widget to config."""
    
    
    
        