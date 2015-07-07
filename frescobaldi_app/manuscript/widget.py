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
The Quick Insert panel widget.
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import os

try:
    import popplerqt4
except ImportError:
    pass

import qpopplerview
import popplerview

import app
import userguide.util
import icons
import symbols

#from view import View

class ManuscriptView(QWidget):
    def __init__(self, dockwidget):
        super(ManuscriptView, self).__init__(dockwidget)
        self._dockwidget = weakref.ref(dockwidget)
        # filled in by ButtonGroup subclasses
        self.actionDict = {}

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.helpButton = QToolButton(
            icon = icons.get("help-contents"),
            autoRaise = True,
            clicked = lambda: userguide.show("manuscript"))
        hor = QHBoxLayout()

        hor.addWidget(self.helpButton)
        self.openButton = QPushButton(self)
        self.openButton.clicked.connect(self.openManuscripts)
        hor.addWidget(self.openButton)
        hor.addStretch(1)

        layout.addLayout(hor)

        self.view = popplerview.View(self)
        layout.addWidget(self.view)

        import qpopplerview.pager
        self._pager = qpopplerview.pager.Pager(self.view)

        app.translateUI(self)
        userguide.openWhatsThis(self)

    def translateUI(self):
        self.setWhatsThis(_(
            "<p>The Manuscript Viewer displays an original manuscript " +
            "one is copying from.</p>\n"
            "<p>See {link} for more information.</p>").format(link=
                userguide.util.format_link("quickinsert")))
        self.openButton.setText(_("Open file"))

    def actionForName(self, name):
        """This is called by the ShortcutCollection of our dockwidget, e.g. if the user presses a key."""
        try:
            return self.actionDict[name]
        except KeyError:
            pass

    def mainwindow(self):
        return self.parent().mainwindow()

    def openManuscripts(self):
        """ Displays an open dialog to open one or more documents. """
        caption = app.caption(_("dialog title", "Open Manuscript(s)"))
        directory = app.basedir()
        files = QFileDialog.getOpenFileNames(self, caption, directory, '*')
        for f in files:
            doc = popplerqt4.Poppler.Document.load(f)
            self.view.load(doc)

    def dockwidget(self):
        return self._dockwidget()
