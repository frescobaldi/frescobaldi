# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 by Wilbert Berendsen
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
Tools to edit durations of selected music.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QAction

import app
import actioncollection
import actioncollectionmanager
import plugin


class Rhythm(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        self.actionCollection = ac = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        mainwindow.currentViewChanged.connect(self.slotViewChanged)
        view = mainwindow.currentView()
        if view:
            self.slotViewChanged(view)
    
    def slotViewChanged(self, view, old=None):
        if old:
            old.selectionChanged.disconnect(self.updateActions)
        view.selectionChanged.connect(self.updateActions)
        self.updateActions()
        
    def updateActions(self):
        selection = self.mainwindow().textCursor().hasSelection()
        ac = self.actionCollection
        ac.rhythm_double.setEnabled(selection)
        ac.rhythm_half.setEnabled(selection)
        ac.rhythm_dot.setEnabled(selection)
        ac.rhythm_undot.setEnabled(selection)
        ac.rhythm_remove_scaling.setEnabled(selection)
        ac.rhythm_remove.setEnabled(selection)
        ac.rhythm_implicit.setEnabled(selection)
        ac.rhythm_implicit_per_line.setEnabled(selection)
        ac.rhythm_explicit.setEnabled(selection)
        ac.rhythm_apply.setEnabled(selection)
        ac.rhythm_copy.setEnabled(selection)
        ac.rhythm_paste.setEnabled(selection)








class Actions(actioncollection.ActionCollection):
    name = "rhythm"
    def createActions(self, parent):
        self.rhythm_double = QAction(parent)
        self.rhythm_half = QAction(parent)
        self.rhythm_dot = QAction(parent)
        self.rhythm_undot = QAction(parent)
        self.rhythm_remove_scaling = QAction(parent)
        self.rhythm_remove = QAction(parent)
        self.rhythm_implicit = QAction(parent)
        self.rhythm_implicit_per_line = QAction(parent)
        self.rhythm_explicit = QAction(parent)
        self.rhythm_apply = QAction(parent)
        self.rhythm_copy = QAction(parent)
        self.rhythm_paste = QAction(parent)
    
    def translateUI(self):
        self.rhythm_double.setText(_("Double durations"))
        self.rhythm_double.setToolTip(_(
            "Double all the durations in the selection."))
        self.rhythm_half.setText(_("Halve durations"))
        self.rhythm_half.setToolTip(_(
            "Halve all the durations in the selection."))
        self.rhythm_dot.setText(_("Dot durations"))
        self.rhythm_dot.setToolTip(_(
            "Add a dot to all the durations in the selection."))
        self.rhythm_undot.setText(_("Undot durations"))
        self.rhythm_undot.setToolTip(_(
            "Remove one dot from all the durations in the selection."))
        self.rhythm_remove_scaling.setText(_("Remove scaling"))
        self.rhythm_remove_scaling.setToolTip(_(
            "Remove all scaling (*n/m) from the durations in the selection."))
        self.rhythm_remove.setText(_("Remove durations"))
        self.rhythm_remove.setToolTip(_(
            "Remove all durations from the selection."))
        self.rhythm_implicit.setText(_("Make implicit"))
        self.rhythm_implicit.setToolTip(_(
            "Make durations implicit (remove repeated durations)."))
        self.rhythm_implicit_per_line.setText(_("Make implicit (per line)"))
        self.rhythm_implicit_per_line.setToolTip(_(
            "Make durations implicit (remove repeated durations), "
            "except for the first duration in a line."))
        self.rhythm_explicit.setText(_("Make explicit"))
        self.rhythm_explicit.setToolTip(_(
            "Make durations explicit (add duration to every note, "
            "even if it is the same as the preceding note)."))
        self.rhythm_apply.setText(_("Apply rhythm..."))
        self.rhythm_apply.setToolTip(_(
            "Apply an entered rhythm to the selected music."))
        self.rhythm_copy.setText(_("Copy rhythm"))
        self.rhythm_copy.setToolTip(_(
            "Copy the rhythm of the selected music."))
        self.rhythm_paste.setText(_("Paste rhythm"))
        self.rhythm_paste.setToolTip(_("Paste a rhythm to the selected music."))


