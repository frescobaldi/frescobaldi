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
Frescobaldi "Generated Files" menu.
"""


import os

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QMenu

import app
import icons
import util
import qutil


class Menu(QMenu):
    def __init__(self, mainwindow):
        super(Menu, self).__init__(mainwindow)
        self.aboutToShow.connect(self.populate)
        app.jobFinished.connect(self.slotJobFinished)
        self.triggered.connect(self.actionTriggered)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Generated &Files"))

    def populate(self):
        self.clear()
        doc = self.parentWidget().currentDocument()
        if doc:
            import resultfiles
            files = resultfiles.results(doc).files()
            first = True
            for group in util.group_files(files,
                    ('pdf', 'mid midi', 'svg svgz', 'png', '!ly ily lyi')):
                if group:
                    if not first:
                        self.addSeparator()
                    first = False
                    for f in group:
                        name = os.path.split(f)[1]
                        a = self.addAction(name)
                        a.setIcon(icons.file_type(f))
                        a.filename = f
            if not self.actions():
                a = self.addAction(_("No files available"))
                a.setEnabled(False)
            else:
                qutil.addAccelerators(self.actions())

    def actionTriggered(self, action):
        import helpers
        helpers.openUrl(QUrl.fromLocalFile(action.filename))

    def slotJobFinished(self, doc):
        if self.isVisible() and doc == self.parentWidget().currentDocument():
            self.populate()


