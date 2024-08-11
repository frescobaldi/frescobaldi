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

from PyQt6.QtCore import (
    QByteArray,
    QSettings,
    Qt
)
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import app
import fonts
import userguide
import widgets.dialog

from . import (
    fontcommand,
    musicfonts,
    preview,
    textfonts
)


_default_fonts = {
    'music': 'emmentaler',
    'brace': 'emmentaler',
    'roman': 'TeXGyre Schola',
    'sans': 'TeXGyre Heros',
    'typewriter': 'TeXGyre Cursor'
}


class FontsDialog(QDialog):
    """Dialog to show available fonts"""

    _selected_fonts = {
        'music': _default_fonts['music'],
        'brace': _default_fonts['brace'],
        'roman': _default_fonts['roman'],
        'sans': _default_fonts['sans'],
        'typewriter': _default_fonts['typewriter']
    }

    def __init__(
        self,
        parent,
        lilypond_info=None,
        show_music=True
    ):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        super().__init__(
            parent,
        )
        self.info = lilypond_info
        if not lilypond_info:
            import documentinfo
            self.info = documentinfo.lilyinfo(parent.currentDocument())

        self.result = ''
        self.available_fonts = fonts.available(self.info)

        # Notation fonts (and preview) are limited to LilyPond >= 2.19.12
        # At some point we may remove the old dialog altogether
        # and instead make this dialog behave differently
        # (i.e. hide the music font stuff and use old font selection code)
        # self.show_music = self.info.version() >= (2, 19, 12).
        # For now this distinction is made by the action and simply
        # the dialog to be used is chosen. At some point the old
        # "Set document fonts" dialog should be dropped.
        #
        # Also, it may at some point be indicated to make this
        # dialog usable to *only* choose text fonts, e.g. from
        # the "Fonts & Colors" Preference page.
        #
        # NOTE: All facilities that *seemed* to support this functionality
        # have been removed to avoid confusion.
        self.show_music = show_music

        # Basic dialog attributes
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowModality(Qt.WindowType.WindowModal)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a QSplitter as main widget
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)

        # Left side layout
        self.left_column = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        self.left_column.setLayout(left_layout)
        self.splitter.addWidget(self.left_column)

        # Status area
        # TODO: Populate that widget with a QStackedLayout where
        # different widgets are shown corresponding to the visible tab.
        self.status_area = QWidget()
        left_layout.addWidget(self.status_area)

        # Create the QTabWidget for the dialog's left part
        self.tab_widget = QTabWidget()
        left_layout.addWidget(self.tab_widget)

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

        # Create the RHS score preview pane.
        self.preview_pane = preview.FontsPreviewWidget(self)
        self.splitter.addWidget(self.preview_pane)

        # Bottom area: button box
        self._button_box = bb = QDialogButtonBox()
        layout.addWidget(bb)
        self.restore_button = bb.addButton(QDialogButtonBox.StandardButton.RestoreDefaults)
        self.copy_button = bb.addButton(QDialogButtonBox.StandardButton.Save)
        self.insert_button = bb.addButton(QDialogButtonBox.StandardButton.Ok)
        self.close_button = bb.addButton(QDialogButtonBox.StandardButton.Close)
        # Add and connect help button
        userguide.addButton(self._button_box, "documentfonts")

        app.translateUI(self)
        self.loadSettings()
        self.connectSignals()

        # Trigger the generation of a preview
        self.invalidate_command()

    def connectSignals(self):
        self.finished.connect(self.saveSettings)
        self.restore_button.clicked.connect(self.restore)
        self.copy_button.clicked.connect(self.copy_result)
        self.insert_button.clicked.connect(self.insert_result)
        self.close_button.clicked.connect(self.close)

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
        s.beginGroup('document-fonts-dialog')

        self.select_font('music', s.value('music-font', 'emmentaler', str))
        self.select_font('brace', s.value('brace-font', 'emmentaler', str))
        self.select_font('roman', s.value('roman-font', 'TeXGyre Schola', str))
        self.select_font('sans', s.value('sans-font', 'TeXGyre Heros', str))
        self.select_font(
            'typewriter', s.value('typewriter-font', 'TeXGyre Cursor', str)
        )
        self.splitter.restoreState(
            s.value('splitter-state', QByteArray(), QByteArray)
        )

    def select_font(self, family, name):
        self._selected_fonts[family] = name

    def selected_font(self, family):
        return self._selected_fonts[family]

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('document-fonts-dialog')

        s.setValue('music-font', self.selected_font('music'))
        s.setValue('brace-font', self.selected_font('brace'))
        s.setValue('roman-font', self.selected_font('roman'))
        s.setValue('sans-font', self.selected_font('sans'))
        s.setValue('typewriter-font', self.selected_font('typewriter'))

        # Dialog layout
        s.setValue('splitter-state', self.splitter.saveState())

    def copy_result(self):
        """Copies the font command (as shown) to the clipboard."""
        from PyQt6.QtGui import QGuiApplication
        cmd = self.font_cmd()
        if cmd[-1] != '\n':
            cmd = cmd + '\n'
        QGuiApplication.clipboard().setText(cmd)
        self.accept()

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
        self.accept()

    def invalidate_command(self):
        """Triggers a regeneration of the font command and new display of the
        example (if necessary).
        """
        self.font_command_tab.invalidate_command()

    def restore(self):
        """Reset fonts to defaults"""
        for name in _default_fonts:
            self.select_font(name, _default_fonts[name])
        self.invalidate_command()

    def show_sample(self):
        """Call the preview pane to show the current sample."""
        self.preview_pane.show_sample()
