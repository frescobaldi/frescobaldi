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


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGridLayout, QLabel, QLineEdit, QSpinBox,
    QVBoxLayout, QWidget)

import app
import util
import qutil
import icons
import lasptyqu
import po.setup
import language_names
import preferences
import widgets.urlrequester


class Editor(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(Editor, self).__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(ViewSettings(self))
        layout.addWidget(Highlighting(self))
        layout.addWidget(Indenting(self))
        layout.addWidget(KeyBoard(self))
        layout.addWidget(SourceExport(self))
        layout.addWidget(TypographicalQuotes(self))
        layout.addStretch()


class ViewSettings(preferences.Group):
    def __init__(self, page):
        super(ViewSettings, self).__init__(page)

        layout = QGridLayout(spacing=1)
        self.setLayout(layout)

        self.wrapLines = QCheckBox(toggled=self.changed)
        self.numContextLines = QSpinBox(minimum=0, maximum=20, valueChanged=self.changed)
        self.numContextLinesLabel = l = QLabel()
        l.setBuddy(self.numContextLines)

        layout.addWidget(self.wrapLines, 0, 0, 1, 1)
        layout.addWidget(self.numContextLinesLabel, 1, 0)
        layout.addWidget(self.numContextLines, 1, 1)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("View Preferences"))
        self.wrapLines.setText(_("Wrap long lines by default"))
        self.wrapLines.setToolTip('<qt>' + _(
            "If enabled, lines that don't fit in the editor width are wrapped "
            "by default. "
            "Note: when the document is displayed by multiple views, they all "
            "share the same line wrapping width, which might look strange."))
        self.numContextLinesLabel.setText(_("Number of surrounding lines:"))
        self.numContextLines.setToolTip('<qt>' + _(
            "When jumping between search results or clicking on a link, the "
            "text view tries to scroll as few lines as possible. "
            "Here you can specify how many surrounding lines at least should "
            "be visible."))
        self.numContextLinesLabel.setToolTip(self.numContextLines.toolTip())

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("view_preferences")
        self.wrapLines.setChecked(s.value("wrap_lines", False, bool))
        self.numContextLines.setValue(s.value("context_lines", 3, int))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("view_preferences")
        s.setValue("wrap_lines", self.wrapLines.isChecked())
        s.setValue("context_lines", self.numContextLines.value())


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
        self.dspacesLabel.setText(_("Tab outside indent inserts:"))
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


