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
Some special part types.
"""


from PyQt5.QtWidgets import QCheckBox

import ly.dom

from . import _base
from . import register


class Chords(_base.ChordNames, _base.Part):
    @staticmethod
    def title(_=_base.translate):
        return _("Chord names")


class BassFigures(_base.Part):
    @staticmethod
    def title(_=_base.translate):
        return _("Figured Bass")

    def createWidgets(self, layout):
        self.extenderLines = QCheckBox()
        layout.addWidget(self.extenderLines)

    def translateWidgets(self):
        self.extenderLines.setText(_("Use extender lines"))

    def build(self, data, builder):
        a = data.assign('figBass')
        s = ly.dom.FigureMode(a)
        p = ly.dom.FiguredBass()
        ly.dom.Identifier(a.name, p)
        ly.dom.Identifier(data.globalName, s)
        ly.dom.LineComment(_("Figures follow here."), s)
        ly.dom.BlankLine(s)
        if self.extenderLines.isChecked():
            p.getWith()['useBassFigureExtenders'] = ly.dom.Scheme('#t')
        data.nodes.append(p)


class Staff(_base.Part):
    @staticmethod
    def title(_=_base.translate):
        return _("Staff")




register(
    lambda: _("Special"),
    [
        Chords,
        BassFigures,
        #Staff,
    ])
