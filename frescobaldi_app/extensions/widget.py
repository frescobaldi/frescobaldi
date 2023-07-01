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
Base ExtensionWidget for extensions
"""

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

import app

from . import ExtensionMixin

class FailedExtensionWidget(QWidget):
    """Simple placeholder widget that is used if an extension's
    Tool Panel fails to instantiate."""

    def __init__(self, parent):
        super().__init__(parent)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignHCenter)
        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)
        self.translateUI()

    def translateUI(self):
        self.label.setText(_("Tool Panel failed to load"))


class ExtensionWidget(QWidget, ExtensionMixin):
    """Convenience base class for widgets in an extension.
    Can be used as the immediate super class for a widget to be used in
    an extension that otherwise would be a QWidget. If the widget is
    something else use ExtensionMixin as secondary super class
    instead.

    The class provides additional attributes to directly interact with the
    elements of an extension, see the docstring for ExtensionMixin
    for details.
    """

    pass
