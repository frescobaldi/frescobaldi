# -*- coding: utf-8 -*-
#
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

from PyQt5.QtCore import pyqtSignal, QRect, Qt
from PyQt5.QtGui import QPainter, QKeySequence
from PyQt5.QtWidgets import QStyle, QStyleOptionButton


class SelectorViewMixin:
    """SelectorViewMixin class, to mixin with View.

    Adds the capability to select or unselect Pages.
    Pages are numbered from 1.

    Instance variables:

    ``userChangeSelectionModeEnabled`` = True
        whether the user can change the selectionMode (by longpressing a page
        to enable selectionMode, and pressing ESC to leave selectionMode. (Be
        sure to mix in the :class:`qpageview.util.LongMousePressMixin` class
        when you want to use the long mouse press event.)

    """
    selectionChanged = pyqtSignal()
    selectionModeChanged = pyqtSignal(bool)

    userChangeSelectionModeEnabled = True


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
        diff = self._selection ^ old
        if diff:
            self.selectionChanged.emit()
            # repaint if needed
            visible = self.visibleRect()
            if any(self.page(n).geometry() & visible for n in diff):
                self.viewport().update()

    def updatePageLayout(self, lazy=False):
        """Reimplemented to also check the selection."""
        super().updatePageLayout(lazy)
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

    def selectAll(self):
        """Convenience method to select all pages."""
        with self.modifySelection() as s:
            s.update(range(1, self.pageCount() + 1))

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
            self.viewport().update() # repaint

    def paintEvent(self, ev):
        super().paintEvent(ev)      # first draw the contents
        if self._selectionMode:
            painter = QPainter(self.viewport())
            for page, rect in self.pagesToPaint(ev.rect(), painter):
                self.drawSelection(page, painter)

    def drawSelection(self, page, painter):
        """Draws the state (selected or not) for the page."""
        option = QStyleOptionButton()
        option.initFrom(self)
        option.rect = QRect(0, 0, QStyle.PM_IndicatorWidth, QStyle.PM_IndicatorHeight)
        pageNum = self.pageLayout().index(page) + 1
        option.state |= QStyle.State_On if pageNum in self._selection else QStyle.State_Off
        scale = None
        # in the unlikely case the checkboxes are larger than the page, scale them down
        if option.rect not in page.rect():
            scale = min(page.width / option.rect.width(), page.height / option.rect.height())
            painter.save()
            painter.scale(scale, scale)
        self.style().drawPrimitive(QStyle.PE_IndicatorCheckBox, option, painter, self)
        if scale is not None:
            painter.restore()

    def mousePressEvent(self, ev):
        """Reimplemented to check if a checkbox was clicked."""
        if self._selectionMode and ev.buttons() == Qt.LeftButton:
            pos = ev.pos() - self.layoutPosition()
            page = self._pageLayout.pageAt(pos)
            if page:
                pageNum = self._pageLayout.index(page) + 1
                pos -= page.pos()
                if pos in QRect(0, 0, QStyle.PM_IndicatorWidth, QStyle.PM_IndicatorHeight):
                    # the indicator has been clicked
                    if ev.modifiers() & Qt.ControlModifier:
                        # CTRL toggles selection of page
                        self.toggleSelection(pageNum)
                    elif self._selection and ev.modifiers() & Qt.ShiftModifier:
                        # Shift extends the selection
                        with self.modifySelection() as s:
                            s.add(pageNum)
                            first, last = min(self._selection), max(self._selection)
                            s.update(range(first, last+1))
                    else:
                        # toggle this one and clear all the others
                        with self.modifySelection() as s:
                            select = pageNum not in s
                            s.clear()
                            if select:
                                s.add(pageNum)
                    return
        super().mousePressEvent(ev)

    def keyPressEvent(self, ev):
        """Clear the selection and switch off selectionmode with ESC."""
        if self._selectionMode:
            if self.userChangeSelectionModeEnabled and ev.key() == Qt.Key_Escape and not ev.modifiers():
                self.clearSelection()
                self.setSelectionMode(False)
                return
            elif ev.matches(QKeySequence.SelectAll):
                self.selectAll()
                return
        super().keyPressEvent(ev)

    def longMousePressEvent(self, ev):
        """Called on long mouse button press, set selectionMode on if enabled."""
        if self.userChangeSelectionModeEnabled:
            if not self._selectionMode:
                self.setSelectionMode(True)
                return
            elif not self._selection:
                self.setSelectionMode(False)
                return
        super().longMousePressEvent(ev)


