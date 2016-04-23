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
Manages highlighting of arbitrary things in a View, e.g.
the current line, marked lines, search results etc.
"""


from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QColor, QTextCharFormat, QTextFormat

import app
import plugin
import bookmarks
import textformats
import gadgets.arbitraryhighlighter


def highlighter(view):
    return ViewHighlighter.instance(view)


app.viewCreated.connect(highlighter)


class ViewHighlighter(plugin.Plugin, gadgets.arbitraryhighlighter.ArbitraryHighlighter):
    def __init__(self, view):
        # no need to call the plugin __init__ method
        gadgets.arbitraryhighlighter.ArbitraryHighlighter.__init__(self, view)
        self._cursorFormat = QTextCharFormat()
        self._cursorFormat.setProperty(QTextFormat.FullWidthSelection, True)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        bookmarks.bookmarks(view.document()).marksChanged.connect(self.updateMarkedLines)
        self.updateMarkedLines()
        view.cursorPositionChanged.connect(self.updateCursor)
        view.installEventFilter(self)

    def updateMarkedLines(self):
        """Called when something changes in the bookmarks."""
        for type, marks in bookmarks.bookmarks(self.parent().document()).marks().items():
            self.highlight(type, marks, -1)

    def eventFilter(self, view, ev):
        if ev.type() in (QEvent.FocusIn, QEvent.FocusOut):
            self.updateCursor(view)
        return False

    def updateCursor(self, view=None):
        """Called when the textCursor has moved. Highlights the current line.

        If view is None (the default), our parent() is assumed to be the
        view. The eventFilter() method calls us with the view, this is
        done because the event filter is sometimes called very late in
        the destructor phase, when our parent is possibly not valid
        anymore.

        """
        if view is None:
            view = self.parent()
        # sometimes in the destruction phase, view is a generic QWidget...
        try:
            cursor = view.textCursor()
        except AttributeError:
            return
        # highlight current line
        cursor.clearSelection()
        color = QColor(self._baseColors['current'])
        color.setAlpha(200 if view.hasFocus() else 100)
        self._cursorFormat.setBackground(color)
        self.highlight(self._cursorFormat, [cursor], 0)

    def readSettings(self):
        data = textformats.formatData('editor')
        self._baseColors = data.baseColors
        self.updateCursor()
        self.reload()

    def textFormat(self, name):
        """(Internal) Returns a QTextCharFormat setup according to the preferences.

        For bookmarks and the current line, FullWidthSelection is automatically enabled.

        """
        f = QTextCharFormat()
        f.setBackground(self._baseColors[name])
        if name in ('current', 'mark', 'error'):
            f.setProperty(QTextFormat.FullWidthSelection, True)
        return f
