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
A dummy surface only showing a "could not load popplerqt5 module" message.
"""


from PyQt5.QtWidgets import QLabel, QLayout, QVBoxLayout, QWidget

import qpopplerview
import app


class Surface(qpopplerview.Surface):
    def __init__(self, view):
        super(Surface, self).__init__(view)
        self._msg = QLabel(openExternalLinks = True)
        layout = QVBoxLayout(sizeConstraint = QLayout.SetFixedSize)
        self.setLayout(layout)
        layout.addWidget(self._msg)
        app.translateUI(self)

    def translateUI(self):
        self._msg.setText(_("Could not load the {name} module.").format(
            name = '<a href="https://github.com/wbsoft/python-poppler-qt4">popplerqt5</a>'))

    def paintEvent(self, ev):
        QWidget.paintEvent(self, ev)
