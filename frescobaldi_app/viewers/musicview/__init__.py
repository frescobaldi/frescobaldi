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

import viewers
import app


class MusicViewPanel(viewers.AbstractViewPanel):
    def __init__(self, mainwindow):
        super(MusicViewPanel, self).__init__(mainwindow, Actions)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+M"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("window title", "Music View"))
        self.toggleViewAction().setText(_("&Music View"))

    def createWidget(self):
        from . import widget
        w = widget.MusicView(self)
        w.zoomChanged.connect(self.slotMusicZoomChanged)
        w.updateZoomInfo()
        w.view.surface().selectionChanged.connect(self.updateSelection)
        w.view.surface().pageLayout().setPagesPerRow(1)   # default to single
        w.view.surface().pageLayout().setPagesFirstRow(0) # pages

        import qpopplerview.pager
        self._pager = p = qpopplerview.pager.Pager(w.view)
        p.pageCountChanged.connect(self.slotPageCountChanged)
        p.currentPageChanged.connect(self.slotCurrentPageChanged)
        app.languageChanged.connect(self.updatePagerLanguage)

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

    def translateUI(self):
        super(Actions, self).translateUI()
