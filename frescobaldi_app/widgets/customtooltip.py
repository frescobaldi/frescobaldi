# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
Displays any widget as a tooltip.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app


__all__ = ['hide', 'show']


# the currently displayed widget
_widget = None

# the timer to hide (connected later)
_timer = QTimer(singleShot=True)

# the event handler (setup later)
_handler = None


def hide():
    """Hide the currently displayed widget (if any)."""
    global _widget
    if _widget:
        _widget.hide()
        _widget = None
        app.qApp.removeEventFilter(_handler)
    
def show(widget, pos, timeout=10000):
    """Show the widget at position."""
    global _widget
    if _widget:
        if _widget is not widget:
            _widget.hide()
    else:
        global _handler
        if _handler is None:
            _handler = EventHandler()
        app.qApp.installEventFilter(_handler)
    widget.setWindowFlags(Qt.ToolTip)
    widget.move(pos + QPoint(2, 20))
    widget.show()
    _widget = widget
    _timer.start(timeout)




class EventHandler(QObject):
    def eventFilter(self, obj, ev):
        print 'event filter'
        return False



# setup
_timer.timeout.connect(hide)


