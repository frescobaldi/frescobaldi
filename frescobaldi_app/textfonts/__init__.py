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

from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import plugin

def textfonts(mainwindow):
    return TextFonts.instance(mainwindow)

class TextFonts(plugin.MainWindowPlugin):

    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.engrave_show_available_fonts.triggered.connect(self.showAvailableFonts)

    def showAvailableFonts(self):
        """Menu action Show Available Fonts."""
        from engrave import command
        info = command.info(self.mainwindow().currentDocument())
        from . import availablefonts
        availablefonts.show_available_fonts(self.mainwindow(), info)


class Actions(actioncollection.ActionCollection):
    name = "textfonts"

    def createActions(self, parent=None):
        self.engrave_show_available_fonts = QAction(parent)

    def translateUI(self):
        self.engrave_show_available_fonts.setText(_("Show Available &Fonts..."))
