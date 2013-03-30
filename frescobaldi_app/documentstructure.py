# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
Maintains an overview of the structure of a Document.
"""

from __future__ import unicode_literals

import re

from PyQt4.QtCore import QSettings

import app
import plugin


default_outline_res = [
r"\\(score|book|bookpart)\b",
r"\\(new|context)\s+[A-Z]\w+",
r"%%+\s*BEGIN",
r"[a-zA-Z]+\s*=",
r"^<<",
r"^\{",
r"^\\relative",
r"\b(FIXME|HACK|XXX)\b",
]

def outline_re():
    """Return the expression to look for document outline items."""
    rx = QSettings().value("documentstructure/outline_re", default_outline_res, type(""))
    rx = '|'.join(rx)
    return re.compile(rx, re.MULTILINE)


class DocumentStructure(plugin.DocumentPlugin):
    def __init__(self, document):
        app.settingsChanged.connect(self.invalidate, -999)
        self._outline = None
    
    def invalidate(self):
        """Called when the document changes or the settings are changed."""
        self._outline = None
        self.document().contentsChanged.disconnect(self.invalidate)
    
    def outline(self):
        """Return the document outline as a series of match objects."""
        if self._outline is None:
            self._outline = list(outline_re().finditer(self.document().toPlainText()))
            self.document().contentsChanged.connect(self.invalidate)
        return self._outline



