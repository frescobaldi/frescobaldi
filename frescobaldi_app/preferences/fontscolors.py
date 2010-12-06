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
        self.tree.setAnimated(True)
        self.stack = QStackedWidget(self)
        hbox.addWidget(self.tree)
        hbox.addWidget(self.stack)
        layout.addLayout(hbox)
        
        self.fontButton = QPushButton(_("Change Font..."))
        layout.addWidget(self.fontButton)
        
        # add the items to our list
        self.baseColorsItem = i = QTreeWidgetItem()
        self.tree.addTopLevelItem(i)
        self.defaultStylesItem = i = QTreeWidgetItem()
        self.tree.addTopLevelItem(i)
        
        self.defaultStyles = {}
        for name in defaultStyles:
            self.defaultStyles[name] = i = QTreeWidgetItem()
            self.defaultStylesItem.addChild(i)
            i.name = name
        self.defaultStylesItem.setExpanded(True)
        
        self.allStyles = {}
        for group, title, styles in allStyles():
            i = QTreeWidgetItem()
            children = {}
            self.allStyles[group] = (i, children)
            self.tree.addTopLevelItem(i)
            i.group = group
            for name, title in styles:
                j = QTreeWidgetItem()
                j.name = name
                i.addChild(j)
                children[name] = j
        
        self.baseColorsWidget = BaseColors(self)
        self.customAttributesWidget = CustomAttributes(self)
        self.emptyWidget = QWidget(self)
        self.stack.addWidget(self.baseColorsWidget)
        self.stack.addWidget(self.customAttributesWidget)
        self.stack.addWidget(self.emptyWidget)
        
        self.tree.currentItemChanged.connect(self.currentItemChanged)
        self.tree.setCurrentItem(self.baseColorsItem)
        self.scheme.currentChanged.connect(self.currentSchemeChanged)
        self.scheme.changed.connect(self.changed)
        self.baseColorsWidget.changed.connect(self.baseColorsChanged)
        self.customAttributesWidget.changed.connect(self.customAttributesChanged)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.baseColorsItem.setText(0, _("Base Colors"))
        self.defaultStylesItem.setText(0, _("Default Styles"))
        for name in defaultStyles:
            self.defaultStyles[name].setText(0, defaultStyleNames[name]())
        for group, title, styles in allStyles():
            self.allStyles[group][0].setText(0, title)
            for name, title in styles:
                self.allStyles[group][1][name].setText(0, title)
            
    def currentItemChanged(self, item, previous):
        if item is self.baseColorsItem:
            self.stack.setCurrentWidget(self.baseColorsWidget)
        elif not item.parent():
            self.stack.setCurrentWidget(self.emptyWidget)
        else:
            data = self.data[self.scheme.currentScheme()]
            w = self.customAttributesWidget
            self.stack.setCurrentWidget(w)
            if item.parent() is self.defaultStylesItem:
                # default style
                w.setTitle(item.text(0))
                w.setStyleData(data.defaultStyles[item.name])
            else:
                # specific style of specific group
                w.setTitle("{0}: {1}".format(item.parent().text(0), item.text(0)))
                
    def currentSchemeChanged(self):
        scheme = self.scheme.currentScheme()
        if scheme not in self.data:
            self.data[scheme] = Data(scheme)
        self.updateDisplay()
        
    def updateDisplay(self):
        data = self.data[self.scheme.currentScheme()]
        # update base colors
        for name in baseColors:
            self.baseColorsWidget.color[name].setColor(data.baseColors[name])
        # update base colors for whole treewidget
        p = QApplication.palette()
        p.setColor(QPalette.Base, data.baseColors['background'])
        p.setColor(QPalette.Text, data.baseColors['text'])
        p.setColor(QPalette.Highlight, data.baseColors['selectionbackground'])
        p.setColor(QPalette.HighlightedText, data.baseColors['selectiontext'])
        self.tree.setPalette(p)
        
        baseFont = self.tree.font() # TEMP
        
        # update looks of default styles
        for name in defaultStyles:
            item = self.defaultStyles[name]
            d = data.defaultStyles[name]
            font = QFont(baseFont)
            if d.textColor.isValid():
                item.setForeground(0, d.textColor)
            else:
                item.setForeground(0, data.baseColors['text'])
            if d.backgroundColor.isValid():
                item.setBackground(0, d.backgroundColor)
            else:
                item.setBackground(0, QBrush())
            font.setWeight(QFont.Bold if d.bold else QFont.Normal)
            font.setItalic(d.italic or False)
            font.setUnderline(d.underline or False)
            item.setFont(0, font)
        
    def baseColorsChanged(self, name):
        # keep data up to date with base colors
        data = self.data[self.scheme.currentScheme()]
        data.baseColors[name] = self.baseColorsWidget.color[name].color()
        self.updateDisplay()
        self.changed()
    
    def customAttributesChanged(self):
        item = self.tree.currentItem()
        if not item or not item.parent():
            return
        data = self.data[self.scheme.currentScheme()]
        if item.parent() is self.defaultStylesItem:
            # a default style has been changed
            data.defaultStyles[item.name] = self.customAttributesWidget.styleData()
        else:
            pass # a custum style has been changed
        self.updateDisplay()
        
    def loadSettings(self):
        self.data = {} # holds all data with scheme as key
        self.scheme.loadSettings("editor_scheme", "editor_schemes")
        
    def saveSettings(self):
        self.scheme.saveSettings("editor_scheme", "editor_schemes", "fontscolors")
        for scheme in self.data:
            self.data[scheme].save(scheme)


