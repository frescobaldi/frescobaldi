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
The Quick Insert panel widget.
"""


import weakref

from PyQt5.QtWidgets import QVBoxLayout, QWidget


class Tool(QWidget):
    """Base class for a tool in the quick insert panel toolbox.

    """
    def __init__(self, panel):
        super(Tool, self).__init__(panel)
        self._panel = weakref.ref(panel)
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

    def panel(self):
        """Returns the panel."""
        return self._panel()

    def icon(self):
        """Should return an icon for our tab."""
        pass

    def title(self):
        """Should return a title for our tab."""
        pass

    def tooltip(self):
        """Should return a tooltip for our tab."""
        pass

