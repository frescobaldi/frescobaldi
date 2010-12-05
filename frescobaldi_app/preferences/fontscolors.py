# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Fonts and Colors preferences page.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
    preferences,
)

from ..widgets import ClearButton
from ..widgets.schemeselector import SchemeSelector
from ..widgets.colorbutton import ColorButton


class FontsColors(preferences.Page):
    def __init__(self, dialog):
        super(FontsColors, self).__init__(dialog)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scheme = SchemeSelector(self)
        layout.addWidget(self.scheme)
        
        hbox = QHBoxLayout()
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAnimated(True)
        self.stack = QStackedWidget(self)
        hbox.addWidget(self.tree)
        hbox.addWidget(self.stack)
        layout.addLayout(hbox)
        
        self.fontButton = QPushButton(_("Change Font..."))
        layout.addWidget(self.fontButton)
    
    
    def loadSettings(self):
        self.scheme.loadSettings("editor_scheme", "editor_schemes")
        
    def saveSettings(self):
        self.scheme.saveSettings("editor_scheme", "editor_schemes", "fontscolor")
        

class BaseColors(QGroupBox):
    def __init__(self, parent=None):
        super(BaseColors, self).__init__(parent)
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.color = {}
        self.labels = {}
        for name in (
            'text',
            'background',
            'selectiontext',
            'selectionbackground',
            'current',
            'mark',
            'error',
            'search',
                ):
            c = self.color[name] = ColorButton(self)
            l = self.labels[name] = QLabel()
            l.setBuddy(c)
            row = grid.rowCount()
            grid.addWidget(l, row, 0)
            grid.addWidget(c, row, 1)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("Base Colors"))
        for name, title in (
            ('text', _("Text")),
            ('background', _("Background")),
            ('selectiontext', _("Selected Text")),
            ('selectionbackground', _("Selection Background")),
            ('current', _("Current Line")),
            ('mark', _("Marked Line")),
            ('error', _("Error Line")),
            ('search', _("Search Result")),
            ):
            self.labels[name].setText(title)


class CustomAttributes(QGroupBox):
    def __init__(self, parent=None):
        super(CustomAttributes, self).__init__(parent)
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.toplabel = QLabel()
        grid.addWidget(self.toplabel, 0, 0, 1, 3)
        
        self.textColor = ColorButton()
        l = self.textLabel = QLabel()
        l.setBuddy(self.textColor)
        grid.addWidget(l, 1, 0)
        grid.addWidget(self.textColor, 1, 1)
        c = ClearButton()
        c.clicked.connect(self.textColor.clear)
        grid.addWidget(c, 1, 2)
        
        self.backgroundColor = ColorButton()
        l = self.backgroundLabel = QLabel()
        l.setBuddy(self.backgroundColor)
        grid.addWidget(l, 2, 0)
        grid.addWidget(self.backgroundColor, 2, 1)
        c = ClearButton()
        c.clicked.connect(self.backgroundColor.clear)
        grid.addWidget(c, 2, 2)
        
        self.bold = QCheckBox()
        self.italic = QCheckBox()
        self.underline = QCheckBox()
        grid.addWidget(self.bold, 3, 0)
        grid.addWidget(self.italic, 4, 0)
        grid.addWidget(self.underline, 5, 0)
        
        self.underlineColor = ColorButton()
        grid.addWidget(self.underlineColor, 5, 1)
        c = ClearButton()
        c.clicked.connect(self.underlineColor.clear)
        grid.addWidget(c, 5, 2)
        
        
        app.translateUI(self)
        
    def translateUI(self):
        self.textLabel.setText(_("Text"))
        self.backgroundLabel.setText(_("Background"))
        self.bold.setText(_("Bold"))
        self.italic.setText(_("Italic"))
        self.underline.setText(_("Underline"))
        
        

def defaultStyles():
    return (
        ('keyword', _("Keyword")),
        ('function', _("Function")),
        ('variable', _("Variable")),
        ('value', _("Value")),
        ('string', _("String")),
        ('escape', _("Escape")), # TODO: better translatable name
        ('comment', _("Comment")),
        ('error', _("Error")),
    )

