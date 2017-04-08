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
An Object Editor
"""

# Note: This is only a very first stub


import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

import panel

class ObjectEditor(panel.Panel):
    def __init__(self, mainwindow):
        super(ObjectEditor, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+E"))
        mainwindow.addDockWidget(Qt.LeftDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("Object Editor"))
        self.toggleViewAction().setText(_("O&bject Editor"))

    def createWidget(self):
        from . import widget
        w = widget.Widget(self)
        return w


