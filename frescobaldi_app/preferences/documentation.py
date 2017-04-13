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
Documentation preferences.
"""


from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (QComboBox, QCompleter, QFontComboBox,
    QGridLayout, QLabel, QSpinBox, QVBoxLayout)

import app
import qutil
import icons
import preferences
import widgets.listedit
import widgets.dialog
import lilydoc
import userguide
import language_names
import qsettings


class Documentation(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Documentation, self).__init__(dialog)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(Paths(self))
        layout.addWidget(Browser(self))
        layout.addStretch(1)


class Paths(preferences.Group):
    def __init__(self, page):
        super(Paths, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.paths = LilyDocPathsList()
        self.paths.changed.connect(self.changed)
        layout.addWidget(self.paths)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Paths to LilyPond Documentation"))
        self.paths.setToolTip(_(
            "Add paths or URLs. See \"What's This\" for more information."))
        self.paths.setWhatsThis(userguide.html("prefs_lilydoc"))

    def loadSettings(self):
        paths = qsettings.get_string_list(QSettings(), "documentation/paths")
        self.paths.setValue(paths)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("documentation")
        paths = self.paths.value()
        if paths:
            s.setValue("paths", paths)
        else:
            s.remove("paths")


class Browser(preferences.Group):
    def __init__(self, page):
        super(Browser, self).__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.languagesLabel = QLabel()
        self.languages = QComboBox(currentIndexChanged=self.changed)
        layout.addWidget(self.languagesLabel, 0, 0)
        layout.addWidget(self.languages, 0, 1)

        items = ['', '']
        items.extend(language_names.languageName(l, l) for l in lilydoc.translations)
        self.languages.addItems(items)

        self.fontLabel = QLabel()
        self.fontChooser = QFontComboBox(currentFontChanged=self.changed)
        self.fontSize = QSpinBox(valueChanged=self.changed)
        self.fontSize.setRange(6, 32)
        self.fontSize.setSingleStep(1)

        layout.addWidget(self.fontLabel, 1, 0)
        layout.addWidget(self.fontChooser, 1, 1)
        layout.addWidget(self.fontSize, 1, 2)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Documentation Browser"))
        self.languagesLabel.setText(_("Preferred Language:"))
        self.languages.setItemText(0, _("Default"))
        self.languages.setItemText(1, _("English (untranslated)"))
        self.fontLabel.setText(_("Font:"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("documentation")
        lang = s.value("language", "default", str)
        if lang in lilydoc.translations:
            i = lilydoc.translations.index(lang) + 2
        elif lang == "C":
            i = 1
        else:
            i = 0
        self.languages.setCurrentIndex(i)

        font = self.font()
        family = s.value("fontfamily", "", str)
        if family:
            font.setFamily(family)
        size = s.value("fontsize", 16, int)
        with qutil.signalsBlocked(self.fontChooser, self.fontSize):
            self.fontChooser.setCurrentFont(font)
            self.fontSize.setValue(size)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("documentation")
        langs = ['default', 'C'] + lilydoc.translations
        s.setValue("language", langs[self.languages.currentIndex()])
        s.setValue("fontfamily", self.fontChooser.currentFont().family())
        s.setValue("fontsize", self.fontSize.value())


class LilyDocPathsList(widgets.listedit.ListEdit):
    def openEditor(self, item):

        dlg = widgets.dialog.Dialog(self,
            _("Please enter a local path or a URL:"),
            app.caption("LilyPond Documentation"),
            icon = icons.get('lilypond-run'))
        urlreq = widgets.urlrequester.UrlRequester()
        urlreq.lineEdit.setCompleter(QCompleter([
            "http://lilypond.org/doc/v2.12/",
            "http://lilypond.org/doc/stable/",
            "http://lilypond.org/doc/latest/",
            ], urlreq.lineEdit))
        dlg.setMainWidget(urlreq)
        urlreq.setPath(item.text())
        urlreq.setMinimumWidth(320)
        urlreq.lineEdit.setFocus()
        if dlg.exec_():
            item.setText(urlreq.path())
            return True
        return False


