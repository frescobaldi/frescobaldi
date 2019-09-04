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

# Tab widget for the configuration of the font setting command

from PyQt5.QtCore import (
    QSettings,
)
from PyQt5.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import app


class FontCommandWidget(QWidget):
    """Displays and manipulates a font setting command."""

    def __init__(self, parent):
        super(FontCommandWidget, self).__init__(parent)
        self.dialog = parent
        layout = QVBoxLayout()
        self.setLayout(layout)
        col_layout = QHBoxLayout()
        layout.addLayout(col_layout)
        layout.addStretch()

        # Left column holding the options
        self.option_widget = QWidget()
        opt_layout = QVBoxLayout()
        self.option_widget.setLayout(opt_layout)
        col_layout.addWidget(self.option_widget)

        # TextEdit to display the generated command
        self.command_edit = ce = QTextEdit()
        ce.setReadOnly(True)
        ce.setEnabled(False)
        col_layout.addWidget(self.command_edit)

        # Which text font families to integrate?
        self.family_group = QGroupBox()
        family_layout = QVBoxLayout()
        opt_layout.addWidget(self.family_group)
        self.family_group.setLayout(family_layout)
        self.cb_roman = QCheckBox()
        family_layout.addWidget(self.cb_roman)
        self.cb_sans = QCheckBox()
        family_layout.addWidget(self.cb_sans)
        self.cb_typewriter = QCheckBox()
        family_layout.addWidget(self.cb_typewriter)

        # Choice between traditional and openLilyLib approach
        self.approach_group = QGroupBox()
        approach_layout = QVBoxLayout()
        self.approach_group.setLayout(approach_layout)
        self.approach_tab = QTabWidget()
        approach_layout.addWidget(self.approach_tab)
        opt_layout.addWidget(self.approach_group)

        self.trad_widget = QWidget()
        trad_layout = QVBoxLayout()
        self.trad_widget.setLayout(trad_layout)
        self.approach_tab.addTab(self.trad_widget, "")

        self.oll_widget = QWidget()
        oll_layout = QVBoxLayout()
        self.oll_widget.setLayout(oll_layout)
        self.approach_tab.addTab(self.oll_widget, "")

        # Configure traditional approach
        self.cb_music = QCheckBox()
        trad_layout.addWidget(self.cb_music)
        self.cb_paper_block = QCheckBox()
        trad_layout.addWidget(self.cb_paper_block)
        trad_layout.addStretch()

        # Configure openLilyLib approach
        self.cb_oll_music = QCheckBox()
        self.cb_oll_music.setChecked(True)
        self.cb_oll_music.setEnabled(False)
        oll_layout.addWidget(self.cb_oll_music)
        self.cb_oll = QCheckBox()
        oll_layout.addWidget(self.cb_oll)
        self.cb_loadpackage = QCheckBox()
        oll_layout.addWidget(self.cb_loadpackage)
        self.cb_extensions = QCheckBox()
        oll_layout.addWidget(self.cb_extensions)
        # Configure handling of stylesheet
        self.stylesheet_group = QGroupBox()
        self.stylesheet_buttons = QButtonGroup()
        oll_layout.addWidget(self.stylesheet_group)
        stylesheet_layout = QVBoxLayout()
        self.stylesheet_group.setLayout(stylesheet_layout)
        self.style_buttons = [QRadioButton() for i in range(3)]
        for i in range(3):
            b = self.style_buttons[i]
            stylesheet_layout.addWidget(b)
            self.stylesheet_buttons.addButton(b)
            self.stylesheet_buttons.setId(b, i)
        self.le_stylesheet = QLineEdit()
        stylesheet_layout.addWidget(self.le_stylesheet)
        oll_layout.addStretch()

        # enable line edit when custom stylesheet is selected
        self.stylesheet_buttons.buttonClicked.connect(
            lambda: self.le_stylesheet.setEnabled(
                self.stylesheet_buttons.checkedId() == 2
            )
        )

        self.loadSettings()
        self.dialog.finished.connect(self.saveSettings)
        # Connect widgets that trigger re-generation of the command
        signal_map = {
            QAbstractButton: 'toggled',
            QButtonGroup: 'buttonClicked',
            QTabWidget: 'currentChanged',
            QLineEdit: 'editingFinished'
        }
        for w in [
            self.cb_roman,
            self.cb_sans,
            self.cb_typewriter,
            self.approach_tab,
            self.cb_music,
            self.cb_paper_block,
            self.cb_oll,
            self.cb_loadpackage,
            self.cb_extensions,
            self.stylesheet_buttons,
            self.le_stylesheet
        ]:
            for base_class in signal_map:
                if isinstance(w, base_class):
                    signal = getattr(w, signal_map[base_class])
                    signal.connect(self.generate_command)
                    break

        app.translateUI(self)

    def translateUI(self):
        self.family_group.setTitle(_("Set font families"))
        self.cb_roman.setText(_("Roman"))
        self.cb_sans.setText(_("Sans"))
        self.cb_typewriter.setText(_("Typewriter"))

        self.approach_group.setTitle(_("Configure command generation"))
        self.approach_tab.setTabText(0, _("Traditional"))
        self.approach_tab.setTabToolTip(0, _(
            "Specify fonts using the setting in a \\paper block."
        ))
        self.approach_tab.setTabText(1, _("openLilyLib"))
        self.approach_tab.setTabToolTip(1, _(
            "Specify fonts using the setting using openLilyLib.\n"
            + "NOTE: This requires openLilyLib (oll-core)\n"
            + "and the 'notation-fonts' openLilyLib package."
        ))

        self.cb_music.setText(_("Set music font"))
        self.cb_paper_block.setText(_("Complete \\paper block"))
        self.cb_paper_block.setToolTip(_(
            "Wrap setting in a complete \\paper block.\n"
            + "If unchecked generate the raw font setting command."
        ))

        self.cb_oll_music.setText(_("Set music font"))
        self.cb_oll_music.setToolTip(_(
            "Specify the music font.\n"
            + "This is a reminder only and can not be unckecked "
            + "because the openLilyLib approach necessarily sets "
            + "the music font."
        ))
        self.cb_oll.setText(_("Load openLilyLib"))
        self.cb_oll.setToolTip(_(
            "Load openLilyLib (oll-core) explicitly.\n"
            + "Unckeck if oll-core is already loaded elsewhere."
        ))
        self.cb_loadpackage.setText(_("Load notation-fonts package"))
        self.cb_loadpackage.setToolTip(_(
            "Load the notation-fonts package explicitly.\n"
            + "Unckeck if it is already loaded elsewhere."
        ))
        self.cb_extensions.setText(_("Load font extensions (if available)"))
        self.cb_extensions.setToolTip(_(
            "Ask for loading font extensions.\n"
            + "Note that *some* fonts provide additional features\n"
            + "(e.g. glyphs) that can be made available through an\n"
            + "extension stylesheet if provided."
        ))
        self.stylesheet_group.setTitle(_("Font stylesheet"))
        self.stylesheet_group.setToolTip(_(
            "Select alternative stylesheet.\n"
            + "Fonts natively supported by the notation-fonts\n"
            + "package provide a default stylesheet to adjust\n"
            + "LilyPond's visuals (e.g. line thicknesses) to the\n"
            + "characteristic of the music font.\n"
            + "Check 'No stylesheet' to avoid a preconfigured\n"
            + "stylesheet to customize the appearance manually,\n"
            + "or check 'Custom stylesheet' to load another stylesheet\n"
            + "in LilyPond's search path."
        ))
        self.style_buttons[0].setText(_("Default stylesheet"))
        self.style_buttons[1].setText(_("No stylesheet"))
        self.style_buttons[2].setText(_("Custom stylesheet"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        self.cb_roman.setChecked(s.value('set-roman', False, bool))
        self.cb_sans.setChecked(s.value('set-sans', False, bool))
        self.cb_roman.setChecked(s.value('set-roman', False, bool))
        self.approach_tab.setCurrentIndex(s.value('approach-index', 0, int))
        self.cb_music.setChecked(s.value('set-music', True, bool))
        self.cb_paper_block.setChecked(s.value('set-paper-block', True, bool))
        self.cb_oll.setChecked(s.value('load-oll', True, bool))
        self.cb_loadpackage.setChecked(s.value('load-package', True, bool))
        self.cb_extensions.setChecked(s.value('font-extensions', False, bool))
        style_type = s.value('style-type', 0, int)
        self.style_buttons[style_type].setChecked(True)
        self.le_stylesheet.setText(s.value('font-stylesheet', '', str))
        self.le_stylesheet.setEnabled(self.style_buttons[2].isChecked())

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('available-fonts-dialog')
        s.setValue('set-roman', self.cb_roman.isChecked())
        s.setValue('set-sans', self.cb_sans.isChecked())
        s.setValue('set-roman', self.cb_roman.isChecked())
        s.setValue('approach-index', self.approach_tab.currentIndex())
        s.setValue('set-music', self.cb_music.isChecked())
        s.setValue('set-paper-block', self.cb_paper_block.isChecked())
        s.setValue('load-oll', self.cb_oll.isChecked())
        s.setValue('load-package', self.cb_loadpackage.isChecked())
        s.setValue('font-extensions', self.cb_extensions.isChecked())
        s.setValue('style-type', self.stylesheet_buttons.checkedId())
        s.setValue('font-stylesheet', self.le_stylesheet.text())

    def generate_command(self, _=None):
        pass
