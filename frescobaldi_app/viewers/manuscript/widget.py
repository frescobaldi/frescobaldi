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
The Manuscript viewer panel widget.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import userguide.util
import icons

import viewers

class Widget(viewers.popplerwidget.AbstractPopplerView):
    def __init__(self, dockwidget):

        self.use_layout = layout = QVBoxLayout()
        super(Widget, self).__init__(dockwidget)

        self.helpButton = QToolButton(
            icon = icons.get("help-contents"),
            autoRaise = True,
            clicked = lambda: userguide.show("manuscript"))
        hor = QHBoxLayout()

        hor.addWidget(self.helpButton)
        self.openButton = QPushButton(self)
        self.openButton.clicked.connect(self.openManuscripts)
        hor.addWidget(self.openButton)

        self.closeButton = QPushButton(self)
        self.closeButton.clicked.connect(self.closeManuscripts)
        hor.addWidget(self.closeButton)

        hor.addStretch(1)

        layout.addLayout(hor)

        app.translateUI(self)
        userguide.openWhatsThis(self)

    def translateUI(self):
        self.setWhatsThis(_(
            "<p>The Manuscript Viewer displays an original manuscript " +
            "one is copying from.</p>\n"
            "<p>See {link} for more information.</p>").format(link=
                userguide.util.format_link("quickinsert")))
        self.openButton.setText(_("Open file"))
        self.closeButton.setText(_("Close"))

    def closeManuscripts(self):
        """ Close current document. """
        self.view.clear()

    def openManuscripts(self):
        """ Displays an open dialog to open a manuscript PDF. """
        caption = app.caption(_("dialog title", "Open Manuscript(s)"))
        directory = app.basedir()
        filename = QFileDialog().getOpenFileName(self, caption, directory, '*.pdf',)
        if filename:
            self.view.clear()
            #TODO: This has to do something different,
            # i.e. not open the doc explicitly but let the base class do it.
            #doc = popplerqt4.Poppler.Document.load(filename)
            #self.view.load(doc)
