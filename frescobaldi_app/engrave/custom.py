# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Custom engraving dialog.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import help
import icons
import widgets
import util


class Dialog(QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        self.versionLabel = QLabel()
        self.versionCombo = QComboBox()
        
        self.outputLabel = QLabel()
        self.outputCombo = QComboBox()
        
        self.previewCheck = QCheckBox()
        self.verboseCheck = QCheckBox()
        
        self.commandLineLabel = QLabel()
        self.commandLine = QTextEdit()
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setIcon(icons.get("lilypond-run"))
        help.addButton(self.buttons, help_engrave_custom)
        
        layout.addWidget(self.versionLabel, 0, 0)
        layout.addWidget(self.versionCombo, 0, 1)
        layout.addWidget(self.outputLabel, 1, 0)
        layout.addWidget(self.outputCombo, 1, 1)
        layout.addWidget(self.previewCheck, 2, 0, 1, 2)
        layout.addWidget(self.verboseCheck, 3, 0, 1, 2)
        layout.addWidget(self.commandLineLabel, 4, 0, 1, 2)
        layout.addWidget(self.commandLine, 5, 0, 1, 2)
        layout.addWidget(widgets.Separator(), 6, 0, 1, 2)
        layout.addWidget(self.buttons, 7, 0, 1, 2)
        
        app.translateUI(self)
        util.saveDialogSize(self, "engrave/custom/dialog/size", QSize(480, 260))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Engrave custom")))
        self.versionLabel.setText(_("LilyPond Version:"))
        self.outputLabel.setText(_("Output Format:"))
        self.previewCheck.setText(_(
            "Run LilyPond in preview mode (with Point and Click)"))
        self.verboseCheck.setText(_("Run LilyPond with verbose output"))
        self.commandLineLabel.setText(_("Command line:"))
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run LilyPond"))
    



class help_engrave_custom(help.page):
    def title():
        return _("Engrave custom")
    
    def body():
        p = '<p>{0}</p>\n'.format
        text = [p(_("""\
In this dialog you can set some parameters for the LilyPond command to be used
to engrave your document.
It is even possible to edit the command line itself.
"""))]
        text.append(p(_("The following replacements will be made:")))
        text.append('<dl>\n')
        for name, msg in (
            ('${lilypond}', _("The LilyPond executable")),
            ('${filename}', _("The filename of the document")),
            ('$$', _("A literal $ character")),
            ):
            text.append('<dt><code>{0}</code></dt>'.format(name))
            text.append('<dd>{0}</dd>\n'.format(msg))
        text.append('</dl>')
        return ''.join(text)


