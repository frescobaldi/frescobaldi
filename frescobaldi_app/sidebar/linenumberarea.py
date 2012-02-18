# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2012 by Wilbert Berendsen
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
The line number area to be used in a View.
"""

from PyQt4.QtGui import QApplication

import widgets.linenumberarea


class LineNumberArea(widgets.linenumberarea.LineNumberArea):
    def __init__(self, textedit):
        super(LineNumberArea, self).__init__(textedit)

    def setTextEdit(self, edit):
        """Adds ourselves to the borderlayout as well."""
        from widgets import borderlayout
        old = self.textEdit()
        super(LineNumberArea, self).setTextEdit(edit)
        if old:
            borderlayout.BorderLayout.get(old).removeWidget(self)
        if QApplication.isRightToLeft():
            side = borderlayout.RIGHT
        else:
            side = borderlayout.LEFT
        if edit:
            borderlayout.BorderLayout.get(edit).addWidget(self, side)


