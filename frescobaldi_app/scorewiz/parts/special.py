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
Some special part types.
"""

import __builtin__

from PyQt4.QtGui import QCheckBox

from . import _base
from . import register


class Chords(_base.ChordNames, _base.Part):
    @staticmethod
    def title(_=__builtin__._):
        return _("Chord names")
    

class BassFigures(_base.Part):
    @staticmethod
    def title(_=__builtin__._):
        return _("Figured Bass")

    def createWidgets(self, layout):
        self.extenderLines = QCheckBox()
        layout.addWidget(self.extenderLines)
    
    def translateWidgets(self):
        self.extenderLines.setText(_("Use extender lines"))


class Staff(_base.Part):
    @staticmethod
    def title(_=__builtin__._):
        return _("Staff")




register(
    lambda: _("Special"),
    [
        Chords,
        BassFigures,
        Staff,
    ])
