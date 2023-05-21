# -*- coding: utf-8 -*-
#
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

The Document class can be used to manually build a document consisting of
a group of pages, that can be specified on construction or added to the list
returned by the Document.pages() method.

Then two subtypes exist, SingleSourceDocument and MultiSourceDocument, that can be
subclassed into document types that either load every Page from a single file
or, respectively, load all pages from one filename.

Instead of a filename, any object can be used as data source. Depending
on the page type, a QIODevice or QByteArray could be used.

Instantiating a Document is very fast, as nothing is loaded or computed on
instantiation. Only when pages() is called for the first time, file contents
are loaded, which normally happens when a Document is shown in a View using
View.setDocument().

"""


class Document:
    """A Document represents a group of pages that belong together in some way.

    Add pages on creation or by manipulating the list returned by pages().

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
        """Return the filename of the document.

        The default implementation returns an empty string.

        """
        return ""

    def filenames(self):
        """Return the list of filenames, for multi-file documents.

        The default implementation returns an empty list.

        """
        return []

    def urls(self):
        """Return a dict, mapping URLs (str) to areas on pages.

        This method queries the links of all pages, and if they have a URL, the
        area attribute of that link is added to a list for every page, and
        every unique URL is mapped to a dict, that maps page number to the list
        of areas on that page (page numbers start with 0).

        In the returned dict you can quickly find the areas in which a URL
        appears in a link.

        """
        urls = {}
        for n, p in enumerate(self.pages()):
            for link in p.links():
                url = link.url
                if url:
                    urls.setdefault(url, {}).setdefault(n, []).append(link.area)
        return urls

    def addUrls(self, urls):
        """Read the dict (such as returned by urls()) and make clickable links.

        This can be used to add url-links to a document from another document,
        e.g. when a document represents the same content, but has no clickable
        links (e.g. images). Links on pages with a higher number than our number
        of pages are skipped.

        """
        from .link import Link
        for url, dests in urls.items():
            for n, areas in dests.items():
                if 0 <= n < self.count():
                    links = self.pages()[n].links()
                    links.bulk_add(Link(*area, url=url) for area in areas)


class AbstractSourceDocument(Document):
    """A Document that loads pages from external source, such as a file.

    The pages are loaded on first request, and invalidate can be called
    to trigger a reload.

    """
    def __init__(self, renderer=None):
        self.renderer = renderer
        self._pages = None
        self._urls = None

    def pages(self):
        """Return the list of Pages, creating them at first call."""
        if self._pages is None:
            self._pages = list(self.createPages())
        return self._pages

    def invalidate(self):
        """Delete all cached pages, except for filename(s) or source object(s).

        Also called internally by clear().

        """
        self._pages = None
        self._urls = None

    def clear(self):
        """Delete all cached pages, and clear filename(s) or source object(s)."""
        self.invalidate()

    def createPages(self):
        """Implement this method to create and yield the pages.

        This method is only called once. After altering filename,-s or
        source,-s, or invalidate(), it is called again.

        """
        return NotImplemented

    def urls(self):
        """Reimplemented to cache the urls returned by Document.urls()."""
        if self._urls == None:
            self._urls = super().urls()
        return self._urls


class SingleSourceDocument(AbstractSourceDocument):
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
        """Delete all cached pages, and clear filename or source object."""
        self.invalidate()
        self._source = None


class MultiSourceDocument(AbstractSourceDocument):
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
        self._sources[:] = sources

    def filenames(self):
        """Return the list of file names of every page."""
        return [f if isinstance(f, str) else "" for f in self._sources]

    setFilenames = setSources

    def clear(self):
        """Delete all cached pages, and clear filenames or source objects."""
        self.invalidate()
        self._sources = []


