# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright 2011 by Wilbert Berendsen
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
The MIDI tool widget.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import css


class Widget(QWidget):
    def __init__(self, dockwidget):
        super(Widget, self).__init__(dockwidget)
        
        self._fileSelector = QComboBox(editable=True)
        self._fileSelector.lineEdit().setReadOnly(True)
        self._fileSelector.lineEdit().setFocusPolicy(Qt.NoFocus)
        self._stopButton = QToolButton()
        self._playButton = QToolButton()
        self._timeSlider = QSlider(Qt.Horizontal, tracking=False)
        self._timeDisplay = QLabel(alignment=Qt.AlignRight|Qt.AlignVCenter)
        self._tempoFactor = QSlider(Qt.Vertical, minimum=-120, maximum=120)
        
        self._timeDisplay.setStyleSheet(css.lcd_screen)
        
        grid = QGridLayout(spacing=0)
        self.setLayout(grid)
        
        grid.addWidget(self._fileSelector, 0, 0, 1, 3)
        grid.addWidget(self._stopButton, 1, 0)
        grid.addWidget(self._playButton, 1, 1)
        grid.addWidget(self._timeSlider, 1, 2)
        grid.addWidget(self._timeDisplay, 2, 0, 1, 3)
        grid.addWidget(self._tempoFactor, 0, 3, 3, 1)
        
        app.translateUI(self)

    def translateUI(self):
        self.updateTimeDisplay()

    def updateTimeDisplay(self):
        """Updates the display of time, etc."""
        self._timeDisplay.setText(_lcd_text.format(
            _("midi lcd screen", "TIME"),
            _("midi lcd screen", "BEAT"),
            " 5:19",
            "24. 1",
        ))




_lcd_text = """\
<table width=100% border=0>
<tr>
<td align=right style="font-size:8px;">{0}</td>
<td align=right style="font-size:8px;">{1}</td>
</tr>
<tr>
<td align=right><h2>{2}</h2></td>
<td align=right><h2>{3}</h2></td>
</tr>
</table>"""

