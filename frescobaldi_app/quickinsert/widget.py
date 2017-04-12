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
The Quick Insert panel widget.
"""


import weakref

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QToolBox,
                             QToolButton, QVBoxLayout, QWidget)

import app
import userguide.util
import icons
import symbols
import gadgets.toolboxwheeler

from . import articulations
from . import barlines
from . import dynamics
from . import spanners


class QuickInsert(QWidget):
    def __init__(self, dockwidget):
        super(QuickInsert, self).__init__(dockwidget)
        self._dockwidget = weakref.ref(dockwidget)
        # filled in by ButtonGroup subclasses
        self.actionDict = {}

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        self.helpButton = QToolButton(
            icon = icons.get("help-contents"),
            autoRaise = True,
            clicked = lambda: userguide.show("quickinsert"))
        self.directionLabel = QLabel()
        self.direction = QComboBox()
        self.direction.addItems(['', '', ''])
        self.direction.setItemIcon(0, icons.get("go-up"))
        self.direction.setItemIcon(2, icons.get("go-down"))
        self.direction.setCurrentIndex(1)
        hor = QHBoxLayout()
        hor.setContentsMargins(0, 0, 0, 0)
        hor.addWidget(self.helpButton)
        hor.addWidget(self.directionLabel)
        hor.addWidget(self.direction)
        layout.addLayout(hor)

        self.toolbox = QToolBox(self)
        gadgets.toolboxwheeler.ToolBoxWheeler(self.toolbox)
        layout.addWidget(self.toolbox)

        for cls in (
                articulations.Articulations,
                dynamics.Dynamics,
                spanners.Spanners,
                barlines.BarLines,
            ):
            widget = cls(self)
            self.toolbox.addItem(widget, widget.icon(), '')

        app.translateUI(self)
        userguide.openWhatsThis(self)

        # restore remembered current page
        name = QSettings().value("quickinsert/current_tool", "", str)
        if name:
            for i in range(self.toolbox.count()):
                if name == self.toolbox.widget(i).__class__.__name__.lower():
                    self.toolbox.setCurrentIndex(i)
                    break
        self.toolbox.currentChanged.connect(self.slotCurrentChanged)

    def slotCurrentChanged(self, index):
        name = self.toolbox.widget(index).__class__.__name__.lower()
        QSettings().setValue("quickinsert/current_tool", name)

    def translateUI(self):
        self.setWhatsThis(_(
            "<p>With the Quick Insert Panel you can add various music "
            "elements to the current note or selected music.</p>\n"
            "<p>See {link} for more information.</p>").format(link=
                userguide.util.format_link("quickinsert")))
        self.helpButton.setToolTip(_("Help"))
        self.directionLabel.setText(_("Direction:"))
        for item, text in enumerate((_("Up"), _("Neutral"), _("Down"))):
            self.direction.setItemText(item, text)
        for i in range(self.toolbox.count()):
            self.toolbox.setItemText(i, self.toolbox.widget(i).title())
            self.toolbox.setItemToolTip(i, self.toolbox.widget(i).tooltip())

    def actionForName(self, name):
        """This is called by the ShortcutCollection of our dockwidget, e.g. if the user presses a key."""
        try:
            return self.actionDict[name]
        except KeyError:
            pass

    def dockwidget(self):
        return self._dockwidget()


