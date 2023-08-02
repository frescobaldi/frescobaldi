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
A QWidget showing a "could not load PyQtWebEngine" message.
"""


import platform

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QLayout, QVBoxLayout, QWidget

import app


class WebEngineDummy(QWidget):
    def __init__(self, dockwidget):
        super(WebEngineDummy, self).__init__(dockwidget)
        self._msg = QLabel(openExternalLinks = True)
        self._msg.setTextFormat(Qt.RichText)
        self._msg.setWordWrap(True)
        # take into account docbrowser.HelpBrowser.activate()
        self.webview = self._msg
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self._msg)
        app.translateUI(self)

    def translateUI(self):
        message = (_("<b>Could not load PyQtWebEngine, "
                     + "so the {tool} cannot be loaded.</b>").format(
                     tool = self.parentWidget().windowTitle()))
        if platform.system() == "Darwin":
            import macosx
            if (macosx.inside_app_bundle()
                    and not macosx.inside_lightweight_app_bundle()):
                message = (
                    message + "<br><br>"
                    + _("PyQtWebEngine has been intentionally excluded from "
                        + "the application bundle: at the moment, including "
                        + "it results in a faulty application.<br><br>"
                        + "For more details, see <a href=\"{issue}\">issue #1244</a> "
                        + "on Frescobaldi's GitHub page.<br>"
                        + "For more information on alternative ways of running "
                        + "Frescobaldi, see the <a href=\"{wiki}\">relevant Wiki "
                        + "page</a> on GitHub.").format(
                        issue = "https://github.com/frescobaldi/frescobaldi/issues/1244",
                        wiki = "https://github.com/frescobaldi/frescobaldi/"
                               + "wiki/How-to-install-Frescobaldi-on-Mac-OS-X"))
        self._msg.setText(message)
