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
Helper application preferences.
"""


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QVBoxLayout,
    QWidget)

import app
import util
import qutil
import icons
import preferences
import widgets.urlrequester


class Helpers(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(Helpers, self).__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(Apps(self))


class Apps(preferences.Group):
    def __init__(self, page):
        super(Apps, self).__init__(page)

        layout = QGridLayout(spacing=1)
        self.setLayout(layout)

        self.messageLabel = QLabel(wordWrap=True)
        layout.addWidget(self.messageLabel, 0, 0, 1, 2)
        self.labels = {}
        self.entries = {}
        for row, (name, title) in enumerate(self.items(), 1):
            self.labels[name] = l = QLabel()
            self.entries[name] = e = widgets.urlrequester.UrlRequester()
            e.setFileMode(QFileDialog.ExistingFile)
            e.changed.connect(page.changed)
            layout.addWidget(l, row, 0)
            layout.addWidget(e, row, 1)

        app.translateUI(self)

    def items(self):
        """Yields (name, title) tuples for every setting in this group."""
        yield "pdf", _("PDF:")
        yield "midi", _("MIDI:")
        yield "svg", _("SVG:")
        yield "image", _("Image:")
        yield "browser", _("Browser:")
        yield "email", _("E-Mail:")
        yield "directory", _("File Manager:")
        yield "shell", _("Shell:")
        yield "git", _("Git:")

    def translateUI(self):
        self.setTitle(_("Helper Applications"))
        self.messageLabel.setText(_(
            "Below you can enter commands to open different file types. "
            "<code>$f</code> is replaced with the filename, "
            "<code>$u</code> with the URL. "
            "Leave a field empty to use the operating system default "
            "application."))
        for name, title in self.items():
            self.labels[name].setText(title)
        self.entries["email"].setToolTip(_(
            "Command that should accept a mailto: URL."))
        self.entries["shell"].setToolTip(_(
            "Command to open a Terminal or Command window."))
        self.entries["git"].setToolTip(_(
            "Command (base) to run Git versioning actions."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("helper_applications")
        for name, title in self.items():
            self.entries[name].setPath(s.value(name, "", str))

    def saveSettings(self):
        s= QSettings()
        s.beginGroup("helper_applications")
        for name, title in self.items():
            s.setValue(name, self.entries[name].path())


