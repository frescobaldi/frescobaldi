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
Exception dialog for unhandled Python exceptions
(which are bugs in our program).
"""

from __future__ import unicode_literals

import traceback

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import (
    QDesktopServices, QDialog, QDialogButtonBox, QLabel, QTextBrowser,
    QTextCursor, QVBoxLayout)

import app
import icons
import info
import widgets


class ExceptionDialog(QDialog):
    """Single-use dialog displaying a Python exception."""
    def __init__(self, exctype, excvalue, exctb):
        super(ExceptionDialog, self).__init__()
        
        self._tbshort = ''.join(traceback.format_exception_only(exctype, excvalue))
        self._tbfull = ''.join(traceback.format_exception(exctype, excvalue, exctb))
 
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
        self.errorLabel.setText(_("An internal error has occurred:"))
        self.setWindowTitle(app.caption(_("Internal Error")))
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Email Bug Report..."))

    def done(self, result):
        if result:
           self.reportBug()
        super(ExceptionDialog, self).done(result)
        
    def reportBug(self):
        subject = u"[{0} {1}] {2}".format(info.appname, info.version, self._tbshort)
        body = u"{0}: {1}\n\n{2}\n\n{3}\n{4}\n\n".format(
            info.appname, info.version, versionInfo(), self._tbfull,
            _("Optionally describe below what you were doing:"))
        
        url = QUrl("mailto:" + info.maintainer_email)
        url.addQueryItem("subject", subject)
        url.addQueryItem("body", body)
        QDesktopServices.openUrl(url)


def versionInfo():
    """Returns terse version and platform information as a human-readable string for debugging purposes."""
    try:
        import sip
        sip_version = sip.SIP_VERSION_STR
    except (ImportError, NameError):
        sip_version = "unknown"
    
    try:
        import PyQt4.QtCore
        pyqt_version = PyQt4.QtCore.PYQT_VERSION_STR
    except (ImportError, NameError):
        pyqt_version = "unknown"
    
    try:
        qt_version = PyQt4.QtCore.QT_VERSION_STR
    except NameError:
        qt_version = "unknown"
    
    try:
        import platform
        python_version = platform.python_version()
        osname = platform.platform()
    except (ImportError, NameError):
        python_version = "unknown"
        osname = "unknown"
    
    return (
        "Python: {python_version} -- "
        "Qt: {qt_version} -- "
        "PyQt4: {pyqt_version} -- "
        "sip: {sip_version}\n"
        "OS: {osname}".format(**locals()))


