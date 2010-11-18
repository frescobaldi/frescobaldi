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
A Frescobaldi (LilyPond) document.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import view


class Document(QTextDocument):
    def __init__(self):
        super(Document, self).__init__()
        self.setDocumentLayout(QPlainTextDocumentLayout(self))
        self._materialized = False
        app.documents.append(self)
        app.documentCreated(self)
        
        
    def close(self):
        app.documents.remove(self)
        app.documentClosed(self)

    def materialize(self):
        """Really load and instantiate ourselves.
        
        Makes lazy-loading lots of documents possible.
        
        """
        if self._materialized:
            return
        ### Implement
        app.documentMaterialized(self)
        self._materialized = True

    def createView(self):
        """Returns a new View on our document."""
        self.materialize()
        newview = view.View(self)
        return newview
    