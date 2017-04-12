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
Pages through a QToolBox using the mouse wheel, by default with the
CTRL modifier.
"""

from PyQt5.QtCore import QEvent, QObject, Qt


class ToolBoxWheeler(QObject):
    """Pages through a QToolBox using the mouse wheel."""
    def __init__(self, toolbox):
        """Initializes us as eventfilter with the toolbox as parent."""
        super(ToolBoxWheeler, self).__init__(toolbox)
        self._wheeldelta = 0
        toolbox.installEventFilter(self)

    def eventFilter(self, toolbox, ev):
        if ev.type() == QEvent.Wheel and ev.modifiers() & Qt.CTRL:
            self.wheelEvent(toolbox, ev)
            return True
        return False

    def wheelEvent(self, toolbox, ev):
        self._wheeldelta -= ev.angleDelta().y()
        steps, self._wheeldelta = divmod(self._wheeldelta, 120)
        i = toolbox.currentIndex() + steps
        if 0 <= i < toolbox.count():
            toolbox.setCurrentIndex(i)


