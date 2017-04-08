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
Base class for the Panels (QDockWidgets).

A Panel is instantiated on startup of Frescobaldi, but the loading of the
actual widget's module is deferred until the panel is actually shown.

In the panelmanager module, the Panels are instantiated.
"""


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractButton, QDockWidget, QLabel

import app


class Panel(QDockWidget):
    """Base class for Panels.

    You should implement __init__(), createWidget() and translateUI().

    This QDockWidget subclass implements lazy loading of the panel's widget.
    When one of sizeHint() or showEvent() is called for the first time, the
    widget is created by calling createWidget().

    """
    def __init__(self, mainwindow):
        """Implement this method to add yourself to the mainwindow.

        First call this super method as it calls the Qt constructor.

        """
        super(Panel, self).__init__(mainwindow)
        self.setObjectName(self.__class__.__name__.lower())
        app.translateUI(self)
        app.languageChanged.connect(self._setToolTips)
        self._setToolTips()

    def mainwindow(self):
        """Returns the MainWindow."""
        return self.parentWidget()

    def sizeHint(self):
        """Re-implemented to force creation of our widget."""
        self.widget()
        return super(Panel, self).sizeHint()

    def widget(self):
        """Ensures that our widget() is created and returns it."""
        w = super(Panel, self).widget()
        if not w:
            w = self.createWidget()
            self.setWidget(w)
        return w

    def instantiated(self):
        """Return True if the tool already has been loaded."""
        return bool(super(Panel, self).widget())

    def showEvent(self, ev):
        """Re-implemented to force creation of widget."""
        self.widget()

    def createWidget(self):
        """Implement this to return the widget for this tool."""
        return QLabel("<test>", self)

    def activate(self):
        """Really shows the dock widget, even if tabified or floating."""
        self.show()
        if self.mainwindow().tabifiedDockWidgets(self) or self.isFloating():
            self.raise_()

    def maximize(self):
        """Show the dockwidget floating and maximized."""
        self.setFloating(True)
        self.showMaximized()

    def translateUI(self):
        """Implement to set a title for the widget and its toggleViewAction."""
        raise NotImplementedError(
            "Please implement this method to at least set a title "
            "for the dockwidget and its toggleViewAction().")

    def _setToolTips(self):
        """Generic tool tips are set here."""
        self.setToolTip(_("Drag to dock/undock"))
        closebutton = self.findChild(QAbstractButton, 'qt_dockwidget_closebutton')
        if closebutton:
            closebutton.setToolTip(_("Close"))
        floatbutton = self.findChild(QAbstractButton, 'qt_dockwidget_floatbutton')
        if floatbutton:
            floatbutton.setToolTip(_("Dock/Undock"))


