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

from PyQt5.QtCore import QSize, Qt, QSortFilterProxyModel, QRegExp
from PyQt5.QtWidgets import (
    QLabel, QWidget, QLineEdit, QVBoxLayout, QTabWidget, QTextEdit,
    QTreeView
)
from PyQt5.QtGui import(
    QStandardItemModel, QStandardItem
)


import app
import job
import log
import qutil
import widgets.dialog




def show_available_fonts(mainwin, info):
    """Display a dialog with the available fonts of LilyPond specified by info."""
    dlg = ShowFontsDialog(mainwin, info)
    dlg.setWindowTitle(app.caption(_("Available Fonts")))
    dlg.run_command(info, ['-dshow-available-fonts'], _("Available Fonts"))
    qutil.saveDialogSize(dlg, "engrave/tools/available-fonts/dialog/size", QSize(640, 400))
    dlg.setAttribute(Qt.WA_DeleteOnClose)
    dlg.show()


class ShowFontsDialog(widgets.dialog.Dialog):
    """Dialog to show available fonts)"""

    def __init__(self, parent, info):
        super(ShowFontsDialog, self).__init__(
            parent,
            #TODO: Add buttons to export/copy/print
            buttons=('close',),
        )
        self.info = info
        self.setWindowModality(Qt.NonModal)

        self.tabWidget = QTabWidget(self)
        self.setMainWidget(self.tabWidget)

        self.msgLabel = QLabel()
        self.filterEdit = QLineEdit()
        self.filterEdit.setPlaceholderText(_("Filter results (type any part of the font family name)"))

        self.logWidget = QWidget()
        self.log = log.Log(self.logWidget)
        logLayout = QVBoxLayout()
        logLayout.addWidget(self.log)
        self.logWidget.setLayout(logLayout)
        self.tabWidget.addTab(self.logWidget, _("LilyPond output"))

        # Show Font results
        self.fontTreeWidget = QWidget()
        self.fontTree = QTreeView(self.fontTreeWidget)
        self.fontTree.setHeaderHidden(True)
        treeLayout =QVBoxLayout()
        treeLayout.addWidget(self.msgLabel)
        treeLayout.addWidget(self.fontTree)
        treeLayout.addWidget(self.filterEdit)
        self.fontTreeWidget.setLayout(treeLayout)
        self.tabWidget.addTab(self.fontTreeWidget, _("Fonts"))

        self.treeModel = QStandardItemModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.treeModel)
        self.fontTree.setModel(self.proxy)
        self.filterEdit.textChanged.connect(self.update_filter)
        self.filter = QRegExp('', Qt.CaseInsensitive)

        # Widget to show config files
        self.configFilesWidget = QWidget()
        self.configFilesEdit = QTextEdit(self.configFilesWidget)
        config_layout = QVBoxLayout()
        config_layout.addWidget(self.configFilesEdit)
        self.configFilesWidget.setLayout(config_layout)
        self.tabWidget.addTab(self.configFilesWidget, _("Config Files"))

        # Widget to show font directories
        self.fontDirWidget = QWidget()
        self.fontDirEdit = QTextEdit(self.fontDirWidget)
        font_dir_layout = QVBoxLayout()
        font_dir_layout.addWidget(self.fontDirEdit)
        self.fontDirWidget.setLayout(font_dir_layout)
        self.tabWidget.addTab(self.fontDirWidget, _("Font Directories"))


    def populate_model(self):
        """Populate the data model to be displayed in the results"""
        root = self.treeModel.invisibleRootItem()
        for name in self.names:
            family = self.families[name]
            if ((len(family.keys()) == 1) and
                (name in family.keys()) and
                (len(family[name]) == 1)):
                # Single family, only one style
                content = '{} ({})'.format(name, family[name][0])
                root.appendRow(QStandardItem(content))
            elif (len(family.keys()) == 1) and (name in family.keys()):
                # Single family, multiple styles
                family_item = QStandardItem(name)
                root.appendRow(family_item)
                for style in sorted(family[name]):
                    family_item.appendRow(QStandardItem(style))
            else:
                # Multiple family (e.g. XX, XX Cond, XX Ext)
                family_item = QStandardItem(name)
                root.appendRow(family_item)
                for weight in sorted(family.keys()):
                    if len(family[weight]) == 1:
                        # One style for the weight
                        family_item.appendRow(
                            QStandardItem(
                                '{} ({})'.format(weight,family[weight][0])))
                    else:
                        # Multiple styles for the weight
                        weight_item = QStandardItem(weight)
                        family_item.appendRow(weight_item)
                        for style in family[weight]:
                            weight_item.appendRow(QStandardItem(style))


    def run_command(self, info, args, title=None):
        """Run lilypond from info with the args list, and a job title."""
        j = self.job = job.Job()
        j.done.connect(self.show_fonts)
        #TODO: Handle errors
        j.decode_errors = 'replace'
        j.decoder_stdout = j.decoder_stderr = codecs.getdecoder('utf-8')
        j.command = [info.abscommand() or info.command] + list(args)
        if title:
            j.set_title(title)
        self.msgLabel.setText(_("Running LilyPond to list fonts ..."))
        self.log.connectJob(j)
        j.start()


    def read_entries(self):
        """Parse the job history list to dictionaries."""
        self.families = {}
        self.names = []
        self.config_files = []
        self.config_dirs = []
        self.font_dirs = []
        entries = []

        # Process job history into flat string list
        for line in self.job.history():
            lines = line[0].split('\n')
            for l in lines:
                entries.append(l)

        # Parse entries in the string file_insert_file
        last_family = None
        for e in entries:
            if e.startswith('family'):
                last_family = e[7:]
                if not last_family in self.families.keys():
                    self.families[last_family] = {}
            elif last_family:
                self.update_family(last_family, e)
                last_family = None
            elif e.startswith('Config files:'):
                self.config_files.append(e[14:])
            elif e.startswith('Font dir:'):
                self.font_dirs.append(e[10:])
            elif e.startswith('Config dir:'):
                self.config_dirs.append(e[12:])

        # Store sorted reference lists.
        self.names = sorted(self.families.keys(), key=lambda s: s.lower())
        self.config_files = sorted(self.config_files, key=lambda s: s.lower())
        self.config_dirs = sorted(self.config_dirs, key=lambda s: s.lower())
        self.font_dirs = sorted(self.font_dirs, key=lambda s: s.lower())


    def show_fonts(self):
        """Populate widget and show results."""
        self.read_entries()
        self.msgLabel.setText(
            _("{count} font families detected by {version}").format(
                count=len(self.names),
                version=self.info.prettyName()))
        self.populate_model()

        # Display config files and directories
        title = '<p><b>{}</b></p>'.format(_("Config Directories:"))
        dirs = '<p>{}</p>'.format(
            '\n'.join(['{}<br />'.format(file) for file in self.config_dirs]))
        files_title = '<p><b>{}</b></p>'.format(_("Config Files:"))
        files = '<p>{}</p></body></html>'.format(
            '\n'.join(['{}<br />'.format(file) for file in self.config_files]))
        config_html = '<html><body>{}{}{}{}</body></html>'.format(
            title, dirs, files_title, files)
        self.configFilesEdit.setHtml(config_html)

        # Display font directories
        font_dir_html = '<html><body><p>{}</p></body></html>'.format(
            '\n'.join(['{}<br />'.format(file) for file in self.font_dirs]))
        self.fontDirEdit.setHtml(font_dir_html)
        self.tabWidget.setCurrentIndex(1)
        self.filterEdit.setFocus()


    def update_family(self, family_name, input):
        """Parse a font family definition."""
        family = self.families[family_name]
        input = input.strip().split(':')
        if len(input) == 2:
            names = input[0].split(',')
            if not names[-1] in family.keys():
                family[names[-1]] = []
            family[names[-1]].append(input[1][6:])


    def update_filter(self):
        """Filter font results"""
        self.filter.setPattern(self.filterEdit.text())
        self.proxy.setFilterRegExp(self.filter)
