# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
The Quick Insert panel widget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import symbols

import tool
import buttongroup


class Articulations(tool.Tool):
    """Articulations tool in the quick insert panel toolbox.
    
    """
    def __init__(self, panel):
        super(Articulations, self).__init__(panel)
        
        self.layout().addWidget(ArticulationsGroup(self))
        
    def icon(self):
        """Should return an icon for our tab."""
        return symbols.icon("articulation_prall")
    
    def title(self):
        """Should return a title for our tab."""
        return _("Articulations")
  
    def tooltip(self):
	"""Returns a tooltip"""
	return _("Different kinds of articulations and other signs.")


class Group(buttongroup.ButtonGroup):
    def actionData(self):
        for name, title in self.actionTexts():
            yield name, symbols.icon('articulation_'+name), None


class ArticulationsGroup(Group):
    def actionTexts(self):
        yield 'accent', _("Accent")
        yield 'marcato', _("Marcato")
        yield 'staccatissimo', _("Staccatissimo")
        yield 'staccato', _("Staccato")
        yield 'portato', _("Portato")
        yield 'tenuto', _("Tenuto")
        yield 'espressivo', _("Espressivo")
        