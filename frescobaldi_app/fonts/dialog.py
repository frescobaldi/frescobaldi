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
    QSplitter,
    QTabWidget,
)

import app
import widgets.dialog
import fonts
import userguide

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
        app.qApp.setOverrideCursor(Qt.WaitCursor)
        super(FontsDialog, self).__init__(
            parent,
            buttons=('restoredefaults', 'save', 'ok', 'close')
        )

        self.result = ''
        self.info = info
        self.available_fonts = fonts.available(self.info)

        # Notation fonts (and preview) are limited to LilyPond >= 2.19.12
        # At some point we may remove the old dialog altogether
        # and instead make this dialog behave differently
        # (i.e. hide the music font stuff and use old font selection code)
        # self.show_music = self.info.version() >= (2, 19, 12)
        #
        # Also, it may at some point be indicated to make this
        # dialog usable to *only* choose text fonts, e.g. from
        # the "Fonts & Colors" Preference page.
        #
        # NOTE: There are some facilities that seem to handle the state
        # of self.show_music, but in fact they do not work in any meaningful
        # fashion. They have been left in the code because they give an
        # initial idea for future development.
        self.show_music = True

        # Basic dialog attributes
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.NonModal)
        # Make buttons accessible as fields
        self.restore_button = self.button('restoredefaults')
        self.copy_button = self.button('ok')
        self.insert_button = self.button('save')
        # Add and connect help button
        userguide.addButton(self._buttonBox, "documentfonts")

        # Create a QSplitter as main widget
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.setMainWidget(self.splitter)

        # Create the Qtab_widget for the dialog's left part
        self.tab_widget = QTabWidget(self)
        self.splitter.addWidget(self.tab_widget)

        # Create the RHS score preview pane.
        self.preview_pane = preview.FontsPreviewWidget(self)
        self.splitter.addWidget(self.preview_pane)

        # Text Fonts Tab
        self.tab_widget.addTab(textfonts.TextFontsWidget(self), '')
        # Music Fonts Tab
        self.tab_widget.addTab(musicfonts.MusicFontsWidget(self), '')
        # Show/configure the generated font setting command
        self.font_command_tab = fontcommand.FontCommandWidget(self)
        self.tab_widget.addTab(self.font_command_tab, '')
        # Show various fontconfig information
        self.tab_widget.addTab(
            textfonts.MiscFontsInfoWidget(self.available_fonts), '')

        app.translateUI(self)
        self.loadSettings()
        self.connectSignals()

        self.font_command_tab.invalidate_command()

    def connectSignals(self):
        self.finished.connect(self.saveSettings)
        self.restore_button.clicked.connect(self.restore)
        self.copy_button.clicked.connect(self.copy_result)
        self.insert_button.clicked.connect(self.insert_result)

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Document Fonts")))
        self.copy_button.setText(_("&Copy"))
        self.copy_button.setToolTip(_("Copy font command to clipboard"))
        self.insert_button.setText(_("&Use"))
        self.insert_button.setToolTip(
            _("Insert font command at the current cursor position")
        )
        self.tab_widget.setTabText(0, _("Text Fonts"))
        self.tab_widget.setTabText(1, _("Music Fonts"))
        self.tab_widget.setTabText(2, _("Font Command"))
        self.tab_widget.setTabText(3, _("Miscellaneous"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')

        fonts = self.selected_fonts
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

        fonts = self.selected_fonts
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

    def restore(self):
        """Reset fonts to defaults"""
        fonts = self.selected_fonts
        for name in _default_fonts:
            fonts[name] = _default_fonts[name]
        self.font_command_tab.invalidate_command()
