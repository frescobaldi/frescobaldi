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
Manages highlighting of arbitrary sections in a Q(Plain)TextEdit
using QTextEdit.ExtraSelections.
"""

import weakref

from PyQt4.QtCore import QObject, QTimer
from PyQt4.QtGui import QTextCharFormat, QTextEdit, QTextFormat


class ArbitraryHighlighter(QObject):
    """Manages highlighting of arbitrary sections in a Q(Plain)TextEdit.
    
    Stores and highlights lists of QTextCursors on a per-format basis.
    
    """
    def __init__(self, edit):
        """Initializes ourselves with a Q(Plain)TextEdit as parent."""
        super(ArbitraryHighlighter, self).__init__(edit)
        self._selections = {}
    
    def highlight(self, format, cursors, priority=0, msec=0):
        """Highlights the selection of an arbitrary list of QTextCursors.
        
        format can be a name for a predefined text format or a QTextCharFormat;
        in the first case the textFormat() method should return a qtextformat to use.
        priority determines the order of drawing, highlighting with higher priority
        is drawn over highlighting with lower priority.
        msec, if > 0, removes the highlighting after that many milliseconds.
        
        """
        fmt = format if isinstance(format, QTextFormat) else self.textFormat(format)
        selections = []
        for cursor in cursors:
            es = QTextEdit.ExtraSelection()
            es.cursor = cursor
            es.format = fmt
            selections.append(es)
        if msec:
            def clear(selfref=weakref.ref(self)):
                self = selfref()
                if self:
                    self.clear(format)
            timer = QTimer(timeout=clear, singleShot=True)
            timer.start(msec)
            self._selections[format] = (priority, selections, timer)
        else:
            self._selections[format] = (priority, selections)
        self.update()

    def clear(self, format):
        """Removes the highlighting for the given format (name or QTextCharFormat)."""
        try:
            del self._selections[format]
        except KeyError:
            pass
        else:
            self.update()

    def textFormat(self, name):
        """Implement this to return a QTextCharFormat for the given name."""
        raise NotImplementedError

    def update(self):
        """(Internal) Called whenever the arbitrary highlighting changes."""
        textedit = self.parent()
        if textedit:
            textedit.setExtraSelections(
                sum((s[1] for s in sorted(self._selections.values())), []))

    def reload(self):
        """Reloads the named formats in the highlighting (e.g. in case of settings change)."""
        for format in self._selections:
            if not isinstance(format, QTextFormat):
                fmt = self.textFormat(format)
                for es in self._selections[format][1]:
                    es.format = fmt
        self.update()


