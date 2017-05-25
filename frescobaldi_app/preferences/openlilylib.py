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

import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QTabWidget,
    QFileDialog,
    QWidget)

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
        self.packages.packages.itemSelectionChanged.disconnect(self.config.showPackage)
        self.config.invalitatePages()
        self.packages.readPackages()
        self.packages.setEnabled(valid)
        self.config.setEnabled(valid)
        self.packages.packages.itemSelectionChanged.connect(self.config.showPackage)
        self.config.showPackage()

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

    def selectedPackage(self):
        """Returns OLLPackage object representing selected item."""
        index = self.listBox.currentRow()
        if index < 0:
            return None
        package = self.listBox.item(index)._package
        return package

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
        self.setText("{} | {}".format(self._package.displayName, self._package.shortDescription))
        self.setToolTip("<nobr><strong>{}</strong></nobr><br /><br />{}</font>".format(
            self._package.root, self._package.description))
        self.setIcon(self._package.icon)

class PackageInfoLabel(QLabel):
    def __init__(self, text = None):
        super(PackageInfoLabel, self).__init__()
        if text is not None:
            self.setText(text)
        self.style()

    def style(self):
        self.setAlignment(Qt.AlignTop)
        self.setStyleSheet("font-weight: bold")

class PackageInfoPage(QWidget):
    """Page in tabwidget displaying metadata of a package"""
    def __init__(self, package):
        super(PackageInfoPage, self).__init__()
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop );
        self.setLayout(layout)

        self.display_name_label = PackageInfoLabel()
        self.display_name = PackageInfoLabel(package.displayName)
        self.display_name.setStyleSheet("font-weight: bold")

        self.short_description = QLabel(package.shortDescription)
        desc_text = ' '.join(package.description.split('\n'))
        self.description = QLabel(desc_text)
        self.description.setWordWrap(True)

        self.maintainers_label = PackageInfoLabel()
        self._maintainers = [self.linkifyEmail(m) for m in package.maintainers]
        self.maintainers = QLabel('<br />'.join(self._maintainers))
        self.maintainers.setWordWrap(True)
        self.maintainers.setOpenExternalLinks(True)

        self.repository_label = PackageInfoLabel()
        repo_link = '<a href="{url}">{url}</a>'.format(url = package.repository)
        self.repository = QLabel(repo_link)
        self.repository.setOpenExternalLinks(True)

        self.version_label = PackageInfoLabel()
        self.version = QLabel(package.version)

        self.dependencies_label = PackageInfoLabel()
        oll_depends = "oll-core: {}".format(package.oll_core_version)
        deps = [oll_depends]
        for d in package.dependencies:
            deps.append("{}: {}".format(d[0], d[1]))
        dependencies = '<br />'.join(deps)
        self.dependencies = QLabel(dependencies)

        self.license_label = PackageInfoLabel()
        self.license = QLabel(package.license)

        layout.addWidget(self.display_name_label, 0, 0)
        layout.addWidget(self.display_name, 0, 1)
        layout.addWidget(self.short_description, 1, 1)
        layout.addWidget(self.description, 2, 1)
        layout.addWidget(self.maintainers_label, 3, 0)
        layout.addWidget(self.maintainers, 3, 1)
        layout.addWidget(self.repository_label, 4, 0)
        layout.addWidget(self.repository, 4, 1)
        layout.addWidget(self.version_label, 5, 0)
        layout.addWidget(self.version, 5, 1)
        layout.addWidget(self.dependencies_label, 6, 0)
        layout.addWidget(self.dependencies, 6, 1)
        layout.addWidget(self.license_label, 7, 0)
        layout.addWidget(self.license, 7, 1)

        app.translateUI(self)

    def translateUI(self):
        self.display_name_label.setText(_('Package:'))
        maintainers_label_text = (_('Maintainer:')) if len(self._maintainers) == 1 else (_('Maintainers:'))
        self.maintainers_label.setText(maintainers_label_text)
        self.repository_label.setText(_("Repository:"))
        self.version_label.setText(_("Version:"))
        self.dependencies_label.setText(_("Dependencies:"))
        self.license_label.setText(_("License:"))

    def linkifyEmail(self, maintainer):
        """Create a mailto: link if a string contains a < > address.
        This really doesn't check for correctness, and it's up to the package maintainer
        to format the field correctly."""
        email = re.compile('(.*)<(.+)>')
        m = email.search(maintainer)
        if m:
            maintainer = m.group(1) + '<a href="mailto:{link}">{link}</a>'.format(link = m.group(2))
        return maintainer


class Config(OllPreferenceGroup):
    def __init__(self, page):
        super(Config, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.packageList = self.page.packages.packages
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Cache pages which are created when first shown
        self.pages = {}

        self.page.packages.packages.itemSelectionChanged.connect(self.showPackage)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Package configuration"))

    def invalitatePages(self):
        self.tabs.clear()
        self. pages = {}

    def showPackage(self):
        """Create or reload package info page(s) in tab(s)."""
        package = self.packageList.selectedPackage()
        if package is not None:
            name = package.name
            # Cached new page
            new_page = self.pages.get(name, False)
            if not new_page:
                new_page = self.pages[name] = PackageInfoPage(package)

            self.tabs.clear()
            self.tabs.addTab(new_page, package.icon, package.displayName)
            #TODO: if applicable add configuration page(s), if defined in the openlilylib module