class KeyBoard(preferences.Group):
    def __init__(self, page):
        super(KeyBoard, self).__init__(page)

        layout = QGridLayout(spacing=1)
        self.setLayout(layout)

        self.keepCursorInLine = QCheckBox(toggled=self.changed)
        self.smartHome = QCheckBox(toggled=self.changed)
        self.smartStartEnd = QCheckBox(toggled=self.changed)

        layout.addWidget(self.smartHome, 0, 0, 1, 1)
        layout.addWidget(self.smartStartEnd, 1, 0, 1, 1)
        layout.addWidget(self.keepCursorInLine, 2, 0, 1, 1)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Keyboard Preferences"))
        self.smartHome.setText(_("Smart Home key"))
        self.smartHome.setToolTip('<qt>' + _(
            "If enabled, pressing Home will put the cursor at the first non-"
            "whitespace character on the line. "
            "When the cursor is on that spot, pressing Home moves the cursor "
            "to the beginning of the line."))
        self.smartStartEnd.setText(_("Smart Up/PageUp and Down/PageDown keys"))
        self.smartStartEnd.setToolTip('<qt>' + _(
            "If enabled, pressing Up or PageUp in the first line will move the "
            "cursor to the beginning of the document, and pressing Down or "
            "PageDown in the last line will move the cursor to the end of the "
            "document."))
        self.keepCursorInLine.setText(_("Horizontal arrow keys keep cursor in current line"))
        self.keepCursorInLine.setToolTip('<qt>' + _(
            "If enabled, the cursor will stay in the current line when using "
            "the horizontal arrow keys, and not wrap around to the next or previous line."))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("view_preferences")
        self.smartHome.setChecked(s.value("smart_home_key", True, bool))
        self.smartStartEnd.setChecked(s.value("smart_start_end", True, bool))
        self.keepCursorInLine.setChecked(s.value("keep_cursor_in_line", False, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("view_preferences")
        s.setValue("smart_home_key", self.smartHome.isChecked())
        s.setValue("smart_start_end", self.smartStartEnd.isChecked())
        s.setValue("keep_cursor_in_line", self.keepCursorInLine.isChecked())


class SourceExport(preferences.Group):
    def __init__(self, page):
        super(SourceExport, self).__init__(page)

        layout = QGridLayout(spacing=1)
        self.setLayout(layout)

        self.numberLines = QCheckBox(toggled=self.changed)
        self.inlineStyleCopy = QCheckBox(toggled=self.changed)
        self.copyHtmlAsPlainText = QCheckBox(toggled=self.changed)
        self.inlineStyleExport = QCheckBox(toggled=self.changed)
        self.copyDocumentBodyOnly = QCheckBox(toggled=self.changed)
        self.wrapperTag = QLabel()
        self.wrapTagSelector = QComboBox()
        self.wrapTagSelector.currentIndexChanged.connect(page.changed)
        self.wrapperAttribute = QLabel()
        self.wrapAttribSelector = QComboBox()
        self.wrapAttribSelector.currentIndexChanged.connect(page.changed)
        self.wrapAttribNameLabel = QLabel()
        self.wrapAttribName = QLineEdit()
        self.wrapAttribName.textEdited.connect(page.changed)
        self.wrapperTag.setBuddy(self.wrapTagSelector)
        self.wrapperAttribute.setBuddy(self.wrapAttribSelector)
        self.wrapAttribNameLabel.setBuddy(self.wrapAttribName)

        layout.addWidget(self.copyHtmlAsPlainText, 0, 0, 1, 2)
        layout.addWidget(self.copyDocumentBodyOnly, 1, 0, 1, 2)
        layout.addWidget(self.inlineStyleCopy, 2, 0, 1, 2)
        layout.addWidget(self.inlineStyleExport, 3, 0, 1, 2)
        layout.addWidget(self.numberLines, 4, 0, 1, 2)
        layout.addWidget(self.wrapperTag, 5, 0)
        layout.addWidget(self.wrapTagSelector, 5, 1)
        layout.addWidget(self.wrapperAttribute, 6, 0)
        layout.addWidget(self.wrapAttribSelector, 6, 1)
        layout.addWidget(self.wrapAttribNameLabel, 7, 0)
        layout.addWidget(self.wrapAttribName, 7, 1)

        self.wrapTagSelector.addItem("pre")
        self.wrapTagSelector.addItem("code")
        self.wrapTagSelector.addItem("div")
        self.wrapAttribSelector.addItem("id")
        self.wrapAttribSelector.addItem("class")

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
            "If enabled, inline style attributes are used when exporting "
            "colored HTML to a file. "
            "Otherwise, a CSS stylesheet is embedded."))
        self.copyHtmlAsPlainText.setText(_("Copy HTML as plain text"))
        self.copyHtmlAsPlainText.setToolTip('<qt>' + _(
            "If enabled, HTML is copied to the clipboard as plain text. "
            "Use this when you want to type HTML formatted code in a "
            "plain text editing environment."))
        self.copyDocumentBodyOnly.setText(_("Copy document body only"))
        self.copyDocumentBodyOnly.setToolTip('<qt>' + _(
            "If enabled, only the HTML contents, wrapped in a single tag, will be "
            "copied to the clipboard instead of a full HTML document with a "
            "header section. "
            "May be used in conjunction with the plain text option, with the "
            "inline style option turned off, to copy highlighted code in a "
            "text editor when an external style sheet is already available."))
        self.wrapperTag.setText(_("Tag to wrap around source:" + "  "))
        self.wrapperTag.setToolTip('<qt>' + _(
            "Choose what tag the colored HTML will be wrapped into."))
        self.wrapperAttribute.setText(_("Attribute type of wrapper:" + "  "))
        self.wrapperAttribute.setToolTip('<qt>' + _(
            "Choose whether the wrapper tag should be of type 'id' or 'class'"))
        self.wrapAttribNameLabel.setText(_("Name of attribute:" + "  "))
        self.wrapAttribNameLabel.setToolTip('<qt>' + _(
            "Arbitrary name for the type attribute. " +
            "This must match the CSS stylesheet if using external CSS."))


    def loadSettings(self):
        s = QSettings()
        s.beginGroup("source_export")
        self.numberLines.setChecked(s.value("number_lines", False, bool))
        self.inlineStyleCopy.setChecked(s.value("inline_copy", True, bool))
        self.inlineStyleExport.setChecked(s.value("inline_export", False, bool))
        self.copyHtmlAsPlainText.setChecked(s.value("copy_html_as_plain_text", False, bool))
        self.copyDocumentBodyOnly.setChecked(s.value("copy_document_body_only", False, bool))
        self.wrapTagSelector.setCurrentIndex(
            self.wrapTagSelector.findText(s.value("wrap_tag", "pre", str)))
        self.wrapAttribSelector.setCurrentIndex(
            self.wrapAttribSelector.findText(s.value("wrap_attrib", "id", str)))
        self.wrapAttribName.setText(s.value("wrap_attrib_name", "document", str))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("source_export")
        s.setValue("number_lines", self.numberLines.isChecked())
        s.setValue("inline_copy", self.inlineStyleCopy.isChecked())
        s.setValue("inline_export", self.inlineStyleExport.isChecked())
        s.setValue("copy_html_as_plain_text", self.copyHtmlAsPlainText.isChecked())
        s.setValue("copy_document_body_only", self.copyDocumentBodyOnly.isChecked())
        s.setValue("wrap_tag", self.wrapTagSelector.currentText())
        s.setValue("wrap_attrib", self.wrapAttribSelector.currentText())
        s.setValue("wrap_attrib_name", self.wrapAttribName.text())


