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
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDoubleSpinBox, QFontComboBox,
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget)

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
        # TODO: This is not respected yet.
        self.active.setEnabled(False)

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
