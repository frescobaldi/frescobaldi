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
The Quick Insert panel.
"""


import weakref

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

import actioncollection
import actioncollectionmanager
import panel


class QuickInsertPanel(panel.Panel):
    def __init__(self, mainwindow):
        super(QuickInsertPanel, self).__init__(mainwindow)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+I"))
        mainwindow.addDockWidget(Qt.LeftDockWidgetArea, self)
        self.actionCollection = QuickInsertActions(self)
        actioncollectionmanager.manager(mainwindow).addActionCollection(self.actionCollection)

    def translateUI(self):
        self.setWindowTitle(_("Quick Insert"))
        self.toggleViewAction().setText(_("Quick &Insert"))

    def createWidget(self):
        from . import widget
        return widget.QuickInsert(self)


class QuickInsertActions(actioncollection.ShortcutCollection):
    """Manages keyboard shortcuts for the QuickInsert module."""
    name = "quickinsert"
    def __init__(self, panel):
        super(QuickInsertActions, self).__init__(panel.mainwindow())
        self.panel = weakref.ref(panel)

    def createDefaultShortcuts(self):
        self.setDefaultShortcuts('staccato', [QKeySequence('Ctrl+.')])
        self.setDefaultShortcuts('spanner_slur', [QKeySequence('Ctrl+(')])
        self.setDefaultShortcuts('breathe_rcomma', [QKeySequence("Alt+'")])

    def realAction(self, name):
        return self.panel().widget().actionForName(name)

    def title(self):
        return _("Quick Insert")


