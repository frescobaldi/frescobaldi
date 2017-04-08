# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Auto-completes entered text.
"""


from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import app
import actioncollection
import actioncollectionmanager
import plugin


class CompleterManager(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.autocomplete.toggled.connect(self.setAutoComplete)
        ac.popup_completions.triggered.connect(self.showCompletions)
        mainwindow.currentViewChanged.connect(self.setView)
        if mainwindow.currentView():
            self.setView(mainwindow.currentView())
        complete = QSettings().value("autocomplete", True, bool)
        ac.autocomplete.setChecked(complete)

    def setView(self, view):
        self.completer().setWidget(view)

    def completer(self):
        try:
            return self._completer
        except AttributeError:
            from . import completer
            self._completer = c = completer.Completer()
            c.autoComplete = self.actionCollection.autocomplete.isChecked()
            return self._completer

    def setAutoComplete(self, enabled):
        QSettings().setValue("autocomplete", enabled)
        self.completer().autoComplete = enabled

    def showCompletions(self):
        if self.mainwindow().currentView().hasFocus():
            self.completer().showCompletionPopup()


app.mainwindowCreated.connect(CompleterManager.instance)


class Actions(actioncollection.ActionCollection):
    name = 'autocomplete'
    def createActions(self, parent):
        self.autocomplete = QAction(parent, checkable=True)
        self.popup_completions = QAction(parent)
        self.popup_completions.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Space))

    def translateUI(self):
        self.autocomplete.setText(_("Automatic &Completion"))
        self.popup_completions.setText(_("Show C&ompletions Popup"))

