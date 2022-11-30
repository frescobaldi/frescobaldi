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

import lydocument
import ly.document

# default outline patterns that are ignored in comments
default_outline_patterns = [
r"(?P<title>\\(score|book|bookpart))\b",
r"^\\(paper|layout|header)\b",
r"\\(new|context)\s+[A-Z]\w+",
r"^[a-zA-Z]+\s*=",
r"^<<",
r"^\{",
r"^\\relative([ \t]+\w+[',]*)?",
]

# default outline patterns that are matched also in comments
default_outline_patterns_comments = [
r"(?P<title>BEGIN[^\n]*)[ \t]*$",
r"\b(?P<alert>(FIXME|HACK|XXX+)\b\W*\w+)",
]


# cache the outline regexp
_outline_re = None
_outline_re_comments = None


def outline_re():
    """Return the expression to look for document outline items excluding comments."""
    global _outline_re
    if _outline_re is None:
        _outline_re = create_outline_re()
    return _outline_re

def outline_re_comments():
    """Return the expression to look for document outline items in whole document
    (including comments)."""
    global _outline_re_comments
    if _outline_re_comments is None:
        _outline_re_comments = create_outline_re_comments()
    return _outline_re_comments

def _reset_outline_re():
    global _outline_re
    global _outline_re_comments
    _outline_re = None
    _outline_re_comments = None


app.settingsChanged.connect(_reset_outline_re, -999)


def create_outline_re_from_patterns(rx):
    """Create and return the expression to look for document outline items."""
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

def create_outline_re():
    """Create and return the expression to look for document outline items
    excluding comments."""
    try:
        rx = QSettings().value("documentstructure/outline_patterns",
                               default_outline_patterns, str)
    except TypeError:
        rx = []
    return create_outline_re_from_patterns(rx)

def create_outline_re_comments():
    """Create and return the expression to look for document outline items
    in whole document (including comments)."""
    try:
        rx = QSettings().value("documentstructure/outline_patterns_comments",
                               default_outline_patterns_comments, str)
    except TypeError:
        rx = []
    return create_outline_re_from_patterns(rx)


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
            # match patterns excluding comments
            active_code = self.remove_comments()
            outline_list = list(outline_re().finditer(active_code))
            # match patterns including comments
            outline_comments_list = list(outline_re_comments().finditer(self.document().toPlainText()))
            # merge lists and sort by start position
            self._outline = outline_list + outline_comments_list
            self._outline.sort(key=lambda match: match.start())
            self.document().contentsChanged.connect(self.invalidate)
            app.settingsChanged.connect(self.invalidate, -999)
        return self._outline

    def remove_comments(self):
        """Remove Lilypond comments from text"""
        def whiteout_section(cursor, start, end):
            spaces = ''.join(' ' for x in range(start, end))
            with cursor.document as doc:
                doc[start:end] = spaces

        doc = ly.document.Document(self.document().toPlainText())
        cursor = lydocument.Cursor(doc)
        source = ly.document.Source(cursor, True, tokens_with_position=True)
        start = 0
        for token in source:
            if isinstance(token, ly.lex.BlockCommentStart):
                start = token.pos
            elif isinstance(token, ly.lex.BlockCommentEnd):
                if start:
                    whiteout_section(cursor, start, token.end)
                    start = 0
            elif isinstance(token, ly.lex.Comment):
                whiteout_section(cursor, token.pos, token.end)
        return cursor.document.plaintext()

