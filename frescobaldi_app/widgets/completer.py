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
Completer providing completions in a Q(Plain)TextEdit.
"""


from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Completer(QCompleter):
    """A QCompleter providing completions in a Q(Plain)TextEdit.
    
    Use setTextEdit() to assign the completer to a text edit.
    
    """
    def __init__(self):
        super(Completer, self).__init__()
    
    def setTextEdit(self, edit):
        """Sets the completer to work on the given edit.
        
        Use None to remove our binding from any textedit.
        
        """
        old = self.widget()
        if old:
            old.cursorPositionChanged.disconnect(self.slotCursorPositionChanged)
        self.setWidget(edit)
        if edit:
            edit.cursorPositionChanged.connect(self.slotCursorPositionChanged)
    
    def eventFilter(self, obj, ev):
        isVisible = self.popup().isVisible()
        if ev.type() == QEvent.FocusOut:
            self.popup().hide()
        print ev.type()
        return False

    def slotCursorPositionChanged(self):
        """Called when the cursor position in our widget() has changed."""
        
    
