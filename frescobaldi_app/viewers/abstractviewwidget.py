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
Abstract base for viewer widgets
"""

from PyQt5.QtWidgets import QWidget


class AbstractViewWidget(QWidget):
    """Widget containing an abstract viewer widget."""
    pass

    # This serves as a stub for a future base class.
    # It will have to contain the complete interface for generic viewer
    # widgets and any implementation that is not specific to the viewer's
    # technology (Poppler/QWebView or whatever).
    #
    # The idea is to have a consistent interface (with regard to toolbar,
    # navigation, contextmenu etc.) throughout all viewers
    #
    # Currently all code is in AbstractPopplerWidget, but we will have to
    # move as much as possible up to the current base class ASAP.
