# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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
Provides an interface for paging in a View by page number.
"""


from PyQt5.QtCore import pyqtSignal, QEvent, QTimer, QObject


class Pager(QObject):
    """Provides an interface for paging in a View by page number.

    Pages are numbered starting with 1 in this api!

    """
    currentPageChanged = pyqtSignal(int)
    pageCountChanged = pyqtSignal(int)

    def __init__(self, view):
        """Initializes the Pager with the View.

        Also connects with the Surface of the View and its Layout,
        so don't interchange them after initializing the Pager.

        """
        super(Pager, self).__init__(view)
        self._currentPage = 0
        self._pageCount = 0
        self._blockLevel = 0
        self._pageNumSet = False
        self._updateTimer = QTimer(
            singleShot=True, interval=100, timeout=self._updatePageNumber)

        # connect
        view.installEventFilter(self)
        view.surface().installEventFilter(self)
        view.surface().pageLayout().changed.connect(self._layoutChanged)

        # Connect to the kineticScrollingEnabled signal to avoid unneeded updates.
        view.kineticScrollingActive.connect(self.blockListening)

    def currentPage(self):
        """Returns the current page number (0 if there are no pages)."""
        return self._currentPage

    def setCurrentPage(self, num):
        """Shows the specified page number."""
        changed, self._currentPage = self._currentPage != num, num
        self._pageNumSet = True
        self.blockListening(True)
        self.view().gotoPageNumber(num - 1)
        self.blockListening(False)
        if changed:
            self.currentPageChanged.emit(self._currentPage)

    def pageCount(self):
        """Returns the number of pages."""
        return self._pageCount

    def view(self):
        return self.parent()

    def _layoutChanged(self):
        """Called internally whenever the layout is updated."""
        layout = self.view().surface().pageLayout()
        self._pageCount, old = len(layout), self._pageCount
        if old != self._pageCount:
            self.pageCountChanged.emit(self._pageCount)
        self._updatePageNumber()

    def _updatePageNumber(self):
        """Called internally on layout change or view resize or surface move."""
        self._currentPage, old = self.view().currentPageNumber() + 1, self._currentPage
        if self._currentPage == 0 and self._pageCount > 0:
            # the view may not be initialized
            self._currentPage = 1
        if old != self._currentPage:
            self.currentPageChanged.emit(self._currentPage)

    def blockListening(self, block):
        """Block/unblock listening to event, used to avoid multiple updates when we know lots
        of events are going to be sent to the pager.

        Blocking can be nested, only the outermost unblock will really unblock the event processing."""
        if block:
            self._blockLevel += 1
        else:
            self._blockLevel -= 1

        if self._blockLevel == 0:
            if self._pageNumSet:
                self._pageNumSet = False
            else:
                self._updatePageNumber()

    def eventFilter(self, obj, ev):
        if (self._blockLevel == 0 and
            ((ev.type() == QEvent.Resize and obj is self.view())
             or (ev.type() == QEvent.Move and obj is self.view().surface()))
            and not self._updateTimer.isActive()):
            self._updateTimer.start()
        return False


