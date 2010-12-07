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
Loading and defaults for the different textformats used for Syntax Highlighting.
"""

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QColor, QFont, QPalette, QTextCharFormat, QTextFormat

import app


# When textFormatData() is requested for the first time, it is loaded from the config
# When the settings are changed, it is cleared again so that it is reloaded when
# requested again.

_currentData = None

def textFormatData():
    global _currentData
    if _currentData is None:
        _currentData = TextFormatData(QSettings().value('editor_scheme', 'default'))
    return _currentData

def _resetTextFormatData():
    global _currentData
    _currentData = None

app.settingsChanged.connect(_resetTextFormatData, -100) # before all others
    
    
class TextFormatData(object):
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
        for name in defaultStyles:
            self.defaultStyles[name] = d = QTextCharFormat(defaultStyleDefaults[name])
            s.beginGroup(name)
            loadTextFormat(d, s)
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
        for name in defaultStyles:
            s.beginGroup(name)
            saveTextFormat(self.defaultStyles[name], s)
            s.endGroup()
        s.endGroup()
        


def saveTextFormat(fmt, settings):
    if fmt.hasProperty(QTextFormat.FontWeight):
        settings.setValue('bold', fmt.fontWeight() >= 70)
    else:
        settings.remove('bold')
    if fmt.hasProperty(QTextFormat.FontItalic):
        settings.setValue('italic', fmt.fontItalic())
    else:
        settings.remove('italic')
    if fmt.hasProperty(QTextFormat.TextUnderlineStyle):
        settings.setValue('underline', fmt.fontUnderline())
    else:
        settings.remove('underline')
    if fmt.hasProperty(QTextFormat.ForegroundBrush):
        settings.setValue('textColor', fmt.foreground().color().name())
    else:
        settings.remove('textColor')
    if fmt.hasProperty(QTextFormat.BackgroundBrush):
        settings.setValue('backgroundColor', fmt.background().color().name())
    else:
        settings.remove('backgroundColor')
    if fmt.hasProperty(QTextFormat.TextUnderlineColor):
        settings.setValue('underlineColor', fmt.underlineColor().name())
    else:
        settings.remove('underlineColor')
    
def loadTextFormat(fmt, settings):
    if settings.contains('bold'):
        fmt.setFontWeight(QFont.Bold if settings.value('bold') in (True, 'true') else QFont.Normal)
    if settings.contains('italic'):
        fmt.setFontItalic(settings.value('italic') in (True, 'true'))
    if settings.contains('underline'):
        fmt.setFontUnderline(settings.value('underline') in (True, 'true'))
    if settings.contains('textColor'):
        fmt.setForeground(QColor(settings.value('textColor')))
    if settings.contains('backgroundColor'):
        fmt.setBackground(QColor(settings.value('backgroundColor')))
    if settings.contains('underlineColor'):
        fmt.setUnderlineColor(QColor(settings.value('underlineColor')))



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


def _defaultStyleDefaults():
    keyword = QTextCharFormat()
    keyword.setFontWeight(QFont.Bold)
    
    function = QTextCharFormat(keyword)
    function.setForeground(QColor(128, 0, 128))
    
    variable = QTextCharFormat()
    variable.setForeground(QColor(128, 0, 128))
    
    value = QTextCharFormat()
    value.setForeground(QColor(128, 128, 0))
    
    string = QTextCharFormat()
    string.setForeground(QColor(192, 0, 0))
    
    escape = QTextCharFormat()
    escape.setFontWeight(QFont.Bold)
    escape.setForeground(QColor(0, 192, 192))
    
    comment = QTextCharFormat()
    comment.setForeground(QColor(128, 128, 128))
    comment.setFontItalic(True)
    
    error = QTextCharFormat()
    error.setForeground(QColor(255, 0, 0))
    error.setFontUnderline(True)
    
    return locals()
    
defaultStyleDefaults = _defaultStyleDefaults()
del _defaultStyleDefaults


allStyles = (
    ('lilypond', (
        'pitch',
        'duration',
        'slur',
        'dynamic',
        'articulation',
        'chord',
        'beam',
        'check',
        'repeat',
        'keyword',
        'command',
        'usercommand',
        'context',
        'grob',
        'property',
        'string',
        'comment',
        )),
    ('html', (
        'tag',
        'lilypondtag',
        'attribute',
        'value',
        'entityref',
        'string',
        'comment',
        )),
)


inherits = {
    'lilypond': {
        'keyword': 'keyword',
        'string': 'string',
        'comment': 'comment',
    },
    'html' : {
        'tag': 'keyword',
        'lilypondtag': 'keyword',
        'attribute': 'variable',
        'value': 'value',
        'entityref': 'escape',
        'string': 'string',
        'comment': 'comment',
    },
}


        
    