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
A widget that provides a scheme selector, with New and Remove buttons.
"""

from PyQt4.QtCore import QSettings, pyqtSignal
from PyQt4.QtGui import (
    QComboBox, QHBoxLayout, QInputDialog, QLabel, QPushButton, QWidget)

import app
import icons
import preferences


class SchemeSelector(QWidget):
    
    currentChanged = pyqtSignal()
    changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super(SchemeSelector, self).__init__(parent)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.label = QLabel(_("Scheme:"))
        self.scheme = QComboBox()
        self.label.setBuddy(self.scheme)
        self.add = QPushButton(icons.get('list-add'), '')
        self.remove = QPushButton(icons.get('list-remove'), '')
        layout.addWidget(self.label)
        layout.addWidget(self.scheme)
        layout.addWidget(self.add)
        layout.addWidget(self.remove)
        self.scheme.currentIndexChanged.connect(self.slotSchemeChanged)
        self.add.clicked.connect(self.addClicked)
        self.remove.clicked.connect(self.removeClicked)
        app.translateUI(self)
        
    def translateUI(self):
        self.label.setText(_("Scheme:"))
        self.add.setText(_("&New..."))
        self.remove.setText(_("&Remove"))
        
    def slotSchemeChanged(self, index):
        """Called when the Scheme combobox is changed by the user."""
        self.remove.setEnabled(bool(index))
        self.currentChanged.emit()
        self.changed.emit()
    
    def schemes(self):
        """Returns the list with internal names of currently available schemes."""
        return self._schemes
        
    def currentScheme(self):
        """Returns the internal name of the currently selected scheme"""
        return self._schemes[self.scheme.currentIndex()]
        
    def removeClicked(self):
        index = self.scheme.currentIndex()
        if index == 0:
            return # default can not be removed
        
        self._schemesToRemove.add(self._schemes[index])
        del self._schemes[index]
        del self._schemeNames[index]
        self.scheme.removeItem(index)
    
    def addClicked(self):
        name, ok = QInputDialog.getText(self,
            app.caption("Add Scheme"),
            _("Please enter a name for the new scheme:"))
        if not ok:
            return
        num, key = 1, 'user1'
        while key in self._schemes or key in self._schemesToRemove:
            num += 1
            key = 'user{0}'.format(num)
        self._schemes.append(key)
        self._schemeNames.append(name)
        self.scheme.addItem(name)
        self.scheme.setCurrentIndex(self.scheme.count() - 1)
        
    def loadSettings(self, currentKey, namesGroup):
        # dont mark schemes for removal anymore
        self._schemesToRemove = set()
        
        s = QSettings()
        cur = s.value(currentKey, "default")
        
        # load the names for the shortcut schemes
        s.beginGroup(namesGroup)
        self._schemes = ["default"]
        self._schemeNames = [_("Default")]
        for key in s.childKeys():
            self._schemes.append(key)
            self._schemeNames.append(s.value(key, key))
        block = self.scheme.blockSignals(True)
        self.scheme.clear()
        self.scheme.addItems(self._schemeNames)
        
        # find out index
        index = self._schemes.index(cur) if cur in self._schemes else 0
        self.remove.setEnabled(bool(index))
        self.scheme.setCurrentIndex(index)
        self.scheme.blockSignals(block)
        self.currentChanged.emit()
        
    def saveSettings(self, currentKey, namesGroup, removePrefix=None):
        # first save new scheme names
        s = QSettings()
        s.beginGroup(namesGroup)
        for scheme, name in zip(self._schemes, self._schemeNames)[1:]:
            s.setValue(scheme, name)
        # then remove removed schemes
        for scheme in self._schemesToRemove:
            s.remove(scheme)
        s.endGroup()
        if removePrefix:
            for scheme in self._schemesToRemove:
                s.remove("{0}/{1}".format(removePrefix, scheme))
        # then save current
        scheme = self.currentScheme()
        s.setValue(currentKey, scheme)
        # clean up
        self._schemesToRemove = set()


