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


from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

import app
import preferences
import qsettings
import widgets.listedit
import widgets.urlrequester


class Paths(preferences.GroupsPage):
    def __init__(self, dialog):
        super().__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(HyphenPaths(self))
        layout.addWidget(MusicFonts(self))
        layout.addStretch(1)


class HyphenPaths(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

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


class MusicFonts(preferences.Group):
    """Preferences regarding the handling of music/notation fonts."""

    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        font_repo_layout = QHBoxLayout()
        self.font_repo_label = QLabel()
        font_repo_layout.addWidget(self.font_repo_label)
        self.font_repo_cb = QCheckBox()
        self.font_repo_cb.toggled.connect(self.changed)
        font_repo_layout.addWidget(self.font_repo_cb)
        font_repo_layout.addStretch()
        layout.addLayout(font_repo_layout)

        self.font_repo_path_requester = widgets.urlrequester.UrlRequester()
        self.font_repo_path_requester.changed.connect(self.changed)
        layout.addWidget(self.font_repo_path_requester)

        self.font_cache_label = QLabel()
        layout.addWidget(self.font_cache_label)

        self.font_cache_path_requester = widgets.urlrequester.UrlRequester()
        self.font_cache_path_requester.changed.connect(self.changed)
        layout.addWidget(self.font_cache_path_requester)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Music Fonts"))
        self.font_repo_label.setText(_("Music Font Repository:"))
        repo_tt = _(
            "If set this directory can be used to automatically\n"
            + "install all music fonts into a given LilyPond installation."
        )
        self.font_repo_label.setToolTip(repo_tt)
        self.font_repo_path_requester.setToolTip(repo_tt)
        self.font_repo_cb.setText(_("Auto install"))
        self.font_repo_cb.setToolTip(_(
            "Always install fonts from the music font repository\n"
            "to the current LilyPond installation when opening\n"
            "the Document Fonts dialog."
        ))
        self.font_cache_label.setText(_("Music Font Preview Cache:"))
        cache_tt = _(
            "If a writable path is set the provided notation font samples\n"
            + "are cached persistently, otherwise they are cached in the\n"
            + "operating system's temporary directory where they may be\n"
            + "removed upon shutdown.\n"
            + "Notation font previews from custom files or the active\n"
            + "document are always cached temporarily and removed when\n"
            + "closing Frescobaldi."
        )
        self.font_cache_label.setToolTip(cache_tt)
        self.font_cache_path_requester.setToolTip(cache_tt)

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("music-fonts")
        self.font_cache_path_requester.setPath(s.value("font-cache", '', str))
        self.font_repo_path_requester.setPath(s.value("font-repo", '', str))
        self.font_repo_cb.setChecked(s.value("auto-install", True, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("music-fonts")
        font_cache = self.font_cache_path_requester.path()
        if font_cache:
            s.setValue("font-cache", font_cache)
        else:
            s.remove("font-cache")
        font_repo = self.font_repo_path_requester.path()
        print(font_repo)
        if font_repo:
            s.setValue("font-repo", font_repo)
        else:
            s.remove("font-repo")
        s.setValue("auto-install", self.font_repo_cb.isChecked())
