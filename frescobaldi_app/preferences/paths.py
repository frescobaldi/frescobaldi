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
Paths preferences page
"""


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QVBoxLayout, QLabel

import app
import preferences
import qsettings
import widgets.listedit
import widgets.urlrequester


class Paths(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Paths, self).__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(HyphenPaths(self))
        layout.addWidget(Caching(self))
        layout.addStretch(1)


class HyphenPaths(preferences.Group):
    def __init__(self, page):
        super(HyphenPaths, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.listedit = widgets.listedit.FilePathEdit()
        self.listedit.changed.connect(self.changed)
        layout.addWidget(self.listedit)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Folders containing hyphenation dictionaries"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("hyphenation")
        paths = qsettings.get_string_list(s, "paths")
        self.listedit.setValue(paths)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("hyphenation")
        paths = self.listedit.value()
        if paths:
            s.setValue("paths", paths)
        else:
            s.remove("paths")


class Caching(preferences.Group):
    # TODO: There will be further options for caching multiple versions of a doc
    def __init__(self, page):
        super(Caching, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.caching_label = QLabel()
        layout.addWidget(self.caching_label)
        layout.addWidget(QLabel(""))
        self.font_preview_label = QLabel()
        layout.addWidget(self.font_preview_label)
        self.font_preview_path_requester = widgets.urlrequester.UrlRequester()
        self.font_preview_path_requester.changed.connect(self.changed)
        layout.addWidget(self.font_preview_path_requester)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Caching"))
        self.caching_label.setText(_(
            "If paths are set in these preferences the corresponding "
            + "parts of Frescobaldi use (persistent) caching."
        ))
        self.font_preview_label.setText(_("Notation Font Previews:"))
        self.font_preview_label.setToolTip(_(
            "If set renderings of the provided notation font samples\n"
            + "are cached persistently, otherwise they are cached in the\n"
            + "operating system's temporary directory where they may be\n"
            + "removed upon shutdown.\n"
            + "Notation font previews from custom files or the active\n"
            + "document are always cached temporarily and removed when\n"
            + "closing Frescobaldi."
        ))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("caching")
        font_preview = s.value("font-preview", '', str)
        self.font_preview_path_requester.setPath(font_preview)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("caching")
        font_preview = self.font_preview_path_requester.path()
        if font_preview:
            s.setValue("font-preview", font_preview)
        else:
            s.remove("font-preview")
