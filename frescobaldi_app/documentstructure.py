# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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


import re

from PyQt5.QtCore import QSettings

import app
import plugin


default_outline_patterns = [
r"(?P<title>\\(score|book|bookpart))\b",
r"^\\(paper|layout|header)\b",
r"\\(new|context)\s+[A-Z]\w+",
r"(?P<title>BEGIN[^\n]*)[ \t]*$",
r"^[a-zA-Z]+\s*=",
r"^<<",
r"^\{",
r"^\\relative([ \t]+\w+[',]*)?",
r"\b(?P<alert>(FIXME|HACK|XXX+)\b\W*\w+)",
]


# cache the outline regexp
_outline_re = None


def outline_re():
    """Return the expression to look for document outline items."""
    global _outline_re
    if _outline_re is None:
        _outline_re = create_outline_re()
    return _outline_re


def _reset_outline_re():
    global _outline_re
    _outline_re = None


app.settingsChanged.connect(_reset_outline_re, -999)


def create_outline_re():
    """Create and return the expression to look for document outline items."""
    try:
        rx = QSettings().value("documentstructure/outline_patterns",
                               default_outline_patterns, str)
    except TypeError:
        rx = []
    # suffix duplicate named groups with a number
    groups = {}
    new_rx = []
    for e in rx:
        try:
            c = re.compile(e)
        except re.error:
            continue
        if c.groupindex:
            for name in c.groupindex:
                if name in groups:
                    groups[name] += 1
                    new_name = name + format(groups[name])
                    e = e.replace("(?P<{0}>".format(name), "(?P<{0}>".format(new_name))
                else:
                    groups[name] = 0
        new_rx.append(e)
    rx = '|'.join(new_rx)
    return re.compile(rx, re.MULTILINE | re.UNICODE)


class DocumentStructure(plugin.DocumentPlugin):
    def __init__(self, document):
        self._outline = None

    def invalidate(self):
        """Called when the document changes or the settings are changed."""
        self._outline = None
        app.settingsChanged.disconnect(self.invalidate)
        self.document().contentsChanged.disconnect(self.invalidate)

    def outline(self):
        """Return the document outline as a series of match objects."""
        if self._outline is None:
            self._outline = list(outline_re().finditer(self.document().toPlainText()))
            self.document().contentsChanged.connect(self.invalidate)
            app.settingsChanged.connect(self.invalidate, -999)
        return self._outline



