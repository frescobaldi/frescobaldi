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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

class FailedExtensionWidget(QWidget):
    """Simple placeholder widget that is used if an extension's
    Tool Panel fails to instantiate."""
    
    def __init__(self, parent):
        super(FailedExtensionWidget, self).__init__(parent)
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


class ExtensionWidget(QWidget):
    """Convenience base class for Panel widgets.
    Every Panel must provide a widget, which can be any QWidget descendant.
    However, ExtensionWidget provides a number of additional properties
    that are intended to simplify the creation of Frescobaldi extensions.

    The panel argument to the initializer provides a reference to the
    Tool panel, and through its extension() property we can transparently
    pipe through a number of properties of the extension itself.
    """

    def __init__(self, panel):
        super(ExtensionWidget, self).__init__(panel)

    def panel(self):
        """Return the extension's panel."""
        return self.parent()

    def extension(self):
        """Return the actual Extension object."""
        return self.panel().extension()

    def mainwindow(self):
        """Return the active MainWindow."""
        return self.extension().mainwindow()

    # More properties are accessed through the extension() property
    def action_collection(self):
        """Return the extension's action collection."""
        return self.extension().action_collection()

    def current_document(self):
        """Return the current document."""
        return self.extension().current_document()
