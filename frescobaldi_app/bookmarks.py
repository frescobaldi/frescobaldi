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
Manages marked lines (bookmarks) for a Document.

A mark is simply a QTextCursor that maintains its position in the document.

There are different types (categories) of marks, listed in the module-global
types variable. Currently the available types are 'mark' (a normal mark)
and 'error' (marking a line containing an error).

"""


import bisect
import json

from PyQt5.QtGui import QTextCursor

import metainfo
import signals
import plugin

types = (
    'mark',
    'error',
)


metainfo.define('bookmarks', json.dumps(None))


def bookmarks(document):
    """Returns the Bookmarks instance for the document."""
    return Bookmarks.instance(document)


class Bookmarks(plugin.DocumentPlugin):
    """Manages bookmarks (marked lines) for a Document.

    The marks are stored in the metainfo for the Document.

    """
    marksChanged = signals.Signal()

    def __init__(self, document):
        """Creates the Bookmarks instance."""
        document.loaded.connect(self.load)
        document.saved.connect(self.save)
        document.closed.connect(self.save)
        self.load() # initializes self._marks

    def marks(self, type=None):
        """Returns marks (QTextCursor instances).

        If type is specified (one of the names in the module-global types variable),
        the list of marks of that type is returned.
        If type is None, a dictionary listing all types mapped to lists of marks
        is returned.

        """

        return self._marks[type] if type else self._marks

    def setMark(self, linenum, type):
        """Marks the given line number with a mark of the given type."""
        nums = [mark.blockNumber() for mark in self._marks[type]]
        if linenum in nums:
            return
        index = bisect.bisect_left(nums, linenum)
        mark = QTextCursor(self.document().findBlockByNumber(linenum))
        try:
            # only available in very recent PyQt5 versions
            mark.setKeepPositionOnInsert(True)
        except AttributeError:
            pass
        self._marks[type].insert(index, mark)
        self.marksChanged()

    def unsetMark(self, linenum, type):
        """Removes a mark of the given type on the given line."""
        nums = [mark.blockNumber() for mark in self._marks[type]]
        if linenum in nums:
            # remove double occurrences
            while True:
                index = bisect.bisect_left(nums, linenum)
                del self._marks[type][index]
                del nums[index]
                if linenum not in nums:
                    break
            self.marksChanged()

    def toggleMark(self, linenum, type):
        """Toggles the mark of the given type on the given line."""
        nums = [mark.blockNumber() for mark in self._marks[type]]
        index = bisect.bisect_left(nums, linenum)
        if linenum in nums:
            # remove double occurrences
            while True:
                del self._marks[type][index]
                del nums[index]
                if linenum not in nums:
                    break
                index = bisect.bisect_left(nums, linenum)
        else:
            mark = QTextCursor(self.document().findBlockByNumber(linenum))
            try:
                # only available in very recent PyQt5 versions
                mark.setKeepPositionOnInsert(True)
            except AttributeError:
                pass
            self._marks[type].insert(index, mark)
        self.marksChanged()

    def hasMark(self, linenum, type=None):
        """Returns True if the line has a mark (of the given type if specified) else False."""
        for type in types if type is None else (type,):
            for mark in self._marks[type]:
                if mark.blockNumber() == linenum:
                    return True
        return False

    def clear(self, type=None):
        """Removes all marks, or only all marks of the given type. if specified."""
        if type is None:
            for type in types:
                self._marks[type] = []
        else:
            self._marks[type] = []
        self.marksChanged()

    def nextMark(self, cursor, type=None):
        """Finds the first mark after the cursor (of the type if specified)."""
        if type is None:
            marks = []
            for type in types:
                marks += self._marks[type]
            # sort the marks on line number
            marks.sort(key=lambda mark: mark.blockNumber())
        else:
            marks = self._marks[type]
        nums = [mark.blockNumber() for mark in marks]
        index = bisect.bisect_right(nums, cursor.blockNumber())
        if index < len(nums):
            return QTextCursor(marks[index].block())

    def previousMark(self, cursor, type=None):
        """Finds the first mark before the cursor (of the type if specified)."""
        if type is None:
            marks = []
            for type in types:
                marks += self._marks[type]
            # sort the marks on line number
            marks.sort(key=lambda mark: mark.blockNumber())
        else:
            marks = self._marks[type]
        nums = [mark.blockNumber() for mark in marks]
        index = bisect.bisect_left(nums, cursor.blockNumber())
        if index > 0:
            return QTextCursor(marks[index-1].block())

    def load(self):
        """Loads the marks from the metainfo."""
        self._marks = dict((type, []) for type in types)
        marks = metainfo.info(self.document()).bookmarks
        try:
            d = json.loads(marks) or {}
        except ValueError:
            return # No JSON object could be decoded
        for type in types:
            self._marks[type] = [QTextCursor(self.document().findBlockByNumber(num)) for num in d.get(type, [])]
        self.marksChanged()

    def save(self):
        """Saves the marks to the metainfo."""
        d = {}
        for type in types:
            d[type] = lines = []
            for mark in self._marks[type]:
                linenum = mark.blockNumber()
                if linenum not in lines:
                    lines.append(linenum)
        metainfo.info(self.document()).bookmarks = json.dumps(d)


