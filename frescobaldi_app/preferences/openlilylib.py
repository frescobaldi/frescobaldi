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
LilyPond preferences page
"""
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QTabWidget,
    QFileDialog)
from PyQt5.QtGui import QIcon

import app
import icons
import preferences
import widgets.listedit
import widgets.urlrequester
import openlilylib

class OpenLilyLibPrefs(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(OpenLilyLibPrefs, self).__init__(dialog)
        self.lib = openlilylib.lib

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.scrolledWidget.setLayout(layout)

        self.oll_root = OllRoot(self)
        self.packages = Packages(self)
        self.config = Config(self)

        layout.addWidget(self.oll_root)
        layout.addWidget(self.packages)
        layout.addWidget(self.config)
        
        self.changed.connect(self.updatePage)
        self.updatePage()
        
    def updatePage(self):
        valid = self.lib.valid()
        self.packages.readPackages()
        self.packages.setEnabled(valid)
        self.config.setEnabled(valid)
        #TODO: Load Config tabs

class OllPreferenceGroup(preferences.Group):
    """Base class for openLilyLib preference page widgets"""
    def __init__(self, page):
        super(OllPreferenceGroup, self).__init__(page)
        self.page = page
        self.lib = page.lib

class OllRoot(OllPreferenceGroup):
    """Basic openLilyLib installation"""
    def __init__(self, page):
        super(OllRoot, self).__init__(page)

        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel()
        self.directory = widgets.urlrequester.UrlRequester()
        self.directory.setFileMode(QFileDialog.Directory)
        self.directory.editingFinished.connect(self.rootChanged)
        
        layout.addWidget(self.label)
        layout.addWidget(self.directory)

        app.translateUI(self)
        self.loadSettings()

    def translateUI(self):
        self.setTitle(_("openLilyLib Installation directory:"))
        self.label.setText(_("Root directory:"))
        tt = (_("Root directory below which openLilyLib packages are installed."))
        self.label.setToolTip(tt)
        self.directory.setToolTip(tt)

    def loadSettings(self):
        self.directory.setPath(self.lib.root())

    def rootChanged(self):
        root = self.lib.root()
        if root == self.directory.path():
            return
        self.lib.setRoot(self.directory.path())
        valid = self.lib.valid()
        if not valid:
            # TODO: Provide opportunity to install oll-core now
            pass
        bg = 'white' if valid or root == '' else 'yellow'
        self.directory.setStyleSheet("background-color:{};".format(bg))
        self.page.changed.emit()


class Packages(OllPreferenceGroup):
    def __init__(self, page):
        super(Packages, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.packages = PackageList(self)
        layout.addWidget(self.packages)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Installed openLilyLib packages"))

    def readPackages(self):
        self.packages.readPackages()


class PackageList(widgets.listedit.ListEdit):
    def __init__(self, group):

        self.page = group.page
        self.group = group
        self.lib = group.lib

        # This button has to be added before calling super()
        self.updateButton = QPushButton(icons.get('document-edit'), '')
        super(PackageList, self).__init__(group)
        self.layout().addWidget(self.updateButton, 7, 1)
        #TODO: Add proper configuration when action is implemented

        self.readPackages()

        self._TEMP_keepButtonsOff()

    def _TEMP_keepButtonsOff(self):
        """TEMPORARY FUNCTION AS LONG AS HANDLING IS NOT IMPLEMENTED"""
        self.addButton.setEnabled(False)
        self.editButton.setEnabled(False)
        self.removeButton.setEnabled(False)
        self.updateButton.setEnabled(False)

    def connectSlots(self):
        super(PackageList, self).connectSlots()
        self.listBox.itemSelectionChanged.connect(self._selectionChanged)
        self.updateButton.clicked.connect(self.updateAll)

    def translateUI(self):
        super(PackageList, self).translateUI()
        self.editButton.setText(_("&Update..."))
        self.updateButton.setText(_("&Update all"))

    def readPackages(self):
        current_row = self.listBox.currentRow()
        self.listBox.clear()
        self._packages = self.page.lib.packages()
        if self._packages:
            names = ['oll-core'] + sorted([p for p in self._packages.keys() if p != 'oll-core'])
            for n in names:
                self.addItem(PackageInfoItem(self._packages[n]))
            self.listBox.setCurrentRow(max(0, current_row))

    def addClicked(self, button):
        """Download and install new openLilyLib package"""
        #TODO: Not implemented yet
        pass

    def editClicked(self, button):
        """Update current package"""
        #TODO: Note implemented yet
        pass
#        item = self.listBox.currentItem()
#        item and self.updatePackage(item)

    def removeClicked(self, item):
        """Remove current package (from disk)"""
        #TODO: Note implemented yet
        pass
#        item = self.listBox.currentItem()
#        if item:
#            self.removePackage(item)

    def _selectionChanged(self):
        # TODO: check if the package has a dedicated config tab and load it
        # otherwise load the generic one that simply displays some information
        # (from the \declarePackage command)
        self._TEMP_keepButtonsOff()

    def updatePackage(self, item):
        # Depending on the presence of Git
        # - Y
        #   - run git status (ask if anything is to be done)
        #   - ask if master should be checked out
        #   - run git pull
        #   - optionally reset to original state (maybe we have saved a stash?)
        # - N
        #   - look for the zip and compare version
        #   - if newer, download and replace
        # Note that this may take time, so it should be done with feedback (look into lilypond-version-testing)
        pass

    def removePackage(self, item):
        # TODO:
        # Ask if the package really should be deleted
        # - delete from disk
        # - update list
        # self.removeItem(item)
        pass

    def updateAll(self, item):
        """Ask all packages to be updated"""
        for i in range(self.listBox.count()):
            self.updatePackage(self.listBox.item(i))

    def itemChanged(self, item):
        item.display()
        self.setCurrentItem(item)


class PackageInfoItem(QListWidgetItem):
    def __init__(self, package):
        super(PackageInfoItem, self).__init__()
        self._package = package
        # TODO: Retrieve more data

    def display(self):
        self.setText("{} | {}".format(self._package.name, self._package.shortDescription))
        self.setToolTip("<nobr><strong>{}</strong></nobr><br /><br />{}</font>".format(
            self._package.root, self._package.description))
        if self._package.icon:
            self.setIcon(QIcon(os.path.join(self._package.root, 'icon.svg')))
        else:
            self.setIcon(icons.get("package"))


class Config(OllPreferenceGroup):
    def __init__(self, page):
        super(Config, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.tabs = QTabWidget()
        # TODO: Create tabs for each installed package
        # If the package is explicitly supported there will be a dedicated Class
        # Otherwise show a generic tab just showing the info
        # (Alternative: Only show tab when package is explicitly supported and rely on the list's tooltip otherwise
        
        layout.addWidget(self.tabs)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Package configuration"))
