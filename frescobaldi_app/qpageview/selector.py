# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
SelectorViewMixin class, to mixin with View.

Adds the capability to select or unselect Pages.

"""

import contextlib

from PyQt5.QtCore import pyqtSignal


class SelectorViewMixin:
    """SelectorViewMixin class, to mixin with View.

    Adds the capability to select or unselect Pages.
    Pages are numbered from 1.

    """
    selectionChanged = pyqtSignal()
    selectionModeChanged = pyqtSignal(bool)


    def __init__(self, parent=None, **kwds):
        self._selection = set()
        self._selectionMode = False
        super().__init__(parent, **kwds)

    def selection(self):
        """Return the current list of selected page numbers."""
        return sorted(self._selection)
    
    @contextlib.contextmanager
    def modifySelection(self):
        """Context manager that allows changing the selection.

        Yields a set, and on exit of the context, stores the modifications and
        emits the selectionChanged() signal. Used internally by all other
        methods.

        """
        old = set(self._selection)
        yield self._selection
        self._checkSelection()
        if self._selection != old:
            self.selectionChanged.emit()

    def updatePageLayout(self):
        """Reimplemented to also check the selection."""
        super().updatePageLayout()
        self._checkSelection()

    def _checkSelection(self):
        """Internal; silently remove page numbers from the selection that do not exist (anymore)."""
        count = self.pageCount()
        nums = [n for n in self._selection if n < 1 or n > count]
        self._selection.difference_update(nums)

    def clearSelection(self):
        """Convenience method to clear the selection."""
        with self.modifySelection() as s:
            s.clear()

    def toggleSelection(self, pageNumber):
        """Toggles the selected state of page number pageNumber."""
        with self.modifySelection() as s:
            count = len(s)
            s.add(pageNumber)
            if count == len(s):
                s.remove(pageNumber)

    def selectionMode(self):
        """Return the current selectionMode (True is enabled, False is disabled)."""
        return self._selectionMode
    
    def setSelectionMode(self, mode):
        """Switch selection mode on or off (True is enabled, False is disabled)."""
        if self._selectionMode != mode:
            self._selectionMode = mode
            self.selectionModeChanged.emit(mode)
            self.update() # repaint