class BaseColors(QGroupBox):
    
    changed = pyqtSignal(unicode)
    
    def __init__(self, parent=None):
        super(BaseColors, self).__init__(parent)
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.color = {}
        self.labels = {}
        for name in baseColors:
            c = self.color[name] = ColorButton(self)
            c.colorChanged.connect((lambda name: lambda: self.changed.emit(name))(name))
            l = self.labels[name] = QLabel()
            l.setBuddy(c)
            row = grid.rowCount()
            grid.addWidget(l, row, 0)
            grid.addWidget(c, row, 1)
        
        grid.setRowStretch(grid.rowCount(), 2)
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("Base Colors"))
        for name in baseColors:
            self.labels[name].setText(baseColorNames[name]())
        

class CustomAttributes(QGroupBox):
    
    changed = pyqtSignal()
    
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
        grid.setRowStretch(6, 2)
        
        self.textColor.colorChanged.connect(self.changed)
        self.backgroundColor.colorChanged.connect(self.changed)
        self.underlineColor.colorChanged.connect(self.changed)
        self.bold.stateChanged.connect(self.changed)
        self.italic.stateChanged.connect(self.changed)
        self.underline.stateChanged.connect(self.changed)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.textLabel.setText(_("Text"))
        self.backgroundLabel.setText(_("Background"))
        self.bold.setText(_("Bold"))
        self.italic.setText(_("Italic"))
        self.underline.setText(_("Underline"))
        
    def styleData(self):
        """Returns our settings as a StyleData object."""
        d = StyleData()
        fnt = [False, None, True]
        d.bold = fnt[self.bold.checkState()]
        d.italic = fnt[self.italic.checkState()]
        d.underline = fnt[self.underline.checkState()]
        d.textColor = self.textColor.color()
        d.backgroundColor = self.backgroundColor.color()
        d.underlineColor = self.underlineColor.color()
        return d
        
    def setStyleData(self, d):
        """Sets our widget to the StyleData settings."""
        state = lambda value: {False: 0, True: 2}.get(value, 1)
        block = self.blockSignals(True)
        self.bold.setCheckState(state(d.bold))
        self.italic.setCheckState(state(d.italic))
        self.underline.setCheckState(state(d.underline))
        self.textColor.setColor(d.textColor)
        self.backgroundColor.setColor(d.backgroundColor)
        self.underlineColor.setColor(d.underlineColor)
        self.blockSignals(block)
        

class Data(object):
    """Encapsulates all settings in the Fonts & Colors page for a scheme."""
    def __init__(self, scheme):
        """Loads the data from scheme."""
        self.baseColors = {}
        self.defaultStyles = {}
        self.load(scheme)
        
    def load(self, scheme):
        s = QSettings()
        s.beginGroup("fontscolors/" + scheme)
        
        # load base colors
        s.beginGroup("basecolors")
        for name in baseColors:
            if s.contains(name):
                self.baseColors[name] = QColor(s.value(name))
            else:
                self.baseColors[name] = baseColorDefaults[name]()
        s.endGroup()
        # load default styles
        s.beginGroup("defaultstyles")
        for name in defaultStyleNames:
            self.defaultStyles[name] = d = StyleData(defaultStyleDefaults[name])
            s.beginGroup(name)
            d.load(s)
            s.endGroup()
        s.endGroup()
        
    def save(self, scheme):
        s = QSettings()
        s.beginGroup("fontscolors/" + scheme)
        
        # save base colors
        for name in baseColors:
            s.setValue("basecolors/"+name, self.baseColors[name].name())
        # save default styles
        s.beginGroup("defaultstyles")
        for name in defaultStyleNames:
            s.beginGroup(name)
            self.defaultStyles[name].save(s)
            s.endGroup()
        s.endGroup()
        

