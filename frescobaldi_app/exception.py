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
Exception dialog for unhandled Python exceptions
(which are bugs in our program).
"""


import traceback

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QTextBrowser, QVBoxLayout)

import app
import icons
import widgets
import bugreport


class ExceptionDialog(QDialog):
    """Single-use dialog displaying a Python exception."""
    def __init__(self, exctype, excvalue, exctb):
        super(ExceptionDialog, self).__init__()

        self._tbshort = ''.join(traceback.format_exception_only(exctype, excvalue))
        tbfull = traceback.format_exception(exctype, excvalue, exctb)
        self._tbfull = ''.join(tbfull)
        self._ext_maintainer = app.extensions().is_extension_exception(tbfull)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.errorLabel = QLabel()
        layout.addWidget(self.errorLabel)
        textview = QTextBrowser()
        layout.addWidget(textview)
        textview.setText(self._tbfull)
        textview.moveCursor(QTextCursor.End)

        layout.addWidget(widgets.Separator())

        b = self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.button(QDialogButtonBox.Ok).setIcon(icons.get("tools-report-bug"))
        layout.addWidget(b)

        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        self.resize(600,300)
        app.translateUI(self)
        self.exec_()

    def translateUI(self):
        if self._ext_maintainer:
            extension = self._ext_maintainer[0]
            text = _("An internal error has occurred in extension '{name}':").format(name=extension)
            title = _("Extension Error")
        else:
            text = _("An internal error has occurred:")
            title = _("Internal Error")
        self.setWindowTitle(app.caption(title))
        self.errorLabel.setText(text)
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Send Bug Report..."))

    def done(self, result):
        if result:
            self.reportBug()
        super(ExceptionDialog, self).done(result)

    def reportBug(self):
        if self._ext_maintainer:
            # For now extensions don't have a way to use a custom bug reporting
            # method, we use email.
            extension = self._ext_maintainer[0]
            rcpt = self._ext_maintainer[1]
            ext_intro = '\n{}\n\n'.format(
                _("An error occurred in extension '{name}'").format(name=extension))
            ext_header = ' [{}]'.format(self._ext_maintainer[0])
            bugreport.email(
                self._tbshort + ext_header,
                ext_intro + self._tbfull + '\n'
                + _("Optionally describe below what you were doing:"),
                recipient=rcpt)
        else:
            bugreport.new_github_issue(
                title=self._tbshort,
                body=(self._tbfull + '\n'
                      + _("Optionally describe below what you were doing:")))
