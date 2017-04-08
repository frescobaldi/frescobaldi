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
A widget that provides a scheme selector, with New and Remove buttons.
"""


try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from PyQt5.QtGui import (
    QTextFormat, QColor, QTextCharFormat, QFont, QFontDatabase,
    QKeySequence)
from PyQt5.QtWidgets import QMessageBox

import os
import appinfo
import textformats
import app

def exportTheme(widget, schemeName, filename):
    """Saves the colors theme to a file."""
    tfd = widget.currentSchemeData()
    root = ET.Element('frescobaldi-theme')
    root.set('name', schemeName)
    comment = ET.Comment(_comment.format(appinfo=appinfo))
    root.append(comment)
    d = ET.ElementTree(root)

    font = tfd.font
    fontfamily = font.family()
    fontsize = str(font.pointSizeF())
    fontElt = ET.Element('font', {'fontFamily': fontfamily, 'fontSize': fontsize})
    root.append(fontElt)

    baseColors = ET.Element('baseColors')
    for name, color in tfd.baseColors.items():
        elt = ET.Element(name)
        elt.set('color', color.name())
        baseColors.append(elt)

    defaultStyles = ET.Element('defaultStyles')
    for name, fmt in tfd.defaultStyles.items():
        elt = styleToElt(fmt, name)
        if elt is not None:
            defaultStyles.append(elt)

    allStyles = ET.Element('allStyles')
    for name, styles in tfd.allStyles.items():
        subElt = ET.Element(name)
        for name, fmt in styles.items():
            elt = styleToElt(fmt, name)
            if elt is not None:
                subElt.append(elt)
        if list(subElt):
            allStyles.append(subElt)
    root.append(baseColors)
    root.append(defaultStyles)
    root.append(allStyles)

    indentXml(root)
    d.write(filename, 'UTF-8')


def importTheme(filename, widget, schemeWidget):
    """Loads the colors theme from a file"""
    try:
        d = ET.parse(filename)
        root = d.getroot()
        if root.tag != 'frescobaldi-theme':
            raise ValueError(_("No theme found."))
    except Exception as e:
        QMessageBox.critical(widget, app.caption(_("Error")),
        _("Can't read from source:\n\n{url}\n\n{error}").format(
            url=filename, error=e))
        return

    schemeWidget.scheme.blockSignals(True)
    key = schemeWidget.addScheme(root.get('name'))
    schemeWidget.scheme.blockSignals(False)
    tfd = textformats.TextFormatData(key)

    fontElt = root.find('font')

    defaultfont = "Lucida Console" if os.name == "nt" else "monospace"
    if fontElt.get('fontFamily') in QFontDatabase().families():
        fontFamily = fontElt.get('fontFamily')
    else:
        fontFamily = defaultfont
    font = QFont(fontFamily)
    font.setPointSizeF(float(fontElt.get('fontSize')))
    tfd.font = font

    for elt in root.find('baseColors'):
        tfd.baseColors[elt.tag] = QColor(elt.get('color'))

    for elt in root.find('defaultStyles'):
        tfd.defaultStyles[elt.tag] = eltToStyle(elt)

    for style in root.find('allStyles'):
        if not style in tfd.allStyles:
            tfd.allStyles[style] = {}
        for elt in style:
            tfd.allStyles[style.tag][elt.tag] = eltToStyle(elt)

    widget.addSchemeData(key, tfd)
    schemeWidget.disableDefault(False)
    schemeWidget.currentChanged.emit()
    schemeWidget.changed.emit()


def exportShortcut(widget, scheme, schemeName, filename):
    """Saves shortcuts to a file."""
    lst = {}
    for item in widget.items():
        col = item.collection.name
        if not col in lst:
            lst[col] = {}
        if not item.isDefault(scheme):
            lst[col][item.name] = item.shortcuts(scheme)

    root = ET.Element('frescobaldi-shortcut')
    root.set('name', schemeName)
    comment = ET.Comment(_comment.format(appinfo=appinfo))
    root.append(comment)
    d = ET.ElementTree(root)

    for col, shortcuts in lst.items():
        if not shortcuts:
            continue
        colElt = ET.Element('collection')
        colElt.set('name', col)
        root.append(colElt)
        for name, shortList in shortcuts.items():
            nameElt = ET.Element('name')
            nameElt.set('name', name)
            colElt.append(nameElt)
            for seq in shortList:
                shortcutElt = ET.Element('shortcut')
                shortcutElt.text = seq.toString()
                nameElt.append(shortcutElt)

    indentXml(root)
    d.write(filename, 'UTF-8')



def importShortcut(filename, widget, schemeWidget):
    """Loads shortcuts from a file"""
    try:
        d = ET.parse(filename)
        root = d.getroot()
        if root.tag != 'frescobaldi-shortcut':
            raise ValueError(_("No shortcuts found."))
    except Exception as e:
        QMessageBox.critical(widget, app.caption(_("Error")),
        _("Can't read from source:\n\n{url}\n\n{error}").format(
            url=filename, error=e))
        return

    schemeWidget.scheme.blockSignals(True)
    scheme = schemeWidget.addScheme(root.get('name'))
    schemeWidget.scheme.blockSignals(False)

    for col in root.findall('collection'):
        for name in col.findall('name'):
            shortcuts = [QKeySequence.fromString(shortcut.text) for shortcut in name.findall('shortcut')]
            item = widget.item(col.attrib['name'], name.attrib['name'])
            if item:
                item.setShortcuts(shortcuts, scheme)

    schemeWidget.disableDefault(False)
    schemeWidget.currentChanged.emit()
    schemeWidget.changed.emit()


def styleToElt(fmt, name):
    elt = ET.Element(name)
    if fmt.hasProperty(QTextFormat.FontWeight):
        elt.set('bold', str(fmt.fontWeight() >= 70))
    if fmt.hasProperty(QTextFormat.FontItalic):
        elt.set('italic', str(fmt.fontItalic()))
    if fmt.hasProperty(QTextFormat.TextUnderlineStyle):
        elt.set('underline', str(fmt.fontUnderline()))
    if fmt.hasProperty(QTextFormat.ForegroundBrush):
        elt.set('textColor', fmt.foreground().color().name())
    if fmt.hasProperty(QTextFormat.BackgroundBrush):
        elt.set('backgroundColor', fmt.background().color().name())
    if fmt.hasProperty(QTextFormat.TextUnderlineColor):
        elt.set('underlineColor', fmt.underlineColor().name())

    return elt if elt.attrib else None



def toBool(val):
    return {'True': True, 'False': False}[val]

def eltToStyle(elt):
    fmt = QTextCharFormat()
    if elt.get('bold'):
        fmt.setFontWeight(QFont.Bold if toBool(elt.get('bold')) else QFont.Normal)
    if elt.get('italic'):
        fmt.setFontItalic(toBool(elt.get('italic')))
    if elt.get('underline'):
        fmt.setFontUnderline(toBool(elt.get('underline')))
    if elt.get('textColor'):
        fmt.setForeground(QColor(elt.get('textColor')))
    if elt.get('backgroundColor'):
        fmt.setBackground(QColor(elt.get('backgroundColor')))
    if elt.get('underlineColor'):
        fmt.setUnderlineColor(QColor(elt.get('underlineColor')))

    return fmt

def indentXml(elem, level=0, tab=2):
    i = "\n" + level*" "*tab
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + " "*tab
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indentXml(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


_comment = """
  Created by {appinfo.appname} {appinfo.version}.
"""