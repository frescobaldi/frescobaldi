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
A button that emits a tempo(int) signal when the user clicks multiple times.
"""


import time

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QToolButton

import app
import icons


class TempoButton(QToolButton):
    """A button the user can tap a tempo on.

    emits tempo(bpm) when the user clicks the button multiple times.

    """
    tempo = pyqtSignal(int)

    def __init__(self, icon=None, parent=None):
        super(TempoButton, self).__init__(parent)
        self.setIcon(icon or icons.get("media-record"))
        self.tapStart = 0.0
        self.tapTime = 0.0
        self.tapCount = 0
        self.pressed.connect(self.slotPressed)
        app.translateUI(self)

    def translateUI(self):
        self.setToolTip(_("The tempo is set as you click this button."))
        self.setWhatsThis(_(
            "Tap this button to set the tempo.\n\n"
            "The average speed of clicking is used; wait 3 seconds to \"reset\"."))

    def slotPressed(self):
        self.tapTime, t = time.time(), self.tapTime
        if 0.1 < self.tapTime - t < 3.0:
            self.tapCount += 1
            bpm = int(60.0 * self.tapCount / (self.tapTime - self.tapStart))
            self.tempo.emit(bpm)
        else:
            self.tapStart = self.tapTime
            self.tapCount = 0


