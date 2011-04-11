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
The PDF preview panel widget.
"""

from __future__ import unicode_literals

import itertools
import os
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4
import qpopplerview

import app
import icons
import textformats

from . import pointandclick


class MusicView(QWidget):
    def __init__(self, dockwidget):
        super(MusicView, self).__init__(dockwidget)
        
        self._positions = weakref.WeakKeyDictionary()
        self._currentDocument = lambda: None
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.view = qpopplerview.View(self)
        layout.addWidget(self.view)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        self.view.setViewMode(qpopplerview.FitWidth)
        self.view.surface().pageLayout().setDPI(self.physicalDpiX(), self.physicalDpiY())
        self.view.viewModeChanged.connect(self.slotViewModeChanged)
        self.view.surface().linkClicked.connect(self.slotLinkClicked)
        self.view.surface().linkHovered.connect(self.slotLinkHovered)
        self.view.surface().setShowUrlTips(False)
        self.view.surface().linkHelpRequested.connect(self.slotLinkHelpRequested)
        self.slotViewModeChanged(self.view.viewMode())
        
        zoomer = self.parent().actionCollection.music_zoom_combo
        self.view.viewModeChanged.connect(zoomer.updateZoomInfo)
        self.view.surface().pageLayout().scaleChanged.connect(zoomer.updateZoomInfo)

    def sizeHint(self):
        return self.parent().mainwindow().size() / 2
        
    def slotViewModeChanged(self, viewmode):
        ac = self.parent().actionCollection
        ac.music_fit_width.setChecked(viewmode == qpopplerview.FitWidth)
        ac.music_fit_height.setChecked(viewmode == qpopplerview.FitHeight)
        ac.music_fit_both.setChecked(viewmode == qpopplerview.FitBoth)

    def openDocument(self, doc):
        """Opens a documents.Document instance."""
        cur = self._currentDocument()
        if cur:
            self._positions[cur] = self.view.position()
            
        self._currentDocument = weakref.ref(doc)
        self.view.load(doc.document())
        position = self._positions.get(doc, (0, 0, 0))
        self.view.setPosition(position)
        self._links = pointandclick.links(doc.document())

    def clear(self):
        """Empties the view."""
        cur = self._currentDocument()
        if cur:
            self._positions[cur] = self.view.position()
        self._currentDocument = lambda: None
        self.view.clear()
        
    def readSettings(self):
        qpopplerview.cache.options().setPaperColor(textformats.formatData('editor').baseColors['paper'])
        self.view.redraw()

    def slotLinkClicked(self, ev, page, link):
        cursor = self._links.cursor(link, True)
        if cursor:
            self.parent().mainwindow().setTextCursor(cursor, findOpenView=True)
        elif ev.button() != Qt.RightButton and isinstance(link, popplerqt4.Poppler.LinkBrowse):
            QDesktopServices.openUrl(QUrl(link.url()))

    def slotLinkHovered(self, page, link):
        cursor = self._links.cursor(link)
        if not cursor or cursor.document() != self.parent().mainwindow().currentDocument():
            return
        # highlight token(s) at this cursor
        view = self.parent().mainwindow().currentView()
        if not hasattr(self, '_hoverformat'):
            self._hoverformat = QTextCharFormat()
        color = textformats.formatData('editor').baseColors['selectionbackground']
        color.setAlpha(128)
        self._hoverformat.setBackground(color)
        import tokeniter
        block = cursor.block()
        column = cursor.position() - block.position()
        tokens = tokeniter.TokenIterator(block)
        for token in itertools.dropwhile(lambda t: t.pos < column, tokens.forward(False)):
            view.highlight(self._hoverformat, [tokens.cursor()], 2, 1000)
            break

    def slotLinkHelpRequested(self, pos, page, link):
        if isinstance(link, popplerqt4.Poppler.LinkBrowse):
            text = link.url()
            cursor = self._links.cursor(link)
            m = pointandclick.textedit_match(link.url())
            if m:
                filename, line, column = pointandclick.readurl(m)
                text = "{0}  {1}:{2}".format(os.path.basename(filename), line, column)
            QToolTip.showText(pos, text, self.view.surface(), page.linkRect(link))