# We could use QTextCharFormat to store this kind of data,
# but saving it does not work reliably in PyQt4 due to embedded
# wrapped objects (QBrush etc).
class StyleData(object):
    """Encapsulates one highlight style."""
    def __init__(self, other=None, **kwargs):
        if other:
            self.bold = other.bold
            self.italic = other.italic
            self.underline = other.underline
            self.textColor = other.textColor
            self.backgroundColor = other.backgroundColor
            self.underlineColor = other.underlineColor
        elif kwargs:
            for name in styleProperties:
                setattr(self, name, kwargs.get(name))
        else:
            self.bold = None
            self.italic = None
            self.underline = None
            self.textColor = QColor()
            self.backgroundColor = QColor()
            self.underlineColor = QColor()
            
    def save(self, group):
        if self.bold is None:
            group.remove('bold')
        else:
            group.setValue('bold', self.bold)
        if self.italic is None:
            group.remove('italic')
        else:
            group.setValue('italic', self.italic)
        if self.underline is None:
            group.remove('underline')
        else:
            group.setValue('underline', self.underline)
        if self.textColor.isValid():
            group.setValue('textColor', self.textColor.name())
        else:
            group.remove('textColor')
        if self.backgroundColor.isValid():
            group.setValue('backgroundColor', self.backgroundColor.name())
        else:
            group.remove('backgroundColor')
        if self.underlineColor.isValid():
            group.setValue('underlineColor', self.underlineColor.name())
        else:
            group.remove('underlineColor')
        
    def load(self, group):
        if group.contains('bold'):
            self.bold = group.value('bold') in (True, 'true')
        if group.contains('italic'):
            self.italic = group.value('italic') in (True, 'true')
        if group.contains('underline'):
            self.underline = group.value('underline') in (True, 'true')
        if group.contains('textColor'):
            self.textColor = QColor(group.value('textColor'))
        if group.contains('backgroundColor'):
            self.backgroundColor = QColor(group.value('backgroundColor'))
        if group.contains('underlineColor'):
            self.underlineColor = QColor(group.value('underlineColor'))
        

baseColors = (
    'text',
    'background',
    'selectiontext',
    'selectionbackground',
    'current',
    'mark',
    'error',
    'search',
)

baseColorNames = dict(
    text =                lambda: _("Text"),
    background =          lambda: _("Background"),
    selectiontext =       lambda: _("Selected Text"),
    selectionbackground = lambda: _("Selection Background"),
    current =             lambda: _("Current Line"),
    mark =                lambda: _("Marked Line"),
    error =               lambda: _("Error Line"),
    search =              lambda: _("Search Result"),
)

baseColorDefaults = dict(
    text =                lambda: QApplication.palette().color(QPalette.Text),
    background =          lambda: QApplication.palette().color(QPalette.Base),
    selectiontext =       lambda: QApplication.palette().color(QPalette.HighlightedText),
    selectionbackground = lambda: QApplication.palette().color(QPalette.Highlight),
    current =             lambda: QColor(255, 252, 149),
    mark =                lambda: QColor(192, 192, 255),
    error =               lambda: QColor(255, 192, 192),
    search =              lambda: QColor(192, 255, 192),
)

styleProperties = (
    'textColor',
    'backgroundColor',
    'underlineColor',
    'bold',
    'italic',
    'underline',
)

defaultStyles = (
    'keyword',
    'function',
    'variable',
    'value',
    'string',
    'escape',
    'comment',
    'error',
)

defaultStyleNames = dict(
    keyword =   lambda: _("Keyword"),
    function =  lambda: _("Function"),
    variable =  lambda: _("Variable"),
    value =     lambda: _("Value"),
    string =    lambda: _("String"),
    escape =    lambda: _("Escape"), # TODO: better translatable name
    comment =   lambda: _("Comment"),
    error =     lambda: _("Error"),
)


def _defaultStyleDefaults():
    keyword = StyleData()
    keyword.bold = True
    
    function = StyleData(keyword)
    function.textColor = QColor(128, 0, 128)
    
    variable = StyleData()
    variable.textColor = QColor(128, 0, 128)
    
    value = StyleData()
    value.textColor = QColor(128, 128, 0)
    
    string = StyleData()
    string.textColor = QColor(192, 0, 0)
    
    escape = StyleData()
    escape.bold = True
    escape.textColor = QColor(0, 192, 192)
    
    comment = StyleData()
    comment.textColor = QColor(128, 128, 128)
    comment.italic = True
    
    error = StyleData()
    error.textColor = QColor(255, 0, 0)
    error.underline = True
    
    return locals()
    
defaultStyleDefaults = _defaultStyleDefaults()
del _defaultStyleDefaults


def allStyles():
    return (
        ('lilypond', _("LilyPond"), (
            ('pitch', _("Pitch")),
            ('duration', _("Duration")),
            ('slur', _("Slur")),
            ('dynamic', _("Dynamic")),
            ('articulation', _("Articulation")),
            ('chord', _("Chord")),
            ('beam', _("Beam")),
            ('check', _("Check")),
            ('repeat', _("Repeat")),
            ('keyword', _("Keyword")),
            ('command', _("Command")),
            ('usercommand', _("User Command")),
            ('context', _("Context")),
            ('grob', _("Layout Object")),
            ('property', _("Property")),
        )),
    )


            
