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
Show a dialog with available text and music fonts.
"""

from PyQt5.QtCore import (
    QSettings,
    Qt,
)
from PyQt5.QtWidgets import (
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import app
import log
import widgets.dialog
import fonts

from . import (
    textfonts,
    musicfonts,
    fontcommand,
    preview
)


_default_fonts = {
    'music': 'emmentaler',
    'brace': 'emmentaler',
    'roman': 'TeXGyre Schola',
    'sans': 'TeXGyre Heros',
    'typewriter': 'TeXGyre Cursor'
}


class FontsDialog(widgets.dialog.Dialog):
    """Dialog to show available fonts"""

    selected_fonts = {
        'music': _default_fonts['music'],
        'brace': _default_fonts['brace'],
        'roman': _default_fonts['roman'],
        'sans': _default_fonts['sans'],
        'typewriter': _default_fonts['typewriter']
    }

    def __init__(self, info, parent):
        super(FontsDialog, self).__init__(
            parent,
            buttons=('restoredefaults', 'help', 'save', 'ok', 'close',),
        )

        self.result = ''
        self.info = info
        self.available_fonts = fonts.available(self.info)

        # Notation fonts (and preview) are limited to LilyPond >= 2.19.12
        # At some point we may remove the old dialog altogether
        # and instead make this dialog behave differently
        # (i.e. hide the music font stuff and use old font selection code)
        # self.show_music = self.info.version() >= (2, 19, 12)
        self.show_music = True

        self.reloadButton = self._buttonBox.button(
            QDialogButtonBox.RestoreDefaults)
        self.reloadButton.setEnabled(False)
        self.copyButton = self.button('ok')
        self.insertButton = self.button('save')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.NonModal)

        self.tabWidget = QTabWidget(self)
        self.preview_pane = preview.FontsPreviewWidget(self)
        self.preview_pane.starting_up = True

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.addWidget(self.tabWidget)
        if self.show_music:
            self.splitter.addWidget(self.preview_pane)
        self.setMainWidget(self.splitter)

        app.qApp.setOverrideCursor(Qt.WaitCursor)
        self.createTabs()

        app.translateUI(self)
        self.loadSettings()

        self.connectSignals()
        if self.available_fonts.text_fonts().is_loaded():
            self.populate_widgets()
        else:
            self.tabWidget.insertTab(0, self.logTab, _("LilyPond output"))
            self.tabWidget.setCurrentIndex(0)
            self.font_tree_tab.display_waiting()
            self.available_fonts.text_fonts().load_fonts(self.logWidget)
        app.qApp.restoreOverrideCursor()
        self.preview_pane.starting_up = False
        self.font_command_tab.invalidate_command()

    def createTabs(self):

        def create_log():
            # Show original log
            self.logTab = QWidget()
            self.logWidget = log.Log(self.logTab)
            self.logLabel = QLabel()
            logLayout = QVBoxLayout()
            logLayout.addWidget(self.logLabel)
            logLayout.addWidget(self.logWidget)
            self.logTab.setLayout(logLayout)

        create_log()
        # Show Text Font results
        # (Initially don't actually show it, only after compilation)
        self.font_tree_tab = textfonts.TextFontsWidget(self)

        if self.show_music:
            # Show installed notation fonts
            self.music_tree_tab = (
                musicfonts.MusicFontsWidget(self.available_fonts, self)
            )
            self.tabWidget.addTab(self.music_tree_tab, _("Music Fonts"))

        # Configure the resulting font command
        self.font_command_tab = fontcommand.FontCommandWidget(self)
        self.font_command_tab.invalidate_command()
        self.tabWidget.addTab(self.font_command_tab, _("Font Command"))

        # Show various fontconfig information
        self.misc_tree_tab = textfonts.MiscFontsInfoWidget(self.available_fonts)
        self.tabWidget.addTab(self.misc_tree_tab, _("Miscellaneous"))

    def connectSignals(self):
        self.available_fonts.text_fonts().loaded.connect(self.text_fonts_loaded)
        self.finished.connect(self.saveSettings)
        self.reloadButton.clicked.connect(self.reload)
        self.copyButton.clicked.connect(self.copy_result)
        self.insertButton.clicked.connect(self.insert_result)
        if self.show_music:
            mtt = self.music_tree_tab
            mtt.button_install.clicked.connect(
                self.install_music_fonts)

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Document Fonts")))
        self.reloadButton.setText(_("&Reload"))
        self.copyButton.setText(_("&Copy"))
        self.copyButton.setToolTip(_("Copy font command to clipboard"))
        self.insertButton.setText(_("&Use"))
        self.insertButton.setToolTip(
            _("Insert font command at the current cursor position")
        )
        self.logLabel.setText(_("LilyPond output of -dshow-available-options"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')

        # Text font tab
        self.load_font_tree_column_width(s)

        fonts = self.selected_fonts

        # Preview
        if self.show_music:
            self.preview_pane.loadSettings()
            fonts['music'] = s.value('music-font', 'emmentaler', str)
            fonts['brace'] = s.value('brace-font', 'emmentaler', str)
        fonts['roman'] = s.value('roman-font', 'TeXGyre Schola', str)
        fonts['sans'] = s.value('sans-font', 'TeXGyre Heros', str)
        fonts['typewriter'] = s.value('typewriter-font', 'TeXGyre Cursor', str)

        # Music font tab
        # TODO: The following doesn't work so we can't restore
        # the layout of the splitter yet.
#        self.musicFontsSplitter.restoreState(
#            s.value('music-font-splitter-sizes').toByteArray()
#        )

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')

        # Text font tab
        s.setValue('col-width', self.font_tree_tab.tree_view.columnWidth(0))

        fonts = self.selected_fonts
        # Preview
        if self.show_music:
            self.preview_pane.saveSettings()
            s.setValue('music-font', fonts['music'])
            s.setValue('brace-font', fonts['brace'])
        s.setValue('roman-font', fonts['roman'])
        s.setValue('sans-font', fonts['sans'])
        s.setValue('typewriter-font', fonts['typewriter'])

        # Dialog layout
        s.setValue('music-fonts-splitter-sizes', self.splitter.saveState())

    def copy_result(self):
        """Copies the font command (as shown) to the clipboard."""
        from PyQt5.QtGui import QGuiApplication
        cmd = self.font_cmd()
        if cmd[-1] != '\n':
            cmd = cmd + '\n'
        QGuiApplication.clipboard().setText(cmd)

    def font_cmd(self, approach=None):
        """Return the font setting command as shown in the Font Command tab."""
        approach = approach or self.font_command_tab.approach
        return self.font_command_tab.command(approach)

    def font_full_cmd(self, approach=None):
        """Return the "full" command with all properties/fonts."""
        approach = approach or self.font_command_tab.approach
        return self.font_command_tab.full_cmd(approach)

    def insert_result(self):
        """Inserts the font command (as shown) at the current position"""
        self.result = self.font_cmd()

    def install_music_fonts(self):
        """'Install' music fonts from a directory (structure) by
        linking fonts into the LilyPond installation's font
        directories (otf and svg)."""

        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.Directory)
        if not dlg.exec():
            return

        installed = self.available_fonts.music_fonts()
        root_dir = dlg.selectedFiles()[0]
        from . import musicfonts
        repo = musicfonts.MusicFontRepo(root_dir)
        repo.flag_for_install(installed)

        # QUESTION: Do we need a message dialog to confirm/cancel installation?
        # repo.installable_fonts.item_model() is an item model like the one
        # we use for the music font display, but contains only the installable
        # font entries.

        try:
            repo.install_flagged(installed)
        except musicfonts.MusicFontPermissionException as e:
            msg_box = QMessageBox()
            msg_box.setText(_("Fonts could not be installed!"))
            msg_box.setInformativeText(
            _("Installing fonts in the LilyPond installation " +
              "appears to require administrator privileges on " +
              "your system and can unfortunately not be handled " +
              "by Frescobaldi,"))
            msg_box.setDetailedText("{}".format(e))
            msg_box.exec()

    def load_font_tree_column_width(self, s):
        """Load column widths for fontTreeView,
        factored out because it has to be done upon reload too."""
        self.font_tree_tab.tree_view.setColumnWidth(0, int(s.value('col-width', 200)))

    def populate_widgets(self):
        """Populate widgets."""
        self.tabWidget.insertTab(0, self.font_tree_tab, _("Text Fonts"))
        self.tabWidget.setCurrentIndex(0)
        self.load_font_tree_column_width(QSettings())
        self.font_tree_tab.display_count()
        self.font_tree_tab.refresh_filter_edit()
        self.font_tree_tab.filter_edit.setFocus()
        self.reloadButton.setEnabled(True)

    def reload(self):
        """Refresh font list by running LilyPond"""
        self.tabWidget.removeTab(0)
        self.tabWidget.insertTab(0, self.logTab, _("LilyPond output"))
        self.tabWidget.setCurrentIndex(0)
        self.logWidget.clear()
        # We're connected to the 'loaded' signal
        self.available_fonts.text_fonts().load_fonts(self.logWidget)

    def text_fonts_loaded(self):
        """We don't want to keep the LilyPond log open."""
        self.tabWidget.removeTab(0)
        self.populate_widgets()
