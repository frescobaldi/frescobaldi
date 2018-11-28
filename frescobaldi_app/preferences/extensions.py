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
Extensions preferences.
"""


import re

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel

from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFontComboBox,
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
    QTreeView, QVBoxLayout, QWidget
)

import app
import userguide
import qutil
import preferences
import popplerview
import widgets.dialog
import widgets.listedit
import documentstructure
from widgets import urlrequester


class Extensions(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(Extensions, self).__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(General(self))
        layout.addWidget(Installed(self))
        layout.addStretch(1)


class General(preferences.Group):
    def __init__(self, page):
        super(General, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.active = QCheckBox(toggled=self.changed)
        layout.addWidget(self.active)

        self.root = urlrequester.UrlRequester()
        self.root.changed.connect(self.root_changed)
        layout.addWidget(self.root)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("General Settings"))
        self.active.setText(_("Use Extensions"))
        self.active.setToolTip(_("If unchecked don't look for extensions."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("extensions/general")
        self.active.setChecked(s.value("active", True, bool))
        self.root.setPath(s.value("root", '', str))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("extensions/general")
        s.setValue("active", self.active.isChecked())
        s.setValue("root", self.root.path())

    def root_changed(self):
        self.changed.emit()


class Installed(preferences.Group):
    """Overview of installed extensions.

    At some later point the entries in the tree view will
    show more information about the extensions (provided metadata),
    and there should be widgets (a checkbox?) to de/activate individual
    extensions.
    When the currently selected extension provides a configuration widget
    this will be shown in the third Group element (to-be-done).
    """
    def __init__(self, page):
        super(Installed, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tree = QTreeView()
        self.tree.setModel(QStandardItemModel())
        # We don't completely remove the headers because they will
        # be used later.
        self.tree.model().setHorizontalHeaderLabels([''])
        self.populate()
        layout.addWidget(self.tree)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Installed Extensions"))

    def loadSettings(self):
        s = QSettings()
        self.setEnabled(s.value('extensions/general/active', True, bool))
        s.beginGroup("extensions/installed")
        # to be continued

    def populate(self):
        """Populate the tree view with data from the installed extensions.
        """
        # For now we'll create a flat list but there will be child items
        # with further metadata and configuration interface later.
        root = self.tree.model().invisibleRootItem()
        for ext in app.extensions().extensions():
            item = QStandardItem(ext.display_name())
            if ext.has_icon():
                item.setIcon(ext.icon())
            root.appendRow(item)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("extensions/installed")
        # to be continued
