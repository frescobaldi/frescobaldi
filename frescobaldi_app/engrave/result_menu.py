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
Frescobaldi main menu.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QMenu

import app
import icons
import util


class Menu(QMenu):
    def __init__(self, mainwindow):
        super(Menu, self).__init__(mainwindow)
        self.aboutToShow.connect(self.populate)
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
            if not files:
                a = self.addAction(_("No files available"))
                a.setEnabled(False)
                return
            pdfs = []
            midis = []
            svgs = []
            pngs = []
            others = []
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext == '.pdf':
                    pdfs.append(f)
                elif ext in ('.midi', '.mid'):
                    midis.append(f)
                elif ext in ('.svg', '.svgz'):
                    svgs.append(f)
                elif ext == '.png':
                    pngs.append(f)
                elif ext not in ('.ly', '.lyi', '.ily'):
                    others.append(f)
            first = True
            for group in (pdfs, midis, svgs, pngs, others):
                if group:
                    if not first:
                        self.addSeparator()
                    first = False
                    for f in group:
                        name = os.path.split(f)[1]
                        a = self.addAction(name)
                        a.setIcon(icons.file_type(f))
                        a.filename = f
            util.addAccelerators(self.actions())
    
    def actionTriggered(self, action):
        import helpers
        helpers.openUrl(QUrl.fromLocalFile(action.filename))