class TypographicalQuotes(preferences.Group):
    def __init__(self, page):
        super(TypographicalQuotes, self).__init__(page)

        layout = QGridLayout(spacing=1)
        self.setLayout(layout)
        l = self.languageLabel = QLabel()
        c = self.languageCombo = QComboBox(currentIndexChanged=self.languageChanged)
        l.setBuddy(c)

        self.primaryLabel = QLabel()
        self.secondaryLabel = QLabel()
        self.primaryLeft = QLineEdit(textEdited=self.changed)
        self.primaryRight = QLineEdit(textEdited=self.changed)
        self.secondaryLeft = QLineEdit(textEdited=self.changed)
        self.secondaryRight = QLineEdit(textEdited=self.changed)

        self._langs = ["current", "custom"]
        self._langs.extend(lang for lang in lasptyqu.available() if lang != "C")
        c.addItems(['' for i in self._langs])

        layout.addWidget(self.languageLabel, 0, 0)
        layout.addWidget(self.primaryLabel, 1, 0)
        layout.addWidget(self.secondaryLabel, 2, 0)
        layout.addWidget(self.languageCombo, 0, 1, 1, 2)
        layout.addWidget(self.primaryLeft, 1, 1)
        layout.addWidget(self.primaryRight, 1, 2)
        layout.addWidget(self.secondaryLeft, 2, 1)
        layout.addWidget(self.secondaryRight, 2, 2)

        app.translateUI(self)

    def languageChanged(self):
        """Called when the user changes the combobox."""
        enabled = self.languageCombo.currentIndex() == 1
        self.primaryLabel.setEnabled(enabled)
        self.primaryLeft.setEnabled(enabled)
        self.primaryRight.setEnabled(enabled)
        self.secondaryLabel.setEnabled(enabled)
        self.secondaryLeft.setEnabled(enabled)
        self.secondaryRight.setEnabled(enabled)
        self.changed.emit()

    def translateUI(self):
        self.setTitle(_("Typographical Quotes"))
        self.languageLabel.setText(_("Quotes to use:"))
        self.primaryLabel.setText(_("Primary (double) quotes:"))
        self.secondaryLabel.setText(_("Secondary (single) quotes:"))
        curlang = po.setup.current()
        qformat = "{0}   {1.primary.left} {1.primary.right}    {1.secondary.left} {1.secondary.right}"
        self.languageCombo.setItemText(0, qformat.format(
            _("Current language"), lasptyqu.quotes(curlang) or lasptyqu.default()))
        self.languageCombo.setItemText(1, _("Custom quotes (enter below)"))
        for i, lang in enumerate(self._langs[2:], 2):
            self.languageCombo.setItemText(i, qformat.format(
                language_names.languageName(lang, curlang), lasptyqu.quotes(lang)))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup("typographical_quotes")
        lang = s.value("language", "current", str)
        try:
            index = self._langs.index(lang)
        except ValueError:
            index = 0
        self.languageCombo.setCurrentIndex(index)
        default = lasptyqu.default()
        self.primaryLeft.setText(s.value("primary_left", default.primary.left, str))
        self.primaryRight.setText(s.value("primary_right", default.primary.right, str))
        self.secondaryLeft.setText(s.value("secondary_left", default.secondary.left, str))
        self.secondaryRight.setText(s.value("secondary_right", default.secondary.right, str))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup("typographical_quotes")
        s.setValue("language", self._langs[self.languageCombo.currentIndex()])
        s.setValue("primary_left", self.primaryLeft.text())
        s.setValue("primary_right", self.primaryRight.text())
        s.setValue("secondary_left", self.secondaryLeft.text())
        s.setValue("secondary_right", self.secondaryRight.text())
