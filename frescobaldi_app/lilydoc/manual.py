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
A Manual manages a searchable index for a LilyPond manual.
"""



from PyQt5.QtCore import QObject, QUrl, pyqtSignal


class Manual(QObject):

    loaded = pyqtSignal(bool)

    def __init__(self, lilydoc):
        self._loaded = None

    def isLoaded(self):
        """True: successfully loaded, False: load failed, None: load pending."""
        return self._loaded



class NotationManual(Manual):
    """Represents the Notation Manual."""


class LearningManual(Manual):
    """Represents the Learning Manual."""


class InternalsReference(Manual):
    """Represents the Internals Reference."""



