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
Show a dialog with available fonts.
"""


import codecs
import re

from PyQt5.QtCore import (
    QRegExp,
    QSettings,
    QSize,
    Qt,
    QSortFilterProxyModel,
)
from PyQt5.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QTabWidget,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import(
    QFont,
    QFontDatabase,
    QStandardItem,
    QStandardItemModel,
)

import app
import job
import log
import qutil
import widgets.dialog
from widgets.lineedit import LineEdit
from . import available_fonts


def show_available_fonts(mainwin, info):
    """Display a dialog with the available fonts of LilyPond specified by info."""
    dlg = ShowFontsDialog(mainwin, info)
    qutil.saveDialogSize(dlg, "engrave/tools/available-fonts/dialog/size", QSize(640, 400))
    dlg.show()


class FontFilterProxyModel(QSortFilterProxyModel):
    """Custom proxy model that ignores child elements in filtering"""

    def filterAcceptsRow(self, row, parent):
        if parent.isValid():
            return True
        else:
            return super(FontFilterProxyModel, self).filterAcceptsRow(row, parent)


class ShowFontsDialog(widgets.dialog.Dialog):
    """Dialog to show available fonts"""

    # Store the filter expression over the object's lifetime
    filter_re = ''

    def __init__(self, parent, info):

        def create_log_tab():
            # Show original log
            self.logTab = QWidget()
            self.logWidget = log.Log(self.logTab)
            logLayout = QVBoxLayout()
            logLayout.addWidget(self.logWidget)
            self.logTab.setLayout(logLayout)
            self.tabWidget.addTab(self.logTab, _("LilyPond output"))

        def create_font_tab():
            # Show Font results
            self.fontTreeTab = QWidget()
            self.fontCountLabel = QLabel(self.fontTreeTab)
            self.filterEdit = LineEdit()
            self.fontTreeView = QTreeView(self.fontTreeTab)
            treeLayout = QVBoxLayout()
            treeLayout.addWidget(self.fontCountLabel)
            treeLayout.addWidget(self.fontTreeView)
            treeLayout.addWidget(self.filterEdit)
            self.fontTreeTab.setLayout(treeLayout)
            self.tabWidget.addTab(self.fontTreeTab, _("Fonts"))

        def create_font_model():
            self.treeModel = tm = QStandardItemModel()
            self.proxy = FontFilterProxyModel()
            self.proxy.setSourceModel(tm)
            self.fontTreeView.setModel(self.proxy)
            self.filterEdit.textChanged.connect(self.update_filter)
            self.filter = QRegExp('', Qt.CaseInsensitive)

        def create_misc_tab():
            self.miscTab = QWidget()
            self.miscTreeView = QTreeView(self.miscTab)
            self.miscTreeView.setHeaderHidden(True)
            miscLayout = QVBoxLayout()
            miscLayout.addWidget(self.miscTreeView)
            self.miscTab.setLayout(miscLayout)
            self.tabWidget.addTab(self.miscTab, _("Miscellaneous"))

        def create_misc_model():
            self.miscModel = QStandardItemModel()
            self.miscTreeView.setModel(self.miscModel)


        super(ShowFontsDialog, self).__init__(
            parent,
            buttons=('restoredefaults', 'close',),
        )
        self.reloadButton = self._buttonBox.button(
            QDialogButtonBox.RestoreDefaults)
        self.reloadButton.setEnabled(False)
        self.reloadButton.clicked.connect(self.reload)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.NonModal)

        self.lilypond_info = info

        self.tabWidget = QTabWidget(self)
        self.setMainWidget(self.tabWidget)

        create_log_tab()
        create_font_tab()
        create_font_model()
        create_misc_tab()
        create_misc_model()

        app.translateUI(self)
        self.loadSettings()
        self.finished.connect(self.saveSettings)

        available_fonts.loaded.connect(self.populate_widgets)
        if not available_fonts.is_loaded:
            self.fontCountLabel.setText(_("Running LilyPond to list fonts ..."))
            available_fonts.load_fonts(info, self.logWidget)
        else:
            self.populate_widgets()

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Available Fonts")))
        self.filterEdit.setPlaceholderText(
            _("Filter results (type any part of the font family name. "
            + "Regular Expressions supported.)"))
        self.reloadButton.setText(_("&Reload"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        self.fontTreeView.setColumnWidth(0, int(s.value('col-width', 200)))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        s.setValue('col-width', self.fontTreeView.columnWidth(0))

    def initTreeModel(self):
        """Initialize the tree model, which has to be redone upon
        any reload/reset of the model."""
        tm = self.treeModel
        tm.clear()
        tm.setColumnCount(2)
        tm.setHeaderData(0, Qt.Horizontal, _("Font"))
        tm.setHeaderData(1, Qt.Horizontal, _("Sample"))
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        self.fontTreeView.setColumnWidth(0, int(s.value('col-width', 200)))

    def populate_widgets(self):
        """Populate widgets."""
        self.fontCountLabel.setText(
            _("{count} font families detected by {version}").format(
                count=len(available_fonts.family_names()),
                version=self.lilypond_info.prettyName()))
        self.populate_font_tree()
        self.populate_misc()
        self.tabWidget.setCurrentIndex(1)
        self.filterEdit.setText(ShowFontsDialog.filter_re)
        self.filterEdit.setFocus()
        self.reloadButton.setEnabled(True)

    def populate_font_tree(self):
        """Populate the data model to be displayed in the results"""

        def sample(sub_family, style):
            """Produce a styled font sample for a given weight/style.
            This is not completely reliable since the style aliases
            returned by LilyPond are somewhat inconsistent and don't
            always match a font style that PyQt can get."""
            item = QStandardItem(
                _('The quick brown fox jumps over the lazy dog'))
            font = QFont(sub_family)
            font.setStyleName(style)
            item.setFont(font)
            return item

        self.initTreeModel()
        root = self.treeModel.invisibleRootItem()
        for name in available_fonts.family_names():
            family = available_fonts.font_families()[name]
            sub_families = []
            for sub_family_name in sorted(family.keys()):
                sub_family = family[sub_family_name]
                if len(sub_family) == 1:
                    # Subfamily has only one entry, create single line
                    style = sub_family[0]
                    sub_families.append(
                        [QStandardItem('{} ({})'.format(
                            sub_family_name, style)),
                        sample(sub_family_name, style)])
                else:
                    # Subfamily has multiple entries, create
                    # container plus styled line for each style
                    sub_family_item = QStandardItem(sub_family_name)
                    sub_families.append(sub_family_item)
                    for style in sorted(sub_family):
                        sub_family_item.appendRow(
                            [QStandardItem(style),
                            sample(sub_family_name, style)])

            # Pull up subfamily as top-level entry if
            # - there is only one subfamily and
            # - it is a subfamily item with children
            if (len(sub_families) == 1
                and isinstance(sub_families[0], QStandardItem)
            ):
                root.appendRow(sub_families[0])
            else:
                family_item = QStandardItem(name)
                root.appendRow(family_item)
                for f in sub_families:
                    family_item.appendRow(f)

    def populate_misc(self):
        """Populate the data model for the "Miscellaneous" tab"""
        self.miscModel.clear()
        root = self.miscModel.invisibleRootItem()

        conf_file_item = QStandardItem(_("Configuration Files"))
        root.appendRow(conf_file_item)
        for file in available_fonts.config_files():
            conf_file_item.appendRow(QStandardItem(file))

        conf_dir_item = QStandardItem(_("Configuration Directories"))
        root.appendRow(conf_dir_item)
        for dir in available_fonts.config_dirs():
            conf_dir_item.appendRow(QStandardItem(dir))

        font_dir_item = QStandardItem(_("Font Directories"))
        root.appendRow(font_dir_item)
        for dir in available_fonts.font_dirs():
            font_dir_item.appendRow(QStandardItem(dir))

    def reload(self):
        """Refresh font list by running LilyPond"""
        self.tabWidget.setCurrentIndex(0)
        self.logWidget.clear()
        # We're connected to the 'loaded' signal
        available_fonts.load_fonts(self.lilypond_info, self.logWidget)

    def update_filter(self):
        """Filter font results"""
        ShowFontsDialog.filter_re = re = self.filterEdit.text()
        self.filter.setPattern(re)
        self.proxy.setFilterRegExp(self.filter)
