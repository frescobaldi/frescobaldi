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
    """Convenience base class for widgets in an extension.
    Can be used as the immediate super class for a widget to be used in
    an extension. Alternatively it can be the secondary super class if
    another widget (e.g. a QTabWidget) is preferred.

    The class provides additional attributes to directly interact with the
    elements of an extension, such as the main Extension object, the settings,
    the mainwindow etc.

    If the 'parent' has an 'extension()' attribute (which is for example true
    when the widget is instantiated as an extension's panel widget) this
    is implicitly made available within the widget. Otherwise the subclass
    must specify the '_extension_name' class variable, exactly using the
    name matching the extension directory. This is true for additional widgets
    that may be used *within* the panel widget or in widgets used in newly
    created dialogs etc.
    """

    _extension_name = ''

    def __init__(self, parent=None):
        super(ExtensionWidget, self).__init__(parent)

    def extension(self):
        """Return the actual Extension object if possible."""
        if hasattr(self.parent(), 'extension'):
            # The parent has access to the extension (typically the Panel)
            return self.parent().extension()
        elif self._extension_name:
            return app.extensions().get(self._extension_name)
        else:
            raise AttributeError(_(
                "Class '{classname}' can't access Extension object. "
                "It should provide an _extension_name class variable."
                ).format(classname=self.__name__))

# More properties are accessed through the extension() property

    def action_collection(self):
        """Return the extension's action collection."""
        return self.extension().action_collection()

    def current_document(self):
        """Return the current document."""
        return self.extension().current_document()

    def mainwindow(self):
        """Return the active MainWindow."""
        return self.extension().mainwindow()

    def panel(self):
        """Return the extension's panel, or None if the widget
        is not a Panel widget and the extension does not have a panel."""
        return self.extension().panel()
