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
Global Font Dialog, used to set the three fonts for the make-pango-font-tree
command.

It keeps its settings.
"""


from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFontComboBox, QGridLayout, QLabel

import app
import qutil
import widgets.dialog

class GlobalFontDialog(widgets.dialog.Dialog):
    def __init__(self, parent=None):
        super(GlobalFontDialog, self).__init__(parent)
        self._messageLabel.setWordWrap(True)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.mainWidget().setLayout(layout)

        self.romanLabel = QLabel()
        self.romanCombo = QFontComboBox()
        self.sansLabel = QLabel()
        self.sansCombo = QFontComboBox()
        self.typewriterLabel = QLabel()
        self.typewriterCombo = QFontComboBox(fontFilters=QFontComboBox.MonospacedFonts)

        layout.addWidget(self.romanLabel, 0, 0)
        layout.addWidget(self.romanCombo, 0, 1, 1, 2)
        layout.addWidget(self.sansLabel, 1, 0)
        layout.addWidget(self.sansCombo, 1, 1, 1, 2)
        layout.addWidget(self.typewriterLabel, 2, 0)
        layout.addWidget(self.typewriterCombo, 2, 1, 1, 2)

        self.loadSettings()
        self.finished.connect(self.saveSettings)
        app.translateUI(self)

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Global Fonts")))
        self.setMessage(_(
            "Please select the three global fonts to use for "
            r"<code>\roman</code>, <code>\sans</code>, and <code>\typewriter</code> "
            "respectively."))
        self.romanLabel.setText(_("Roman Font:"))
        self.sansLabel.setText(_("Sans Font:"))
        self.typewriterLabel.setText(_("Typewriter Font:"))

    def romanFont(self):
        return self.romanCombo.currentFont().family()

    def setromanFont(self, family):
        self.romanCombo.setCurrentFont(QFont(family))

    def sansFont(self):
        return self.sansCombo.currentFont().family()

    def setSansFont(self, family):
        self.sansCombo.setCurrentFont(QFont(family))

    def typewriterFont(self):
        return self.typewriterCombo.currentFont().family()

    def settypewriterFont(self, family):
        self.typewriterCombo.setCurrentFont(QFont(family))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("global_font_dialog")
        roman = s.value("roman", "Century Schoolbook L", str)
        self.romanCombo.setCurrentFont(QFont(roman))
        sans = s.value("sans", "sans-serif", str)
        self.sansCombo.setCurrentFont(QFont(sans))
        typewriter = s.value("typewriter", "monospace", str)
        self.typewriterCombo.setCurrentFont(QFont(typewriter))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("global_font_dialog")
        s.setValue("roman", self.romanCombo.currentFont().family())
        s.setValue("sans", self.sansCombo.currentFont().family())
        s.setValue("typewriter", self.typewriterCombo.currentFont().family())


