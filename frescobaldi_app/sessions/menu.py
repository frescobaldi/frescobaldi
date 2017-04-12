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
Session menu.
"""


from PyQt5.QtWidgets import QActionGroup, QMenu

import app
import qutil
import sessions

from . import manager


class SessionMenu(QMenu):
    def __init__(self, mainwindow):
        super(SessionMenu, self).__init__(mainwindow)
        app.translateUI(self)
        mgr = manager.get(mainwindow)
        ac = mgr.actionCollection
        ag = self._actionGroup = QActionGroup(self)
        ag.setExclusive(True)
        ag.addAction(ac.session_none)
        ag.triggered.connect(self.slotSessionsAction)
        self.addAction(ac.session_new)
        self.addAction(ac.session_save)
        self.addSeparator()
        self.addAction(ac.session_manage)
        self.addSeparator()
        self.addAction(ac.session_none)
        self.addSeparator()
        self.aboutToShow.connect(self.populate)

    def translateUI(self):
        self.setTitle(_('menu title', '&Session'))

    def populate(self):
        ac = manager.get(self.parentWidget()).actionCollection
        ag = self._actionGroup
        for a in ag.actions():
            if a is not ac.session_none:
                self.removeAction(a)
                ag.removeAction(a)
        ac.session_none.setChecked(not sessions.currentSession())
        for name in sessions.sessionNames():
            a = self.addAction(name.replace('&', '&&'))
            a.setCheckable(True)
            if name == sessions.currentSession():
                a.setChecked(True)
            a.setObjectName(name)
            ag.addAction(a)
        qutil.addAccelerators(self.actions())

    def slotSessionsAction(self, action):
        if action.objectName() in sessions.sessionNames():
            manager.get(self.parentWidget()).startSession(action.objectName())


