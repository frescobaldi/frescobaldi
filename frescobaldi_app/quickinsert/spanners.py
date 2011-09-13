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
The Quick Insert panel spanners Tool.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import symbols

import tool
import buttongroup


class Spanners(tool.Tool):
    """Dynamics tool in the quick insert panel toolbox."""
    def __init__(self, panel):
        super(Spanners, self).__init__(panel)
        self.layout().addWidget(ArpeggioGroup(self))
        self.layout().addWidget(GlissandoGroup(self))
        self.layout().addStretch(1)

    def icon(self):
        """Should return an icon for our tab."""
        return symbols.icon("slur") # TODO: icon
    
    def title(self):
        """Should return a title for our tab."""
        return _("Spanners")
  
    def tooltip(self):
        """Returns a tooltip"""
        return _("Slurs, spanners, etcetera.")


class ArpeggioGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Arpeggios"))
    
    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None
    
    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'arpeggio_normal', _("Arpeggio")
        yield 'arpeggio_arrow_up', _("Arpeggio with Up Arrow")
        yield 'arpeggio_arrow_down', _("Arpeggio with Down Arrow")
        yield 'arpeggio_bracket', _("Bracket Arpeggio")
        yield 'arpeggio_parenthesis', _("Parenthesis Arpeggio")
        
    def actionTriggered(self, name):
        print 'arpeggio:', name


class GlissandoGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Glissandos"))
    
    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None
    
    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'glissando_normal', _("Glissando")
        yield 'glissando_dashed', _("Dashed Glissando")
        yield 'glissando_dotted', _("Dotted Glissando")
        yield 'glissando_zigzag', _("Zigzag Glissando")
        yield 'glissando_trill', _("Trill Glissando")

    def actionTriggered(self, name):
        print 'glissando:', name


