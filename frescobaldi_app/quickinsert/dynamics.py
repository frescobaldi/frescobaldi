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
The Quick Insert panel dynamics Tool.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import symbols

import tool
import buttongroup


class Dynamics(tool.Tool):
    """Dynamics tool in the quick insert panel toolbox."""
    def __init__(self, panel):
        super(Dynamics, self).__init__(panel)
        self.layout().addWidget(DynamicGroup(self))
        self.layout().addWidget(SpannerGroup(self))
        self.layout().addStretch(1)

    def icon(self):
        """Should return an icon for our tab."""
        return symbols.icon("dynamic_f")
    
    def title(self):
        """Should return a title for our tab."""
        return _("Dynamics")
  
    def tooltip(self):
        """Returns a tooltip"""
        return _("Dynamic symbols.")


class DynamicGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        # L10N: dynamic signs
        self.setTitle(_("Signs"))
    
    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for m in dynamic_marks:
            name = 'dynamic_' + m
            yield name, symbols.icon(name), None
    
    def actionTexts(self):
        """Should yield name, text for very action."""
        for m in dynamic_marks:
            name = 'dynamic_' + m
            bold = "<b><i>{0}</i></b>".format
            yield name, _("Dynamic sign {name}").format(name=bold(m))
        
    def actionTriggered(self, name):
        print 'dynamic:', name


class SpannerGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Spanners"))
    
    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None
    
    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'dynamic_hairpin_cresc', _("Hairpin crescendo")
        yield 'dynamic_cresc', _("Crescendo")
        yield 'dynamic_hairpin_dim', _("Hairpin diminuendo")
        yield 'dynamic_dim', _("Diminuendo")
        yield 'dynamic_decresc', _("Decrescendo")
        
    def actionTriggered(self, name):
        print 'dynamic:', name


dynamic_marks = (
    'f', 'ff', 'fff', 'ffff', 'fffff',
    'p', 'pp', 'ppp', 'pppp', 'ppppp',
    'mf', 'mp', 'fp', 'sfz', 'rfz',
    'sf', 'sff', 'sp', 'spp',
)


