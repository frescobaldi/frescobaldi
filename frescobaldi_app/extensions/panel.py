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
Base ExtensionPanel for extensions
"""

import panel

class ExtensionPanel(panel.Panel):
    """Base class for an Extension Tool Panel.
    It is a lightweight layer around the regular panel.Panel,
    its only purpose being to act as a bridge to ExtensionWidget and
    descendants.
    """
    def __init__(self, extension, widget_class, dock_area):
        self._extension = extension
        self._widget_class = widget_class
        super(ExtensionPanel, self).__init__(extension.mainwindow())
        self.hide()
        self.mainwindow().addDockWidget(dock_area, self)

    def createWidget(self):
        """Create the panel's widget.
        *If* an ExtensionPanel is actually instantiated it also has
        information about it's widget class, which we use here."""
        return self._widget_class(self)

    def translateUI(self):
        self.setWindowTitle(self.extension().display_name())

    def extension(self):
        return self._extension
