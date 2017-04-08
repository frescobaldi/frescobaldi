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
Highlights matching characters in a textedit,
using an ArbitraryHighlighter.
"""

from . import matcher

class Matcher(matcher.Matcher):

    priority = 0

    def __init__(self, highlighter):
        """Initialize the Matcher; highlighter is an ArbitraryHighlighter instance."""
        super(matcher.Matcher, self).__init__(highlighter)
        self.edit().cursorPositionChanged.connect(self.slotCursorPositionChanged)

    def edit(self):
        """Reimplemented to return the parent of our parent:)"""
        return self.parent().parent()

    def highlight(self, cursors):
        """Highlights the selections of the specified QTextCursor instances."""
        self.parent().highlight(self.format, cursors, self.priority, self.time)

    def clear(self):
        """Removes the highlighting."""
        self.parent().clear(self.format)
