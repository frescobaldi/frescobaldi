# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import help
import icons
import symbols
import widgets.toolboxwheeler

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
            clicked = lambda: help.help(quickinsert_help))
        self.directionLabel = QLabel()
        self.direction = QComboBox()
        self.direction.addItems(['', '', ''])
        self.direction.setItemIcon(0, icons.get("arrow-up"))
        self.direction.setItemIcon(2, icons.get("arrow-down"))
        self.direction.setCurrentIndex(1)
        hor = QHBoxLayout()
        hor.setContentsMargins(0, 0, 0, 0)
        hor.addWidget(self.helpButton)
        hor.addWidget(self.directionLabel)
        hor.addWidget(self.direction)
        layout.addLayout(hor)
        
        self.toolbox = QToolBox(self)
        widgets.toolboxwheeler.ToolBoxWheeler(self.toolbox)
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
        help.openWhatsThis(self)
        
        # restore remembered current page
        name = QSettings().value("quickinsert/current_tool", "")
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
                quickinsert_help.link()))
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


class quickinsert_help(help.page):
    def title():
        return _("The Quick Insert Panel")
    
    def body():
        return (_("""\
<p>
With the tools in the Quick Insert Panel you can add various music elements
to the current note or selected music.
</p>

<p>
The <em>Direction</em> chooser specifies if articulations, dynamics or slurs
appear in a neutral position (e.g. determined by stem direction), or above
or below the staff by prepending a <code>-</code>, <code>^</code> or
<code>_</code> character.
</p>

<p>
Click on a tab to select a tool. You can cycle through the tools with Ctrl
(or {command}) and the mouse wheel.
All buttons in the Quick Insert Panel have configurable keyboard shortcuts;
you can change them by right-clicking a button.
</p>
""").format(command="\u2318") + ("""\
<h3>Articulations</h3>

<p>
These musical symbols can be added to a note or rest or a selected range
of music.
If you add them to a selection, rests will be skipped.
If there is no text selected, the cursor will automatically move to the next
pitch, rest, skip or chord.
</p>

<p>
If <em>Allow shorthands</em> is checked, Frescobaldi will use short signs
for articulations if they exist
(e.g. <code>-.</code> instead of <code>-\staccato</code>).
</p>
""") + ("""\
<h3>Dynamics</h3>

<p>
Dynamics can also be added to a note or rest.
If you select a range of music, you can add spanners which will automatically
terminate at the last note, rest or chord in the selection.
If you then click a sign, it will replace the terminator.
</p>
""") + ("""\
<h3>Spanners</h3>

<p>
This tool lets you add arpeggio, glissandos and other spanners like slurs,
phrasing slurs, manual beams or trills.
</p>

<p>
Arpeggios and glissandos apply to the current note;
they need no music to be selected.
The slurs, beams or trill apply to the current note and the next one
if no music is selected,
or to the first and the last note or chord in the selection.
</p>
""") + ("""\
<h3>Bar Lines</h3>

<p>
Here you can insert bar lines or various breathing signs.
</p>
"""))


