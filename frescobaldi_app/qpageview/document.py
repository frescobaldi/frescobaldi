# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
Document, a simple class representing a group of pages.

It is certainly not necessary to use a Document to handle pages in a View,
but it might be convenient in some cases.

A Document has either one filename for multiple pages, OR a filename
for every Page.

Instead of a filename, any object can be used as data source. Depending
on the page type, a QIODevice or QByteArray could be used.

"""


class AbstractDocument:
    """A Document represents a group of pages that belong together in some way.

    Inherit from this class and implement createPage() and load().
    The type of data objects you would use depend on the type of content you
    want to display.

    A page can be loaded from a filename or a data source. Both can be set
    using either setSource (for the whole document) or setSources (for every
    page). setFilename and setFilenames are synomyms of the setSource and
    setSources methods.

    The source() and sources() methods return the sources for either the whole
    document or every page. The filename() and filenames() do the same, but
    instead return an empty string for non-string source objects.

    """
    def __init__(self, renderer=None):
        self.renderer = None
        self._pages = None
        self._source = None
        self._sources = []

    def count(self):
        """Return the number of pages."""
        return len(self.pages())

    def pages(self):
        """Return the list of Pages, creating them at first call."""
        if self._pages is None:
            self._pages = list(self.createPages())
        return self._pages

    def source(self):
        """Return a data object that might be set for the whole document."""
        return self._source

    def setSource(self, source):
        """Set the data object for the whole document. Invalidates the document."""
        self.clear()
        self._source = source

    def sources(self):
        """Return data objects for every page."""
        return self._sources

    def setSources(self, sources):
        """Set data objects for every page. Invalidates the document."""
        self.clear()
        self._sources = sources

    def filename(self):
        """Return the file name applying to the whole document."""
        if isinstance(self._source, str):
            return self._source

    setFilename = setSource

    def filenames(self):
        """Return the list of file names of every page."""
        return [f if isinstance(f, str) else "" for f in self._sources]

    setFilenames = setSources

    def invalidate(self):
        """Delete all cached pages, except for filenames or data objects."""
        self._pages = None

    def clear(self):
        """Delete all caches pages, and filenames and data objects."""
        self._pages = None
        self._source = None
        self._sources = []

    def createPages(self):
        """Implement this method to create and yield the pages.

        This method is only called once. After altering filename,-s or
        source,-s, or invalidate(), it is called again.

        """
        return NotImplemented


