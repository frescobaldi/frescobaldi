# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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

from __future__ import unicode_literals

from PyQt4.QtCore import Qt, QSettings
from PyQt4.QtGui import QKeySequence
import sys, panel

def load_bool_option(s, key):
    """
    Load a boolean option from QSettings s.
    Ensure that the result is a Boolean
    (PyQt bug)
    """
    val = s.value(key, True)
    if isinstance(val, bool):
        return val
    else:
        return True if val.upper() == "TRUE" else False

def load_options():
    """Load preview options at least once at program startup"""
    s = QSettings()
    s.beginGroup("lilypond_settings")
    load_bool_option(s, 'skylines')
    load_bool_option(s, 'control-points')
    load_bool_option(s, 'voices')
    load_bool_option(s, 'directions')

class PreviewOptions(panel.Panel):
    def __init__(self, mainwindow):
        super(PreviewOptions, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+V"))
        mainwindow.addDockWidget(Qt.LeftDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("Preview Options"))
        self.toggleViewAction().setText(_("Pre&view Options"))
        
    def createWidget(self):
        from . import widget
        w = widget.Widget(self)
        return w
