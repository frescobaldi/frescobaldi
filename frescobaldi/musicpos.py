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


from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel

import weakref

import app
import plugin
import cursortools
import documentinfo


class MusicPosition(plugin.ViewSpacePlugin):
    def __init__(self, space):
        self._timer = QTimer(singleShot=True, timeout=self.slotTimeout)
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
        d = documentinfo.info(view.document())
        d.contentsChanged.connect(self.slotTimeout)

    def disconnectView(self, view):
        view.cursorPositionChanged.disconnect(self.startTimer)
        d = documentinfo.info(view.document())
        d.contentsChanged.disconnect(self.slotTimeout)

    def startTimer(self):
        """Called when the cursor moves."""
        try:
            if not self._view().document().isChanging():
                self._timer.start(100)
        except AttributeError:
            pass

    def slotTimeout(self):
        """Called when one of the timers fires."""
        view = self._view()
        if view:
            try:
                d = view.document()
                c = view.textCursor()
            except RuntimeError:
                # This happens if the window is closed before the timer fires
                return
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
            self._label.setText(text)
            self._label.setVisible(bool(text))


app.viewSpaceCreated.connect(MusicPosition.instance)

