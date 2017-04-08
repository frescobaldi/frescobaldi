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
The preview mode options.
"""


import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

import panel

# dictionary mapping internal option names to command line switches
_debugmodes = {
    'annotate-spacing':
        ('-ddebug-annotate-spacing',
        lambda: _("Annotate Spacing"),
        lambda: _("Use LilyPond's \"annotate spacing\" option to\n"
          "display measurement information")),
    'control-points':
        ('-ddebug-control-points',
        lambda: _("Display Control Points"),
        lambda: _("Display the control points that "
          "determine curve shapes")),
    'directions':
        ('-ddebug-directions',
        lambda: _("Color explicit directions"),
        lambda: _("Highlight elements that are explicitly switched up- or downwards")),
    'grob-anchors':
        ('-ddebug-grob-anchors',
        lambda: _("Display Grob Anchors"),
        lambda: _("Display a dot at the anchor point of each grob")),
    'grob-names':
        ('-ddebug-grob-names',
        lambda: _("Display Grob Names"),
        lambda: _("Display the name of each grob")),
    'paper-columns':
        ('-ddebug-paper-columns',
        lambda: _("Display Paper Columns"),
        lambda: _("Display info on the paper columns")),
    'skylines':
        ('-ddebug-display-skylines',
        lambda: _("Display Skylines"),
        lambda: _("Display the skylines that LilyPond "
          "uses to detect collisions.")),
    'voices':
        ('-ddebug-voices',
        lambda: _("Color \\voiceXXX"),
        lambda: _("Highlight notes that are explicitly "
        "set to \\voiceXXX")),
}

def modelist():
    """
    Return the names of the debug modes in defined order
    """
    yield 'control-points'
    yield 'voices'
    yield 'directions'
    yield 'grob-anchors'
    yield 'grob-names'
    yield 'skylines'
    yield 'paper-columns'
    yield 'annotate-spacing'

def option(mode):
    """
    Return the command line option for a key
    """
    return _debugmodes[mode][0]

def label(mode):
    """
    Return the label of a mode as a translatable string
    """
    return _debugmodes[mode][1]()

def tooltip(mode):
    """
    Return the tooltip of a mode as a translatable string
    """
    return _debugmodes[mode][2]()


class LayoutControlOptions(panel.Panel):
    def __init__(self, mainwindow):
        super(LayoutControlOptions, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+C"))
        mainwindow.addDockWidget(Qt.LeftDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("Layout Control Options"))
        self.toggleViewAction().setText(_("Layout &Control Options"))

    def createWidget(self):
        from . import widget
        w = widget.Widget(self)
        return w


