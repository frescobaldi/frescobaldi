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
Loading and defaults for the different textformats used for Syntax Highlighting.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication, QColor, QFont, QPalette, QTextCharFormat, QTextFormat

import app
import ly.colorize


# When formatData() is requested for the first time, it is loaded from the config
# When the settings are changed, it is cleared again so that it is reloaded when
# requested again.


def formatData(format_type):
    """Return a TextFormatData instance of type 'editor' or 'printer'."""
    if _currentData[format_type] is None:
        _currentData[format_type] = TextFormatData(QSettings().value('{0}_scheme'.format(format_type), 'default', type("")))
    return _currentData[format_type]

def _resetFormatData():
    global _currentData
    _currentData = {
        'editor': None,
        'printer': None,
    }

app.settingsChanged.connect(_resetFormatData, -100) # before all others
_resetFormatData()

    
class TextFormatData(object):
    """Encapsulates all settings in the Fonts & Colors page for a scheme."""
    def __init__(self, scheme):
        """Loads the data from scheme."""
        self.font = None
        self.baseColors = {}
        self.defaultStyles = {}
        self.allStyles = {}
        self._inherits = {}
        self.load(scheme)
        
    def load(self, scheme):
        """Load the settings for the scheme. Called on init."""
        s = QSettings()
        s.beginGroup("fontscolors/" + scheme)
        
        # load font
        defaultfont = "Lucida Console" if os.name == "nt" else "monospace"
        self.font = QFont(s.value("fontfamily", defaultfont, type("")))
        self.font.setPointSizeF(s.value("fontsize", 10.0, float))
        
        # load base colors
        s.beginGroup("basecolors")
        for name in baseColors:
            if s.contains(name):
                self.baseColors[name] = QColor(s.value(name, "", type("")))
            else:
                self.baseColors[name] = baseColorDefaults[name]()
        s.endGroup()
        
        # get the list of supported styles from ly.colorize
        all_styles = ly.colorize.default_mapping()
        default_styles = set()
        for group, styles in all_styles:
            d = self._inherits[group] = {}
            for name, base, clss in styles:
                if base:
                    default_styles.add(base)
                    d[name] = base
        
        default_scheme = ly.colorize.default_scheme
        
        # load default styles
        s.beginGroup("defaultstyles")
        for name in default_styles:
            self.defaultStyles[name] = f = QTextCharFormat()
            css = default_scheme[None].get(name)
            if css:
                css2fmt(css, f)
            s.beginGroup(name)
            self.loadTextFormat(f, s)
            s.endGroup()
        s.endGroup()
        
        # load specific styles
        s.beginGroup("allstyles")
        for group, styles in all_styles:
            self.allStyles[group]= {}
            s.beginGroup(group)
            for name, inherits, clss in styles:
                self.allStyles[group][name] = f = QTextCharFormat()
                css = default_scheme[group].get(name)
                if css:
                    css2fmt(css, f)
                s.beginGroup(name)
                self.loadTextFormat(f, s)
                s.endGroup()
            s.endGroup()
        s.endGroup()
        
    def save(self, scheme):
        """Save the settings to the scheme."""
        s = QSettings()
        s.beginGroup("fontscolors/" + scheme)
        
        # save font
        s.setValue("fontfamily", self.font.family())
        s.setValue("fontsize", self.font.pointSizeF())
        
        # save base colors
        for name in baseColors:
            s.setValue("basecolors/"+name, self.baseColors[name].name())
        
        # save default styles
        s.beginGroup("defaultstyles")
        for name in defaultStyles:
            s.beginGroup(name)
            self.saveTextFormat(self.defaultStyles[name], s)
            s.endGroup()
        s.endGroup()
        
        # save all specific styles
        s.beginGroup("allstyles")
        for group, styles in allStyles:
            s.beginGroup(group)
            for name in styles:
                s.beginGroup(name)
                self.saveTextFormat(self.allStyles[group][name], s)
                s.endGroup()
            s.endGroup()
        s.endGroup()

    def textFormat(self, group, name):
        """Return a QTextCharFormat() for the specified group and name."""
        inherit = self._inherits[group].get(name)
        f = QTextCharFormat(self.defaultStyles[inherit]) if inherit else QTextCharFormat()
        f.merge(self.allStyles[group][name])
        return f
    
    def css_scheme(self):
        """Return a dictionary of css dictionaries representing this scheme.
        
        This can be fed to the ly.colorize.format_stylesheet() function.
        
        """
        scheme = {}
        # base/default styles
        d = scheme[None] = {}
        for name, fmt in self.defaultStyles.items():
            d[name] = fmt2css(fmt)
        # mode/group styles
        for mode, styles in self.allStyles.items():
            d = scheme[mode] = {}
            for name, fmt in styles.items():
                d[name] = fmt2css(fmt)
        return scheme
    
    def palette(self):
        """Return a basic palette with text, background, selection and selection background filled in."""
        p = QApplication.palette()
        p.setColor(QPalette.Text, self.baseColors['text'])
        p.setColor(QPalette.Base, self.baseColors['background'])
        p.setColor(QPalette.HighlightedText, self.baseColors['selectiontext'])
        p.setColor(QPalette.Highlight, self.baseColors['selectionbackground'])
        return p
        
    def saveTextFormat(self, fmt, settings):
        """(Internal) Store one QTextCharFormat in the QSettings instance."""
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
        
    def loadTextFormat(self, fmt, settings):
        """(Internal) Merge values from the QSettings instance into the QTextCharFormat."""
        if settings.contains('bold'):
            fmt.setFontWeight(QFont.Bold if settings.value('bold', False, bool) else QFont.Normal)
        if settings.contains('italic'):
            fmt.setFontItalic(settings.value('italic', False, bool))
        if settings.contains('underline'):
            fmt.setFontUnderline(settings.value('underline', False, bool))
        if settings.contains('textColor'):
            fmt.setForeground(QColor(settings.value('textColor', '' , type(""))))
        if settings.contains('backgroundColor'):
            fmt.setBackground(QColor(settings.value('backgroundColor', '' , type(""))))
        if settings.contains('underlineColor'):
            fmt.setUnderlineColor(QColor(settings.value('underlineColor', '' , type(""))))


