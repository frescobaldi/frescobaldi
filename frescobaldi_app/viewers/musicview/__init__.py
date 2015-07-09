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
The PDF preview panel.

This file loads even if popplerqt4 is absent, although the PDF preview
panel only shows a message about missing the popplerqt4 module.

The widget module contains the real widget, the documents module a simple
abstraction and caching of Poppler documents with their filename,
and the printing module contains code to print a Poppler document, either
via a PostScript rendering or by printing raster images to a QPrinter.

All the point & click stuff is handled in the pointandclick module.

"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QKeySequence

import app
import viewers
from viewers import popplerwidget


class MusicViewPanel(viewers.AbstractViewPanel):
    def __init__(self, mainwindow):
        super(MusicViewPanel, self).__init__(mainwindow, Actions)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+M"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        ac = self.actionCollection
        ac.music_document_select.documentsChanged.connect(self.updateActions)

    def translateUI(self):
        self.setWindowTitle(_("window title", "Music View"))
        self.toggleViewAction().setText(_("&Music View"))

    def createWidget(self):
        #TODO: clean that up, the current implementation is
        # simply to demonstrate the steps where one can hook into.
        # Concise implementation here:
        # return super(MusicViewPanel, self).createWidget(Widget(self))
        w = super(MusicViewPanel, self).configureWidget(Widget(self))
        # there could be more code after applying the superclass's method

        selector = self.actionCollection.music_document_select
        selector.currentDocumentChanged.connect(w.openDocument)
        selector.documentClosed.connect(w.clear)

        if selector.currentDocument():
            # open a document only after the widget has been created;
            # this prevents many superfluous resizes
            def open():
                if selector.currentDocument():
                    w.openDocument(selector.currentDocument())
            QTimer.singleShot(0, open)

        return w

class Actions(viewers.Actions):
    name = "musicview"

    def createActions(self, parent=None):
        super(Actions, self).createActions(parent)
        self.music_document_select = viewers.DocumentChooserAction(parent)
        self.music_document_select.setShortcut(QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_O))

    def translateUI(self):
        super(Actions, self).translateUI()
        self.music_document_select.setText(_("Select Music View Document"))

class Widget(viewers.popplerwidget.AbstractPopplerView):
    def __init__(self, dockwidget):
        super(Widget, self).__init__(dockwidget)
