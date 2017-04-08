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
Help browser dockwidget.
"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import icons
import panel


class HelpBrowser(panel.Panel):
    def __init__(self, mainwindow):
        super(HelpBrowser, self).__init__(mainwindow)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+D"))
        self.hide()
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.help_lilypond_doc.triggered.connect(self.activate)

    def translateUI(self):
        self.setWindowTitle(_("Documentation Browser"))
        self.toggleViewAction().setText(_("&Documentation Browser"))

    def createWidget(self):
        from . import browser
        return browser.Browser(self)

    def activate(self):
        super(HelpBrowser, self).activate()
        self.widget().webview.setFocus()


class Actions(actioncollection.ActionCollection):
    name = "docbrowser"

    def title(self):
        return _("Documentation Browser")

    def createActions(self, parent=None):
        self.help_back = QAction(parent)
        self.help_forward = QAction(parent)
        self.help_home = QAction(parent)
        self.help_print = QAction(parent)
        self.help_lilypond_doc= QAction(parent)
        self.help_lilypond_context = QAction(parent)

        self.help_back.setIcon(icons.get("go-previous"))
        self.help_forward.setIcon(icons.get("go-next"))
        self.help_home.setIcon(icons.get("go-home"))
        self.help_lilypond_doc.setIcon(icons.get("lilypond-run"))
        self.help_print.setIcon(icons.get("document-print"))

        self.help_lilypond_doc.setShortcut(QKeySequence("F9"))
        self.help_lilypond_context.setShortcut(QKeySequence("Shift+F9"))

    def translateUI(self):
        self.help_back.setText(_("Back"))
        self.help_forward.setText(_("Forward"))
        # L10N: Home page of the LilyPond manual
        self.help_home.setText(_("Home"))
        self.help_print.setText(_("Print..."))
        self.help_lilypond_doc.setText(_("&LilyPond Documentation"))
        self.help_lilypond_context.setText(_("&Contextual LilyPond Help"))