def css2fmt(d, f=None):
    """Convert a css dictionary to a QTextCharFormat."""
    if f is None:
        f = QTextCharFormat()
    v = d.get('font-style')
    if v:
        f.setFontItalic(v in ('oblique', 'italic'))
    v = d.get('font-weight')
    if v:
        if v == 'bold':
            f.setFontWeight(QFont.Bold)
        elif v == 'normal':
            f.setFontWeight(QFont.Normal)
        elif v.isdigit():
            f.setFontWeight(int(v) / 10)
    v = d.get('color')
    if v:
        f.setForeground(QColor(v))
    v = d.get('background')
    if v:
        f.setBackground(QColor(v))
    v = d.get('text-decoration')
    if v:
        f.setFontUnderline(v == 'underline')
    v = d.get('text-decoration-color')
    if v:
        f.setUnderlineColor(QColor(v))
    return f

def fmt2css(f, d=None):
    """Convert a QTextCharFormat to a css dictionary."""
    if d is None:
        d = {}
    if f.hasProperty(QTextFormat.FontWeight):
        d['font-weight'] = 'bold' if f.fontWeight() >= 70 else 'normal'
    if f.hasProperty(QTextFormat.FontItalic):
        d['font-style'] = 'italic' if f.fontItalic() else 'normal'
    if f.hasProperty(QTextFormat.TextUnderlineStyle):
        d['text-decoration'] = 'underline' if f.fontUnderline() else 'none'
    if f.hasProperty(QTextFormat.ForegroundBrush):
        d['color'] = f.foreground().color().name()
    if f.hasProperty(QTextFormat.BackgroundBrush):
        d['background'] = f.background().color().name()
    if f.hasProperty(QTextFormat.TextUnderlineColor):
        d['text-decoration-color'] = f.underlineColor().name()
    return d


