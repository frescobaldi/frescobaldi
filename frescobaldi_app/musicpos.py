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
Shows the time position of the text cursor in the music.
"""


from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QLabel

import weakref

import app
import plugin
import cursortools
import worker


class MusicPosition(plugin.ViewSpacePlugin):
    def __init__(self, space):
        self._worker = MusicPositionWorker.create()
        self._worker.textChanged.connect(self.slotDisplayText)
        self._timer = QTimer(singleShot=True, timeout=self.slotTimeout)
        self._waittimer = QTimer(singleShot=True, timeout=self.slotTimeout)
        self._label = QLabel()
        space.status.layout().insertWidget(1, self._label)
        self._view = lambda: None
        space.viewChanged.connect(self.slotViewChanged)
        view = space.activeView()
        if view:
            self.slotViewChanged(view)

    def slotViewChanged(self, view):
        old = self._view()
        if old:
            self.disconnectView(old)
        self._view = weakref.ref(view)
        self.connectView(view)
        self.startTimer()

    def connectView(self, view):
        view.cursorPositionChanged.connect(self.startTimer)
        view.document().contentsChanged.connect(self.startWaitTimer)

    def disconnectView(self, view):
        view.cursorPositionChanged.disconnect(self.startTimer)
        view.document().contentsChanged.disconnect(self.startWaitTimer)

    def startWaitTimer(self):
        """Called when the document changes, waits longer to prevent stutter."""
        self._waittimer.start(900)
        self._timer.stop()

    def startTimer(self):
        """Called when the cursor moves."""
        if not self._waittimer.isActive():
            self._timer.start(100)

    def slotTimeout(self):
        """Called when one of the timers fires."""
        view = self._view()
        if view:
            self._worker.prepare(view.document(), view.textCursor())
            QTimer.singleShot(0, self._worker.slotWork)

    def slotDisplayText(self, text):
        """Called from the worker to display the updated music position."""
        self._label.setText(text)
        self._label.setVisible(bool(text))


class MusicPositionWorker(worker.Worker):
    """Worker to update the music position in a background thread.

    If the document has changed, calculating this requires rebuilding
    its ly.music tree (a slow operation). Running it in the background
    thus reduces lag when editing larger files.

    """
    def prepare(self, document, textCursor):
        """Set the document and text cursor atomically."""
        try:
            self.mutex().lock()
            self._document = document
            self._textCursor = textCursor
        finally:
            self.mutex().unlock()

    def slotWork(self):
        """Called from the main thread to recalculate the music position."""
        try:
            self.mutex().lock()
            d = self._document
            c = self._textCursor
            import documentinfo
            m = documentinfo.music(d)
            import ly.duration
            if c.hasSelection():
                cursortools.strip_selection(c)
                length = m.time_length(c.selectionStart(), c.selectionEnd())
                text = _("Length: {length}").format(
                    length=ly.duration.format_fraction(length)) if length is not None else ''
            else:
                pos = m.time_position(c.position())
                text = _("Pos: {pos}").format(
                    pos=ly.duration.format_fraction(pos)) if pos is not None else ''
            self.textChanged.emit(text)
        except AttributeError:
            return  # no document or cursor available
        finally:
            self.mutex().unlock()

    # argument: text
    textChanged = pyqtSignal(str)


app.viewSpaceCreated.connect(MusicPosition.instance)

