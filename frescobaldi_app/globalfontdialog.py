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

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
        self.staffSizeLabel = QLabel()
        self.staffSizeChooser = QSpinBox(minimum=1, maximum=200, value=20)
        
        layout.addWidget(self.romanLabel, 0, 0)
        layout.addWidget(self.romanCombo, 0, 1, 1, 2)
        layout.addWidget(self.sansLabel, 1, 0)
        layout.addWidget(self.sansCombo, 1, 1, 1, 2)
        layout.addWidget(self.typewriterLabel, 2, 0)
        layout.addWidget(self.typewriterCombo, 2, 1, 1, 2)
        layout.addWidget(self.staffSizeLabel, 3, 0)
        layout.addWidget(self.staffSizeChooser, 3, 1)
        
        self.loadSettings()
        self.finished.connect(self.saveSettings)
        app.translateUI(self)
        qutil.saveDialogSize(self, "global_font_dialog/dialog/size")
        
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Global Fonts")))
        self.setMessage(_(
            "Please select the three global fonts to use for "
            r"<code>\roman</code>, <code>\sans</code>, and <code>\typewriter</code> "
            "respectively. "
            "You should also set the staff size to the global staff size you "
            "use in the document (20 by default)."))
        self.romanLabel.setText(_("Roman Font:"))
        self.sansLabel.setText(_("Sans Font:"))
        self.typewriterLabel.setText(_("Typewriter Font:"))
        self.staffSizeLabel.setText(_("Staff Size:"))
    
    def staffSize(self):
        return self.staffSizeChooser.value()
    
    def setStaffSize(self, value):
        self.staffSizeChooser.setValue(value)
    
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
        roman = s.value("roman", "Century Schoolbook L", type(""))
        self.romanCombo.setCurrentFont(QFont(roman))
        sans = s.value("sans", "sans-serif", type(""))
        self.sansCombo.setCurrentFont(QFont(sans))
        typewriter = s.value("typewriter", "monospace", type(""))
        self.typewriterCombo.setCurrentFont(QFont(typewriter))
    
    def saveSettings(self):
        s = QSettings()
        s.beginGroup("global_font_dialog")
        s.setValue("roman", self.romanCombo.currentFont().family())
        s.setValue("sans", self.sansCombo.currentFont().family())
        s.setValue("typewriter", self.typewriterCombo.currentFont().family())


