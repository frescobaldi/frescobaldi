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


class Document:
    """A Document represents a group of pages that belong together in some way.

    Add pages by manipulating the list returned by pages().

    """
    def __init__(self, pages=()):
        self._pages = []
        self._pages.extend(pages)

    def count(self):
        """Return the number of pages."""
        return len(self.pages())

    def pages(self):
        """Return the list of pages."""
        return self._pages

    def clear(self):
        """Empties the document."""
        self._pages.clear()

    def filename(self):
        """Return the filename of the document."""

    def filenames(self):
        """Return the list of filenames, for multi-file documents."""


class AbstractFileDocument(Document):
    """A Document that loads pages from external source, such as a file.

    The pages are loaded on first request, and invalidate can be called
    to trigger a reload.

    """
    def __init__(self, renderer=None):
        self.renderer = renderer
        self._pages = None

    def count(self):
        """Return the number of pages."""
        return len(self.pages())

    def pages(self):
        """Return the list of Pages, creating them at first call."""
        if self._pages is None:
            self._pages = list(self.createPages())
        return self._pages

    def invalidate(self):
        """Delete all cached pages, except for filename(s) or source object(s)."""
        self._pages = None

    def createPages(self):
        """Implement this method to create and yield the pages.

        This method is only called once. After altering filename,-s or
        source,-s, or invalidate(), it is called again.

        """
        return NotImplemented


class SingleFileDocument(AbstractFileDocument):
    """A Document that loads its pages from a single file or source."""
    def __init__(self, source=None, renderer=None):
        super().__init__(renderer)
        self._source = source

    def source(self):
        """Return a data object that might be set for the whole document."""
        return self._source

    def setSource(self, source):
        """Set the data object for the whole document. Invalidates the document."""
        self.clear()
        self._source = source

    def filename(self):
        """Return the file name applying to the whole document."""
        return self._source if isinstance(self._source, str) else ""

    setFilename = setSource

    def clear(self):
        """Delete all caches pages, and clear filename or source object."""
        self._pages = None
        self._source = None


class MultiFileDocument(AbstractFileDocument):
    """A Document that loads every page from its own file or source."""
    def __init__(self, sources=(), renderer=None):
        super().__init__(renderer)
        self._sources = []
        self._sources.extend(sources)

    def sources(self):
        """Return data objects for every page."""
        return self._sources

    def setSources(self, sources):
        """Set data objects for every page. Invalidates the document."""
        self.clear()
        self._sources = sources

    def filenames(self):
        """Return the list of file names of every page."""
        return [f if isinstance(f, str) else "" for f in self._sources]

    setFilenames = setSources

    def clear(self):
        """Delete all caches pages, and clear filenames or source objects."""
        self._pages = None
        self._sources = []


