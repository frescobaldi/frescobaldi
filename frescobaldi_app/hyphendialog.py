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
Dialog for selecting a hyphen language,
and code for finding hyphenation dictionaries to present the user a  choice.
"""


import glob
import locale
import os

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QVBoxLayout

import app
import qutil
import userguide
import language_names
import widgets
import hyphenator
import po.setup

# If the folder was completely removed by a distributor
try:
    import hyphdicts
except ImportError:
    hyphdicts = None


# paths to check for hyphen dicts
default_paths = [
    "share/hyphen",
    "share/myspell",
    "share/myspell/dicts",
    "share/dict/ooo",
    "share/apps/koffice/hyphdicts",
    "lib/scribus/dicts",
    "share/scribus/dicts",
    "share/scribus-ng/dicts",
    "share/hunspell",
]


def settings():
    """Returns the QSettings group for our settings."""
    settings = QSettings()
    settings.beginGroup("hyphenation")
    return settings

def directories():
    """ Yields a list of existing paths based on config """
    # prefixes to look in for relative paths
    prefixes = ['/usr/', '/usr/local/']

    def gen():
        # if the path is not absolute, add it to all prefixes.
        paths = settings().value("paths", default_paths, str)
        for path in paths:
            if os.path.isabs(path):
                yield path
            else:
                for pref in prefixes:
                    yield os.path.join(pref, path)
        if hyphdicts:
            yield hyphdicts.path
    return filter(os.path.isdir, gen())

def findDicts():
    """ Find installed hyphen dictionary files """

    # now find the hyph_xx_XX.dic files
    dicfiles = (f for p in directories()
                  for f in glob.glob(os.path.join(p, 'hyph_*.dic')) if os.access(f, os.R_OK))

    return dict((os.path.basename(dic)[5:-4], dic) for dic in dicfiles)


class HyphenDialog(QDialog):
    def __init__(self, mainwindow):
        super(HyphenDialog, self).__init__(mainwindow)
        self.setWindowModality(Qt.WindowModal)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.topLabel = QLabel()
        self.listWidget = QListWidget()

        layout.addWidget(self.topLabel)
        layout.addWidget(self.listWidget)
        layout.addWidget(widgets.Separator())

        self.buttons = b = QDialogButtonBox()
        layout.addWidget(b)
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        userguide.addButton(b, "lyrics")
        b.rejected.connect(self.reject)
        b.accepted.connect(self.accept)

        self.load()
        app.translateUI(self)
        qutil.saveDialogSize(self, "hyphenation/dialog/size")

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Hyphenate Lyrics Text")))
        self.topLabel.setText(_("Please select a language:"))

    def load(self):
        current = po.setup.current()
        self._langs = [(language_names.languageName(lang, current), lang, dic)
                       for lang, dic in findDicts().items()]
        self._langs.sort()
        for name, lang, dic in self._langs:
            self.listWidget.addItem("{0}  ({1})".format(name, lang))

        def select():
            lastused = settings().value("lastused", "", str)
            if lastused:
                yield lastused
            lang = po.setup.preferred()[0]
            yield lang
            yield lang.split('_')[0]

        langs = [item[1] for item in self._langs]
        for preselect in select():
            try:
                self.listWidget.setCurrentRow(langs.index(preselect))
                break
            except ValueError:
                continue

    def hyphenator(self):
        if self.exec_() and self._langs:
            lang, dic = self._langs[self.listWidget.currentRow()][1:]
            result = hyphenator.Hyphenator(dic)
            settings().setValue("lastused", lang)
        else:
            result = None
        self.deleteLater()
        return result


