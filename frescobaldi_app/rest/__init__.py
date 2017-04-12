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
Tools to edit rests of selected music.
"""


from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import plugin


class Rest(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        self.actionCollection = ac = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.rest_fmrest2spacer.triggered.connect(self.fmrest2spacer)
        ac.rest_spacer2fmrest.triggered.connect(self.spacer2fmrest)
        ac.rest_restcomm2rest.triggered.connect(self.restcomm2rest)

    def fmrest2spacer(self):
        from . import rest
        cursor = self.mainwindow().textCursor()
        rest.fmrest2spacer(cursor)

    def spacer2fmrest(self):
        from . import rest
        cursor = self.mainwindow().textCursor()
        rest.spacer2fmrest(cursor)

    def restcomm2rest(self):
        from . import rest
        cursor = self.mainwindow().textCursor()
        rest.restcomm2rest(cursor)


class Actions(actioncollection.ActionCollection):
    name = "rest"
    def createActions(self, parent):
        self.rest_fmrest2spacer = QAction(parent)
        self.rest_spacer2fmrest = QAction(parent)
        self.rest_restcomm2rest = QAction(parent)

    def translateUI(self):
        self.rest_fmrest2spacer.setText(_(
            "Replace full measure rests with spacer rests"))
        self.rest_fmrest2spacer.setToolTip(_(
            "Change all R to s "
            "in this document or in the selection."))
        self.rest_spacer2fmrest.setText(_(
            "Replace spacer rests with full measure rests"))
        self.rest_spacer2fmrest.setToolTip(_(
            "Change all s to R "
            "in this document or in the selection."))
        self.rest_restcomm2rest.setText(_(
            "Replace positioned rests with plain rests"))
        self.rest_restcomm2rest.setToolTip(_(
            "Change all \\rest with r "
            "in this document or in the selection."))