baseColors = (
    'text',
    'background',
    'selectiontext',
    'selectionbackground',
    'current',
    'mark',
    'error',
    'search',
    'match',
    'paper',
    'musichighlight',
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
    match =               lambda: QColor(0, 192, 255),
    paper =               lambda: QColor(255, 253, 240),
    musichighlight =      lambda: QApplication.palette().color(QPalette.Highlight),
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


# decorator that executes the function and returns the result
_result = lambda f: f()

@_result
def defaultStyleDefaults():
    keyword = QTextCharFormat()
    keyword.setFontWeight(QFont.Bold)
    
    function = QTextCharFormat(keyword)
    function.setForeground(QColor(0, 0, 192))
    
    variable = QTextCharFormat()
    variable.setForeground(QColor(0, 0, 255))
    
    value = QTextCharFormat()
    value.setForeground(QColor(128, 128, 0))
    
    string = QTextCharFormat()
    string.setForeground(QColor(192, 0, 0))
    
    escape = QTextCharFormat()
    escape.setForeground(QColor(0, 128, 128))
    
    comment = QTextCharFormat()
    comment.setForeground(QColor(128, 128, 128))
    comment.setFontItalic(True)
    
    error = QTextCharFormat()
    error.setForeground(QColor(255, 0, 0))
    error.setFontUnderline(True)
    
    return locals()


@_result
def allStyleDefaults():
    
    # LilyPond
    lilypond = {}
    
    lilypond['duration'] = f = QTextCharFormat()
    f.setForeground(QColor(0, 128, 128))
    
    lilypond['markup'] = f = QTextCharFormat()
    f.setForeground(QColor(0, 128, 0))
    f.setFontWeight(QFont.Normal)
    
    lilypond['lyricmode'] = f = QTextCharFormat()
    f.setForeground(QColor(0, 96, 0))
    
    lilypond['lyrictext'] = QTextCharFormat(f)
    
    lilypond['grob'] = f = QTextCharFormat()
    f.setForeground(QColor(192, 0, 192))
    
    lilypond['context'] = f = QTextCharFormat(f)
    f.setFontWeight(QFont.Bold)
    
    lilypond['slur'] = QTextCharFormat(f)
    
    lilypond['articulation'] = f = QTextCharFormat()
    f.setForeground(QColor(255, 128, 0))
    f.setFontWeight(QFont.Bold)
    
    lilypond['dynamic'] = QTextCharFormat(f)
    
    lilypond['fingering'] = f = QTextCharFormat()
    f.setForeground(QColor(255, 128, 0))
    
    lilypond['stringnumber'] = QTextCharFormat(f)
    
    # HTML
    html = {}
    
    # Scheme
    scheme = {}
    
    scheme['scheme'] = f = QTextCharFormat()
    f.setForeground(QColor(80, 40, 0))
    
    scheme['lilypond'] = f = QTextCharFormat(f)
    f.setFontWeight(QFont.Bold)
    
    scheme['delimiter'] = f = QTextCharFormat(f)
    f.setForeground(QColor(160, 0, 150))
    f.setFontWeight(QFont.Bold)
    
    scheme['keyword'] = f = QTextCharFormat()
    f.setForeground(QColor(0, 130, 150))
    f.setFontWeight(QFont.Bold)
    
    scheme['function'] = f = QTextCharFormat()
    f.setForeground(QColor(150, 0, 222))
    
    scheme['variable'] = QTextCharFormat(f)
    
    scheme['constant'] = QTextCharFormat(f)
    
    scheme['symbol'] = QTextCharFormat(f)
    
    # LaTeX
    latex = {}
    
    # DocBook
    docbook = {}
    
    # Texinfo
    texinfo = {}
    
    del f
    return locals()


allStyles = (
    ('lilypond', (
        'pitch',
        'octave',
        'duration',
        'fingering',
        'stringnumber',
        'slur',
        'dynamic',
        'articulation',
        'chord',
        'beam',
        'check',
        'repeat',
        'keyword',
        'command',
        'specifier',
        'usercommand',
        'markup',
        'lyricmode',
        'lyrictext',
        'delimiter',
        'context',
        'grob',
        'property',
        'variable',
        'uservariable',
        'value',
        'string',
        'stringescape',
        'comment',
        'error',
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
    ('scheme', (
        'scheme',
        'number',
        'lilypond',
        'string',
        'comment',
        'keyword',
        'function',
        'variable',
        'constant',
        'symbol',
        'delimiter',
        )),
    ('texinfo', (
        'keyword',
        'block',
        'attribute',
        'escapechar',
        'verbatim',
        'comment',
    ))
)


inherits = {
    'lilypond': {
        'keyword': 'keyword',
        'command': 'function',
        'markup': 'function',
        'lyricmode': 'function',
        'repeat': 'function',
        'specifier': 'variable',
        'usercommand': 'variable',
        'delimiter': 'keyword',
        'property': 'variable',
        'variable': 'variable',
        'value': 'value',
        'string': 'string',
        'stringescape': 'escape',
        'comment': 'comment',
        'error': 'error',
    },
    'html': {
        'tag': 'keyword',
        'lilypondtag': 'function',
        'attribute': 'variable',
        'value': 'value',
        'entityref': 'escape',
        'string': 'string',
        'comment': 'comment',
    },
    'scheme': {
        'number': 'value',
        'string': 'string',
        'comment': 'comment',
    },
    'texinfo': {
        'keyword': 'keyword',
        'block': 'function',
        'attribute': 'variable',
        'escapechar': 'escape',
        'verbatim': 'string',
        'comment': 'comment',
    }
        
}


