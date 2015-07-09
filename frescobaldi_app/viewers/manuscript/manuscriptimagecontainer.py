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
ImageContainer, contains images for display in the manuscript viewer.

"""

from __future__ import unicode_literals

import os
import sys

from PyQt4 import QtCore
from PyQt4 import QtGui


import manuscriptcontainer

class ManuscriptPage(QtGui.QLabel):
    """A manuscript page. Initially this is
    simply a label, but it will get much more information."""
    
    def __init__(self, parent):
        super(ManuscriptPage, self).__init__(parent)


class ManuscriptImageContainer(manuscriptcontainer.AbstractManuscriptContainer):
    """A container for an image list.
    This is a parallel implementation to a PDF viewer class."""
    def __init__(self, parent, image_list):
        super(ManuscriptImageContainer, self).__init__(parent)
        
        self.pages = []
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        for i in image_list:
            pix = QtGui.QPixmap(i)
            page = ManuscriptPage(self)
            page.setPixmap(pix)
            self.pages.append(i)
            self.layout().addWidget(page)
        
        
        
        
    
