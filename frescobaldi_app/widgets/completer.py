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

#TEMP
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)


from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Completer(QCompleter):
    """A QCompleter providing completions in a Q(Plain)TextEdit.
    
    Use setWidget() to assign the completer to a text edit.
    
    """
    def __init__(self, *args, **kwargs):
        super(Completer, self).__init__(*args, **kwargs)
        self.activated[QModelIndex].connect(self.insertCompletion)
        
    def eventFilter(self, obj, ev):
        key = (ev.type() == QEvent.KeyPress) and ev.key()
        if key and obj != self.widget():
            if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Escape):
                return super(Completer, self).eventFilter(obj, ev)
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                self.setCurrentRow(self.popup().currentIndex().row())
                self.insertCompletion(self.currentIndex())
                self.popup().hide()
                return True
            else:
                # deliver event and then look for the cursor position
                self.widget().event(ev)
                # TODO: check newly entered text, cursor position etc.
                return True
        return super(Completer, self).eventFilter(obj, ev)

    def insertCompletion(self, index):
        print 'insertCompletion', self.completionModel().data(index, Qt.EditRole)
        


if __name__ == "__main__":
    ap = QApplication([])
    e = QPlainTextEdit()
    e.show()
    c = Completer('een twee drie vier vijf'.split())
    c.setWidget(e)
    c.complete(QRect(10, 10, 200, 100))
    #c.setCompletionPrefix('v')
    ap.exec_()


