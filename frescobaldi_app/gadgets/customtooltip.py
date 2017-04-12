# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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


from PyQt5.QtCore import QEvent, QObject, QTimer, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication


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
        QApplication.instance().removeEventFilter(_handler)

def show(widget, pos=None, timeout=10000):
    """Show the widget at position."""
    if pos is None:
        pos = QCursor.pos()
    global _widget
    if _widget:
        if _widget is not widget:
            _widget.hide()
    else:
        global _handler
        if _handler is None:
            _handler = EventHandler()
        QApplication.instance().installEventFilter(_handler)

    # where to display the tooltip
    screen = QApplication.desktop().availableGeometry(pos)
    x = pos.x() + 2
    y = pos.y() + 20
    if x + widget.width() > screen.x() + screen.width():
        x -= 4 + widget.width()
    if y + widget.height() > screen.y() + screen.height():
        y -= 24 + widget.height()
    if y < screen.y():
        y = screen.y()
    if x < screen.x():
        x = screen.x()
    widget.move(x, y)
    if widget.windowFlags() & Qt.ToolTip != Qt.ToolTip:
        widget.setWindowFlags(Qt.ToolTip)
        widget.ensurePolished()

    widget.show()
    _widget = widget
    _timer.start(timeout)


_hideevents = {
    QEvent.KeyPress,
    QEvent.KeyRelease,
    QEvent.Leave,
    QEvent.WindowActivate,
    QEvent.WindowDeactivate,
    QEvent.MouseButtonPress,
    QEvent.MouseButtonRelease,
    QEvent.MouseButtonDblClick,
    QEvent.FocusIn,
    QEvent.FocusOut,
    QEvent.Wheel,
    QEvent.MouseMove,
}

class EventHandler(QObject):
    def eventFilter(self, obj, ev):
        if ev.type() in _hideevents:
            hide()
        return False



# setup
_timer.timeout.connect(hide)


