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
The PDF preview panel widget.
"""

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import popplerqt4
import qpopplerview

import app
import icons
import textformats


class PDFView(QWidget):
    def __init__(self, dockwidget):
        super(PDFView, self).__init__(dockwidget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.view = qpopplerview.View(self)
        layout.addWidget(self.view)
        
    def sizeHint(self):
        size = self.parent().mainwindow().size()
        return QSize(size.width() / 2, size.height())
        
    def openPDF(self, pdf):
        # TEMP !!
        d = popplerqt4.Poppler.Document.load(pdf)
        d.setRenderHint(1)
        d.setRenderHint(2)
        d.setPaperColor(textformats.formatData('editor').baseColors['paper'])
        self.view.setViewMode(qpopplerview.FitWidth)
        self.view.load(d)
        self.view.surface().pageLayout().update()
        self.view.surface().updateLayout()

