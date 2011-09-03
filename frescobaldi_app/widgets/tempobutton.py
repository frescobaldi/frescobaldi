# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

import time

from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QToolButton

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
        self.tapTime = 0.0
        self.pressed.connect(self.slotPressed)
        app.translateUI(self)
        
    def translateUI(self):
        self.setToolTip(_("Click this button a few times to set the tempo."))

    def slotPressed(self):
        self.tapTime, t = time.time(), self.tapTime
        bpm = int(60.0 / (self.tapTime - t))
        if 10 < bpm < 1000:
            self.tempo.emit(bpm)


