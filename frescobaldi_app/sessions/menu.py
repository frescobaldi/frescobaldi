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
        self.groupMenus = []

    def translateUI(self):
        self.setTitle(_('menu title', '&Session'))

    def populate(self):
        groups = {}
        tl_sessions = []

        def add_session(menu, name, group=None):
            name = name.replace('&', '&&')
            fullname = group + '/' + name if group else name
            a = menu.addAction(name)
            a.setCheckable(True)
            if fullname == sessions.currentSession():
                a.setChecked(True)
                if group:
                    menu.setTitle('* ' + menu.title())
            a.setObjectName(fullname)
            self._actionGroup.addAction(a)

        def add_sessions():
            for name in tl_sessions:
                add_session(self, name)

        def add_groups():
            for k in sorted(groups.keys()):
                m = self.addMenu(k)
                self.groupMenus.append(m)
                for name in groups[k]:
                    add_session(m, name, k)
                qutil.addAccelerators(m.actions())

        def reset_menu():
            for m in self.groupMenus:
                m.deleteLater()
            self.groupMenus = []
            ac = manager.get(self.parentWidget()).actionCollection
            ag = self._actionGroup
            for a in ag.actions():
                if a is not ac.session_none:
                    self.removeAction(a)
                    ag.removeAction(a)
            ac.session_none.setChecked(not sessions.currentSession())

        reset_menu()
        for name in sessions.sessionNames():
            if '/' in name:
                group, name = name.split('/')
                if group in groups:
                    groups[group].append(name)
                else:
                    groups[group] = [name]
            else:
                tl_sessions.append(name)
        add_groups()
        if groups:
            self.addSeparator()
        add_sessions()
        qutil.addAccelerators(self.actions())

    def slotSessionsAction(self, action):
        if action.objectName() in sessions.sessionNames():
            manager.get(self.parentWidget()).startSession(action.objectName())
