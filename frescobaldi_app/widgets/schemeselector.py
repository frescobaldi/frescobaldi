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
A widget that provides a scheme selector, with New and Remove buttons.
"""


from PyQt5.QtCore import QDir, QSettings, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QComboBox, QHBoxLayout, QInputDialog, QLabel, QPushButton, QWidget,
    QAction, QMenu, QFileDialog)

import app
import icons
import os


class SchemeSelector(QWidget):

    currentChanged = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super(SchemeSelector, self).__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel()
        self.scheme = QComboBox()
        self.menuButton = QPushButton(flat=True)
        menu = QMenu(self.menuButton)
        self.menuButton.setMenu(menu)
        layout.addWidget(self.label)
        layout.addWidget(self.scheme)
        layout.addWidget(self.menuButton)
        layout.addStretch(1)
        # action generator
        def act(slot, icon=None):
            a = QAction(self, triggered=slot)
            self.addAction(a)
            icon and a.setIcon(icons.get(icon))
            return a

        # add action
        a = self.addAction_ = act(self.slotAdd, 'list-add')
        menu.addAction(a)

        # remove action
        a = self.removeAction = act(self.slotRemove, 'list-remove')
        menu.addAction(a)


        # rename action
        a = self.renameAction = act(self.slotRename, 'document-edit')
        menu.addAction(a)

        menu.addSeparator()

        # import action
        a = self.importAction = act(self.slotImport, 'document-open')
        menu.addAction(a)

        # export action
        a = self.exportAction = act(self.slotExport, 'document-save-as')
        menu.addAction(a)


        self.scheme.currentIndexChanged.connect(self.slotSchemeChanged)
        app.translateUI(self)

    def translateUI(self):
        self.label.setText(_("Scheme:"))
        self.menuButton.setText(_("&Menu"))
        self.addAction_.setText(_("&Add..."))
        self.removeAction.setText(_("&Remove"))
        self.renameAction.setText(_("Re&name..."))
        self.importAction.setText(_("&Import..."))
        self.exportAction.setText(_("&Export..."))

    def slotSchemeChanged(self, index):
        """Called when the Scheme combobox is changed by the user."""
        self.disableDefault(self.scheme.itemData(index) == 'default')
        self.currentChanged.emit()
        self.changed.emit()

    def disableDefault(self, val):
        self.removeAction.setDisabled(val)
        self.renameAction.setDisabled(val)

    def schemes(self):
        """Returns the list with internal names of currently available schemes."""
        return [self.scheme.itemData(i) for i in range(self.scheme.count())]

    def currentScheme(self):
        """Returns the internal name of the currently selected scheme"""
        return self.scheme.itemData(self.scheme.currentIndex())

    def insertSchemeItem(self, name, scheme):
        for i in range(1, self.scheme.count()):
            n = self.scheme.itemText(i)
            if n.lower() > name.lower():
                self.scheme.insertItem(i, name, scheme)
                break
        else:
            self.scheme.addItem(name, scheme)

    def addScheme(self, name):
        num, key = 1, 'user1'
        while key in self.schemes() or key in self._schemesToRemove:
            num += 1
            key = 'user{0}'.format(num)
        self.insertSchemeItem(name, key)
        self.scheme.setCurrentIndex(self.scheme.findData(key))
        return key

    def slotAdd(self):
        name, ok = QInputDialog.getText(self,
            app.caption(_("Add Scheme")),
            _("Please enter a name for the new scheme:"))
        if ok:
            self.addScheme(name)


    def slotRemove(self):
        index = self.scheme.currentIndex()
        scheme = self.scheme.itemData(index)
        if scheme == 'default':
            return # default can not be removed

        self._schemesToRemove.add(scheme)
        self.scheme.removeItem(index)

    def slotRename(self):
        index = self.scheme.currentIndex()
        name = self.scheme.itemText(index)
        scheme = self.scheme.itemData(index)
        newName, ok = QInputDialog.getText(self, _("Rename"), _("New name:"), text=name)
        if ok:
            self.scheme.blockSignals(True)
            self.scheme.removeItem(index)
            self.insertSchemeItem(newName, scheme)
            self.scheme.setCurrentIndex(self.scheme.findData(scheme))
            self.scheme.blockSignals(False)
            self.changed.emit()

    def slotImport(self):
        filetypes = "{0} (*.xml);;{1} (*)".format(_("XML Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import color theme"))
        filename = QFileDialog.getOpenFileName(self, caption, QDir.homePath(), filetypes)[0]
        if filename:
            self.parent().import_(filename)

    def slotExport(self):
        name = self.scheme.currentText()
        filetypes = "{0} (*.xml);;{1} (*)".format(_("XML Files"), _("All Files"))
        caption = app.caption(_("dialog title",
            "Export {name}").format(name=name))
        path = os.path.join(QDir.homePath(), name+'.xml')
        filename = QFileDialog.getSaveFileName(self, caption, path, filetypes)[0]
        if filename:
            if os.path.splitext(filename)[1] != '.xml':
                filename += '.xml'
            self.parent().export(name, filename)


    def loadSettings(self, currentKey, namesGroup):
        # don't mark schemes for removal anymore
        self._schemesToRemove = set()

        s = QSettings()
        cur = s.value(currentKey, "default", str)

        # load the names for the shortcut schemes
        s.beginGroup(namesGroup)
        block = self.scheme.blockSignals(True)
        self.scheme.clear()
        self.scheme.addItem(_("Default"), "default")
        lst = [(s.value(key, key, str), key) for key in s.childKeys()]
        for name, key in sorted(lst, key=lambda f: f[0].lower()):
            self.scheme.addItem(name, key)

        # find out index
        index = self.scheme.findData(cur)
        self.disableDefault(cur == 'default')
        self.scheme.setCurrentIndex(index)
        self.scheme.blockSignals(block)
        self.currentChanged.emit()

    def saveSettings(self, currentKey, namesGroup, removePrefix=None):
        # first save new scheme names
        s = QSettings()
        s.beginGroup(namesGroup)
        for i in range(self.scheme.count()):
            if self.scheme.itemData(i) != 'default':
                s.setValue(self.scheme.itemData(i), self.scheme.itemText(i))

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


