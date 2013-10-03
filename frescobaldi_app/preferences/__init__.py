# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
The Preferences Dialog.
"""

from __future__ import unicode_literals


from PyQt4.QtCore import QSettings, QSize, Qt, pyqtSignal
from PyQt4.QtGui import (
    QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QKeySequence,
    QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QWidget)

import app
import qutil
import help
import icons
import widgets

from . import prefshelp

_prefsindex = 0 # global setting for selected prefs page but not saved on exit

def pageorder():
    """Yields the page item classes in order."""
    yield General
    yield LilyPond
    yield Midi
    yield Helpers
    yield Paths
    yield Documentation
    yield Shortcuts
    yield FontsColors
    yield Tools


class PreferencesDialog(QDialog):
    
    def __init__(self, mainwindow):
        super(PreferencesDialog, self).__init__(mainwindow)
        self.setWindowModality(Qt.WindowModal)
        self.addAction(mainwindow.actionCollection.help_whatsthis)
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
        b.button(QDialogButtonBox.Help).clicked.connect(self.showHelp)
        b.button(QDialogButtonBox.Help).setShortcut(QKeySequence.HelpContents)
        b.button(QDialogButtonBox.Apply).setEnabled(False)
        
        # fill the pagelist
        self.pagelist.setIconSize(QSize(32, 32))
        self.pagelist.setSpacing(2)
        for item in pageorder():
            self.pagelist.addItem(item())
        self.pagelist.currentItemChanged.connect(self.slotCurrentItemChanged)
        
        app.translateUI(self, 100)
        # read our size and selected page
        qutil.saveDialogSize(self, "preferences/dialog/size", QSize(500, 300))
        self.pagelist.setCurrentRow(_prefsindex)
        
    def translateUI(self):
        self.pagelist.setFixedWidth(self.pagelist.sizeHintForColumn(0) + 12)
        self.setWindowTitle(app.caption(_("Preferences")))
    
    def done(self, result):
        if result and self.buttons.button(QDialogButtonBox.Apply).isEnabled():
            self.saveSettings()
        # save our size and selected page
        global _prefsindex
        _prefsindex = self.pagelist.currentRow()
        super(PreferencesDialog, self).done(result)
    
    def pages(self):
        """Yields the settings pages that are already instantiated."""
        for n in range(self.stack.count()):
            yield self.stack.widget(n)
    
    def showHelp(self):
        help.help(self.pagelist.currentItem().help)
        
    def loadSettings(self):
        """Loads the settings on reset."""
        for page in self.pages():
            page.loadSettings()
            page.hasChanges = False
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
            
    def saveSettings(self):
        """Saves the settings and applies them."""
        for page in self.pages():
            if page.hasChanges:
                page.saveSettings()
                page.hasChanges = False
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(False)
        
        # emit the signal
        app.settingsChanged()
    
    def slotCurrentItemChanged(self, item):
        item.activate()
        
    def changed(self):
        """Call this to enable the Apply button."""
        self.buttons.button(QDialogButtonBox.Apply).setEnabled(True)


class PrefsItemBase(QListWidgetItem):
    help = prefshelp.preferences_dialog
    def __init__(self):
        super(PrefsItemBase, self).__init__()
        self._widget = None
        self.setIcon(icons.get(self.iconName))
        app.translateUI(self)
    
    def activate(self):
        dlg = self.listWidget().parentWidget()
        if self._widget is None:
            w = self._widget = self.widget(dlg)
            dlg.stack.addWidget(w)
            w.loadSettings()
            w.changed.connect(dlg.changed)
            w.changed.connect(w.markChanged)
        dlg.stack.setCurrentWidget(self._widget)


class General(PrefsItemBase):
    help = prefshelp.preferences_general
    iconName = "preferences-system"
    def translateUI(self):
        self.setText(_("General Preferences"))

    def widget(self, dlg):
        import general
        return general.GeneralPrefs(dlg)
        

class LilyPond(PrefsItemBase):
    help = prefshelp.preferences_lilypond
    iconName = "lilypond-run"
    def translateUI(self):
        self.setText(_("LilyPond Preferences"))
        
    def widget(self, dlg):
        import lilypond
        return lilypond.LilyPondPrefs(dlg)


class Midi(PrefsItemBase):
    help = prefshelp.preferences_midi
    iconName = "audio-volume-medium"
    def translateUI(self):
        self.setText(_("MIDI Settings"))
    
    def widget(self, dlg):
        from . import midi
        return midi.MidiPrefs(dlg)


class Helpers(PrefsItemBase):
    help = prefshelp.preferences_helpers
    iconName = "applications-other"
    def translateUI(self):
        self.setText(_("Helper Applications"))
        
    def widget(self, dlg):
        import helpers
        return helpers.Helpers(dlg)


class Paths(PrefsItemBase):
    help = prefshelp.preferences_paths
    iconName = "folder-open"
    def translateUI(self):
        self.setText(_("Paths"))
        
    def widget(self, dlg):
        from . import paths
        return paths.Paths(dlg)


class Documentation(PrefsItemBase):
    help = prefshelp.preferences_documentation
    iconName = "help-contents"
    def translateUI(self):
        self.setText(_("LilyPond Documentation"))
        
    def widget(self, dlg):
        from . import documentation
        return documentation.Documentation(dlg)


class Shortcuts(PrefsItemBase):
    help = prefshelp.preferences_shortcuts
    iconName = "preferences-desktop-keyboard-shortcuts"
    def translateUI(self):
        self.setText(_("Keyboard Shortcuts"))
        
    def widget(self, dlg):
        from . import shortcuts
        return shortcuts.Shortcuts(dlg)
        

class FontsColors(PrefsItemBase):
    help = prefshelp.preferences_fontscolors
    iconName = "applications-graphics"
    def translateUI(self):
        self.setText(_("Fonts & Colors"))
        
    def widget(self, dlg):
        from . import fontscolors
        return fontscolors.FontsColors(dlg)


class Tools(PrefsItemBase):
    help = prefshelp.preferences_tools
    iconName = "preferences-other"
    def translateUI(self):
        self.setText(_("Tools"))
        
    def widget(self, dlg):
        from . import tools
        return tools.Tools(dlg)


class Page(QWidget):
    """Base class for settings pages."""
    changed = pyqtSignal()
    hasChanges = False
    
    def markChanged(self):
        """Called when something changes in the dialog."""
        self.hasChanges = True
    
    def loadSettings(self):
        """Should load settings from config into our widget."""
        
    def saveSettings(self):
        """Should write settings from our widget to config."""

    
class GroupsPage(Page):
    """Base class for a Page with SettingsGroups.
    
    The load and save methods of the SettingsGroup groups are automatically called.
    
    """
    def __init__(self, dialog):
        super(GroupsPage, self).__init__(dialog)
        self.groups = []
        
    def loadSettings(self):
        for group in self.groups:
            group.loadSettings()
            
    def saveSettings(self):
        for group in self.groups:
            group.saveSettings()
            

class Group(QGroupBox):
    """This is a QGroupBox that auto-adds itself to a Page."""
    changed = pyqtSignal()
    
    def __init__(self, page):
        super(Group, self).__init__()
        page.groups.append(self)
        self.changed.connect(page.changed)
        
    def loadSettings(self):
        """Should load settings from config into our widget."""
        
    def saveSettings(self):
        """Should write settings from our widget to config."""

