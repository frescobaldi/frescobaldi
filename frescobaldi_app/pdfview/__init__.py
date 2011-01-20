# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
The PDF preview panel.
"""

import weakref

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QKeySequence

import panels


class PDFViewPanel(panels.Panel):
    def __init__(self, mainwindow):
        super(PDFViewPanel, self).__init__(mainwindow)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+P"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
    
    def translateUI(self):
        self.setWindowTitle(_("PDF Preview"))
        self.toggleViewAction().setText(_("&PDF Preview"))
        
    def createWidget(self):
        import widget
        return widget.PDFView(self)


