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

from PyQt5.QtCore import QSize, Qt, QSortFilterProxyModel, QRegExp, QSettings
from PyQt5.QtWidgets import (
    QLabel, QWidget, QLineEdit, QVBoxLayout, QTabWidget, QTextEdit,
    QTreeView, QDialogButtonBox
)
from PyQt5.QtGui import(
    QStandardItemModel, QStandardItem, QFont, QFontDatabase
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

    def __init__(self, parent, info):

        def create_log_tab():
            # Show original log
            self.logWidget = QWidget()
            self.log = log.Log(self.logWidget)
            logLayout = QVBoxLayout()
            logLayout.addWidget(self.log)
            self.logWidget.setLayout(logLayout)
            self.tabWidget.addTab(self.logWidget, _("LilyPond output"))

        def create_font_tab():
            # Show Font results
            self.fontTreeWidget = QWidget()
            self.msgLabel = QLabel(self.fontTreeWidget)
            self.filterEdit = LineEdit()
            self.fontTree = QTreeView(self.fontTreeWidget)
            treeLayout = QVBoxLayout()
            treeLayout.addWidget(self.msgLabel)
            treeLayout.addWidget(self.fontTree)
            treeLayout.addWidget(self.filterEdit)
            self.fontTreeWidget.setLayout(treeLayout)
            self.tabWidget.addTab(self.fontTreeWidget, _("Fonts"))

        def create_font_model():
            self.treeModel = tm = QStandardItemModel()
            self.proxy = FontFilterProxyModel()
            self.proxy.setSourceModel(tm)
            self.fontTree.setModel(self.proxy)
            self.filterEdit.textChanged.connect(self.update_filter)
            self.filter = QRegExp('', Qt.CaseInsensitive)

        def create_misc_tab():
            self.miscWidget = QWidget()
            self.miscTree = QTreeView(self.miscWidget)
            self.miscTree.setHeaderHidden(True)
            miscLayout = QVBoxLayout()
            miscLayout.addWidget(self.miscTree)
            self.miscWidget.setLayout(miscLayout)
            self.tabWidget.addTab(self.miscWidget, _("Miscellaneous"))

        def create_misc_model():
            self.miscModel = QStandardItemModel()
            self.miscTree.setModel(self.miscModel)


        super(ShowFontsDialog, self).__init__(
            parent,
            buttons=('restoredefaults', 'close',),
        )
        self._buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.reload)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.NonModal)

        self.lilypond_info = info
        self.filter_re = ''

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
            self.msgLabel.setText(_("Running LilyPond to list fonts ..."))
            available_fonts.load_fonts(info, self.log)
        else:
            self.populate_widgets()



    def translateUI(self):
        self.setWindowTitle(app.caption(_("Available Fonts")))
        self.filterEdit.setPlaceholderText(_("Filter results (type any part of the font family name. Regular Expressions supported.)"))
        self._buttonBox.button(QDialogButtonBox.RestoreDefaults).setText(_("&Refresh"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        self.fontTree.setColumnWidth(0, int(s.value('col-width', 200)))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        s.setValue('col-width', self.fontTree.columnWidth(0))


    def initTreeModel(self):
        tm = self.treeModel
        tm.clear()
        tm.setColumnCount(2)
        tm.setHeaderData(0, Qt.Horizontal, _("Font"))
        tm.setHeaderData(1, Qt.Horizontal, _("Sample"))
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        self.fontTree.setColumnWidth(0, int(s.value('col-width', 200)))

    def populate_widgets(self):
        """Populate widgets."""
        self.msgLabel.setText(
            _("{count} font families detected by {version}").format(
                count=len(available_fonts.family_names()),
                version=self.lilypond_info.prettyName()))
        self.populate_font_tree()
        self.populate_misc()
        self.tabWidget.setCurrentIndex(1)
        self.filterEdit.setText(self.filter_re)
        self.filterEdit.setFocus()


    def populate_font_tree(self):
        """Populate the data model to be displayed in the results"""

        def sample(weight, available_styles, style_info):
            """Produce a styled font sample for a given weight/style.
            The style aliases returned by LilyPond are somewhat inconsistent
            and don't always match a font style that PyQt can get, so we
            have to do the lookup in the available styles reported by
            QFontDatabase (as passed in the available_styles argument."""
            font = QFont(weight)
            reported_styles = style_info.split(',')
            if not available_styles:
                # In some cases Qt does *not* report available styles.
                # In these cases it seems correct to use the style reported
                # by LilyPond. In very rare cases it seems possible that
                # LilyPond reports multiple styles for such fonts, and for Now
                # we have to simply ignore these cases so we take the first
                # or single style.
                font.setStyleName(reported_styles[0])
            else:
                # Match LilyPond's reported styles with those reported by Qt
                for style in reported_styles:
                    if style in available_styles:
                        font.setStyleName(style)
            item = QStandardItem(_('The quick brown fox jumps over the lazy dog'))
            item.setFont(font)
            return item

        font_db = QFontDatabase()
        self.initTreeModel()
        root = self.treeModel.invisibleRootItem()
        for name in available_fonts.family_names():
            family = available_fonts.font_families()[name]
            family_item = QStandardItem(name)
            root.appendRow(family_item)
            for series in sorted(family.keys()):
                shapes = font_db.styles(series)
                if len(family[series]) == 1:
                    family_item.appendRow(
                        [QStandardItem(series),
                        sample(series, shapes, family[series][0])])
                else:
                    series_item = QStandardItem(series)
                    family_item.appendRow(series_item)
                    for shape in family[series]:
                        series_item.appendRow(
                            [QStandardItem(shape),
                            sample(series, shapes, shape)])


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
        self.log.clear()
        available_fonts.load_fonts(self.lilypond_info, self.log)


    def update_filter(self):
        """Filter font results"""
        self.filter_re = re = self.filterEdit.text()
        self.filter.setPattern(re)
        self.proxy.setFilterRegExp(self.filter)
