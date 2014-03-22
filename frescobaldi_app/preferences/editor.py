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
Helper application preferences.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QSpinBox, 
    QVBoxLayout, QWidget)

import app
import util
import qutil
import icons
import preferences
import widgets.urlrequester


class Editor(preferences.GroupsPage):
    def __init__(self, dialog):
        super(Editor, self).__init__(dialog)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(ViewSettings(self))
        layout.addWidget(Highlighting(self))
        layout.addWidget(Indenting(self))
        layout.addWidget(SourceExport(self))
        layout.addStretch()


class ViewSettings(preferences.Group):
    def __init__(self, page):
        super(ViewSettings, self).__init__(page)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.wrapLines = QCheckBox(toggled=self.changed)
        
        layout.addWidget(self.wrapLines)
        app.translateUI(self)
    
    def translateUI(self):
        self.setTitle(_("View Preferences"))
        self.wrapLines.setText(_("Wrap long lines by default"))
        self.wrapLines.setToolTip('<qt>' + _(
            "If enabled, lines that don't fit in the editor width are wrapped "
            "by default. "
            "Note: when the document is displayed by multiple views, they all "
            "share the same line wrapping width, which might look strange."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("view_preferences")
        self.wrapLines.setChecked(s.value("wrap_lines", False, bool))
    
    def saveSettings(self):
        s = QSettings()
        s.beginGroup("view_preferences")
        s.setValue("wrap_lines", self.wrapLines.isChecked())


class Highlighting(preferences.Group):
    def __init__(self, page):
        super(Highlighting, self).__init__(page)
        
        layout = QGridLayout(spacing=1)
        self.setLayout(layout)
        
        self.messageLabel = QLabel(wordWrap=True)
        layout.addWidget(self.messageLabel, 0, 0, 1, 2)
        self.labels = {}
        self.entries = {}
        for row, (name, title, default) in enumerate(self.items(), 1):
            self.labels[name] = l = QLabel()
            self.entries[name] = e = QSpinBox()
            e.setRange(0, 60)
            e.valueChanged.connect(page.changed)
            layout.addWidget(l, row, 0)
            layout.addWidget(e, row, 1)
            
        app.translateUI(self)
    
    def items(self):
        """
        Yields (name, title, default) tuples for every setting in this group.
        Default is understood in seconds.
        """
        yield "match", _("Matching Item:"), 1
        
    def translateUI(self):
        self.setTitle(_("Highlighting Options"))
        self.messageLabel.setText(_(
            "Below you can define how long "
            "\"matching\" items like matching brackets or the items "
            "linked through Point-and-Click are highlighted."))
        # L10N: abbreviation for "n seconds" in spinbox, n >= 1, no plural forms
        prefix, suffix = _("{num} sec").split("{num}")
        for name, title, default in self.items():
            self.entries[name].setSpecialValueText(_("Infinite"))
            self.entries[name].setPrefix(prefix)
            self.entries[name].setSuffix(suffix)
            self.labels[name].setText(title)
    
    def loadSettings(self):
        s = QSettings()
        s.beginGroup("editor_highlighting")
        for name, title, default in self.items():
            self.entries[name].setValue(s.value(name, default, int))
    
    def saveSettings(self):
        s= QSettings()
        s.beginGroup("editor_highlighting")
        for name, title, default in self.items():
            s.setValue(name, self.entries[name].value())


class Indenting(preferences.Group):
    def __init__(self, page):
        super(Indenting, self).__init__(page)
        
        layout = QGridLayout(spacing=1)
        self.setLayout(layout)
        
        self.tabwidthBox = QSpinBox(minimum=1, maximum=99)
        self.tabwidthLabel = l = QLabel()
        l.setBuddy(self.tabwidthBox)
        
        self.nspacesBox = QSpinBox(minimum=0, maximum=99)
        self.nspacesLabel = l = QLabel()
        l.setBuddy(self.nspacesBox)
        
        self.dspacesBox = QSpinBox(minimum=0, maximum=99)
        self.dspacesLabel = l = QLabel()
        l.setBuddy(self.dspacesBox)
        
        layout.addWidget(self.tabwidthLabel, 0, 0)
        layout.addWidget(self.tabwidthBox, 0, 1)
        layout.addWidget(self.nspacesLabel, 1, 0)
        layout.addWidget(self.nspacesBox, 1, 1)
        layout.addWidget(self.dspacesLabel, 2, 0)
        layout.addWidget(self.dspacesBox, 2, 1)
        
        self.tabwidthBox.valueChanged.connect(page.changed)
        self.nspacesBox.valueChanged.connect(page.changed)
        self.dspacesBox.valueChanged.connect(page.changed)
        self.translateUI()
        
    def translateUI(self):
        self.setTitle(_("Indenting Preferences"))
        self.tabwidthLabel.setText(_("Visible Tab Width:"))
        self.tabwidthBox.setToolTip(_(
            "The visible width of a Tab character in the editor."))
        self.nspacesLabel.setText(_("Indent text with:"))
        self.nspacesBox.setToolTip(_(
            "How many spaces to use for indenting one level.\n"
            "Move to zero to use a Tab character for indenting."))
        self.nspacesBox.setSpecialValueText(_("Tab"))
        self.dspacesLabel.setText(_("Tab ouside indent inserts:"))
        self.dspacesBox.setToolTip(_(
            "How many spaces to insert when Tab is pressed outside the indent, "
            "elsewhere in the document.\n"
            "Move to zero to insert a literal Tab character in this case."))
        self.nspacesBox.setSpecialValueText(_("Tab"))
        self.dspacesBox.setSpecialValueText(_("Tab"))
        # L10N: abbreviation for "n spaces" in spinbox, n >= 1, no plural forms
        prefix, suffix = _("{num} spaces").split("{num}")
        self.nspacesBox.setPrefix(prefix)
        self.nspacesBox.setSuffix(suffix)
        self.dspacesBox.setPrefix(prefix)
        self.dspacesBox.setSuffix(suffix)

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("indent")
        self.tabwidthBox.setValue(s.value("tab_width", 8, int))
        self.nspacesBox.setValue(s.value("indent_spaces", 2, int))
        self.dspacesBox.setValue(s.value("document_spaces", 8, int))
    
    def saveSettings(self):
        s = QSettings()
        s.beginGroup("indent")
        s.setValue("tab_width", self.tabwidthBox.value())
        s.setValue("indent_spaces", self.nspacesBox.value())
        s.setValue("document_spaces", self.dspacesBox.value())


class SourceExport(preferences.Group):
    def __init__(self, page):
        super(SourceExport, self).__init__(page)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.numberLines = QCheckBox(toggled=self.changed)
        self.inlineStyleCopy = QCheckBox(toggled=self.changed)
        self.copyHtmlAsPlainText = QCheckBox(toggled=self.changed)
        self.inlineStyleExport = QCheckBox(toggled=self.changed)
        self.copyDocumentBodyOnly = QCheckBox(toggled=self.changed)

        layout.addWidget(self.numberLines)
        layout.addWidget(self.inlineStyleCopy)
        layout.addWidget(self.inlineStyleExport)
        layout.addWidget(self.copyHtmlAsPlainText)
        layout.addWidget(self.copyDocumentBodyOnly)

        app.translateUI(self)
    
    def translateUI(self):
        self.setTitle(_("Source Export Preferences"))
        self.numberLines.setText(_("Show line numbers"))
        self.numberLines.setToolTip('<qt>' + _(
            "If enabled, line numbers are shown in exported HTML or printed "
            "source."))
        self.inlineStyleCopy.setText(_("Use inline style when copying colored HTML"))
        self.inlineStyleCopy.setToolTip('<qt>' + _(
            "If enabled, inline style attributes are used when copying "
            "colored HTML to the clipboard. "
            "Otherwise, a CSS stylesheet is embedded."))
        
        self.inlineStyleExport.setText(_("Use inline style when exporting colored HTML"))
        self.inlineStyleExport.setToolTip('<qt>' + _(
            "If enabled, inline style attributes are used when exporing "
            "colored HTML to a file. "
            "Otherwise, a CSS stylesheet is embedded."))
        self.copyHtmlAsPlainText.setText(_("Copy HTML as plain text"))
        self.copyHtmlAsPlainText.setToolTip('<qt>' + _(
            "If enabled, HTML is copied to the clipboard as plain text. "
            "Use this when you want to type HTML formatted code in a "
            "plain text editing environment."))
        self.copyDocumentBodyOnly.setText(_("Copy <pre> element only"))
        self.copyDocumentBodyOnly.setToolTip('<qt>' + _(
            "If enabled, only the HTML contents, wrapped in a PRE tag, will be "
            "copied to the clipboard instead of a full HTML document with a "
            "header section. "
            "May be used in conjunction with the plain text option, with the "
            "inline style option turned off, to copy highlighted code in a "
            "text editor when an external style sheet is already available."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("source_export")
        self.numberLines.setChecked(s.value("number_lines", False, bool))
        self.inlineStyleCopy.setChecked(s.value("inline_copy", True, bool))
        self.inlineStyleExport.setChecked(s.value("inline_export", False, bool))
        self.copyHtmlAsPlainText.setChecked(s.value("copy_html_as_plain_text", False, bool))
        self.copyDocumentBodyOnly.setChecked(s.value("copy_document_body_only", False, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("source_export")
        s.setValue("number_lines", self.numberLines.isChecked())
        s.setValue("inline_copy", self.inlineStyleCopy.isChecked())
        s.setValue("inline_export", self.inlineStyleExport.isChecked())
        s.setValue("copy_html_as_plain_text", self.copyHtmlAsPlainText.isChecked())
        s.setValue("copy_document_body_only", self.copyDocumentBodyOnly.isChecked())


