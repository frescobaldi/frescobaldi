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
Some useful tools dealing with popplerqt5 (PDF) documents.
"""

import os


class Document(object):
    """Represents a (lazily) loaded PDF document."""
    def __init__(self, filename=''):
        self._filename = filename
        self._document = None
        self._dirty = True

    def filename(self):
        """Returns the filename, set on init or via setFilename()."""
        return self._filename

    def setFilename(self, filename):
        """Sets a filename.

        The document will be reloaded next time it is requested.

        """
        self._filename = filename
        self._dirty = True

    def name(self):
        """Returns the filename without path."""
        return os.path.basename(self._filename)

    def document(self):
        """Returns the PDF document the filename points to, reloading if the filename was set.

        Can return None, in case the document failed to load.

        """
        if self._dirty:
            self._document = self.load()
            self._dirty = False
        return self._document

    def load(self):
        """Should load and return the popplerqt5 Document for our filename."""
        try:
            import popplerqt5
        except ImportError:
            return
        return popplerqt5.Poppler.Document.load(self._filename)


