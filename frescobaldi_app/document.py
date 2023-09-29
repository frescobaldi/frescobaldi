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
A (Frescobaldi) document.

This contains the text the user can edit in Frescobaldi. In most cases it will
be a LilyPond source file, but other file types can be used as well.

There are two different document Classes: Document and EditorDocument.
Both provide a QTextDocument with additional metadata, but the EditorDocument
provides additional handling of signals that are hooked into the Frescobaldi
GUI environment. That means: use EditorDocument for documents open in the
editor, Document for "abstract" documents, for example to pass a generated
document to a job.lilypond.LilyPondJob without implicitly creating a tab.

"""


import os

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QTextCursor, QTextDocument
from PyQt5.QtWidgets import QPlainTextDocumentLayout

import app
import util
import variables
import signals


class AbstractDocument(QTextDocument):
    """Base class for a Frescobaldi document. Not intended to be instantiated.

    Objects of subclasses can be passed to the functions in documentinfo
    or lilypondinfo etc. for additional meta information.

    """

    @classmethod
    def load_data(cls, url, encoding=None):
        """Class method to load document contents from an url.

        This is intended to open a document without instantiating one
        if loading the contents fails.

        This method returns the text contents of the url as decoded text,
        thus a unicode string.

        The line separator is always '\\n'.

        """
        filename = url.toLocalFile()

        # currently, we do not support non-local files
        if not filename:
            raise OSError("not a local file")
        with open(filename, 'rb') as f:
            data = f.read()
        text = util.decode(data, encoding)
        return util.universal_newlines(text)

    @classmethod
    def new_from_url(cls, url, encoding=None):
        """Create and return a new document, loaded from url.

        This is intended to open a new Document without instantiating one
        if loading the contents fails.

        """
        # Do this first, raises IOError if not found, without creating the document.
        if not url.isEmpty():
            data = cls.load_data(url, encoding)
        # If this did not raise, proceed to create a new document.
        d = cls(url, encoding)
        if not url.isEmpty():
            d.setPlainText(data)
            d.setModified(False)
        return d

    def __init__(self, url=None, encoding=None):
        """Create a new Document with url and encoding.

        Does not load the contents, you should use load() for that, or
        use the new_from_url() constructor to instantiate a new Document
        with the contents loaded.

        """
        if url is None:
            url = QUrl()
        super().__init__()
        self.setDocumentLayout(QPlainTextDocumentLayout(self))
        self._encoding = encoding
        self._url = url # avoid urlChanged on init
        self.setUrl(url)

    def load(self, url=None, encoding=None, keepUndo=False):
        """Load the specified or current url (if None was specified).

        Currently only local files are supported. An IOError is raised
        when trying to load a nonlocal URL.

        If loading succeeds and an url was specified, the url is made the
        current url (by calling setUrl() internally).

        If keepUndo is True, the loading can be undone (with Ctrl-Z).

        """
        if url is None:
            url = QUrl()
        u = url if not url.isEmpty() else self.url()
        text = self.load_data(u, encoding or self._encoding)
        if keepUndo:
            c = QTextCursor(self)
            c.select(QTextCursor.Document)
            c.insertText(text)
        else:
            self.setPlainText(text)
        self.setModified(False)
        if not url.isEmpty():
            self.setUrl(url)

    def _save(self, url, filename):
        with open(filename, "wb") as f:
            f.write(self.encodedText())
            f.flush()
            os.fsync(f.fileno())
        self.setModified(False)
        if not url.isEmpty():
            self.setUrl(url)

    def save(self, url=None, encoding=None):
        """Saves the document to the specified or current url.

        Currently only local files are supported. An IOError is raised
        when trying to save a nonlocal URL.

        If saving succeeds and an url was specified, the url is made the
        current url (by calling setUrl() internally).

        This method is never called directly but only from the overriding
        subclass methods that make further specific use of the modified results.

        """
        if url is None:
            url = QUrl()
        u = url if not url.isEmpty() else self.url()
        filename = u.toLocalFile()
        # currently, we do not support non-local files
        if not filename:
            raise OSError("not a local file")
        # keep the url if specified when we didn't have one, even if saving
        # would fail
        if self.url().isEmpty() and not url.isEmpty():
            self.setUrl(url)
        return url, filename

    def url(self):
        return self._url

    def setUrl(self, url):
        """ Change the url for this document. """
        if url is None:
            url = QUrl()
        old, self._url = self._url, url
        # number for nameless documents
        if self._url.isEmpty():
            nums = [0]
            nums.extend(doc._num for doc in app.documents if doc is not self)
            self._num = max(nums) + 1
        else:
            self._num = 0
        return old

    def encoding(self):
        return variables.get(self, "coding") or self._encoding

    def setEncoding(self, encoding):
        self._encoding = encoding

    def encodedText(self):
        """Return the text of the document as a bytes string encoded in the
        correct encoding.

        The line separator is '\\n' on Unix, '\\r\\n' on Windows.

        Useful to save to a file.

        """
        text = util.platform_newlines(self.toPlainText())
        return util.encode(text, self.encoding())

    def documentName(self):
        """Return a suitable name for this document.

        This is only to be used for display. If the url of the document is
        empty, something like "Untitled" or "Untitled (3)" is returned.

        """
        if self._url.isEmpty():
            if self._num == 1:
                return _("Untitled")
            else:
                return _("Untitled ({num})").format(num=self._num)
        else:
            return os.path.basename(self._url.path())


class Document(AbstractDocument):
    """A Frescobaldi document to be used anywhere except the main editor
    viewspace (also non-GUI jobs/operations)."""

    def save(self, url=None, encoding=None):
        url, filename = super().save(url, encoding)
        self._save(url, filename)


class EditorDocument(AbstractDocument):
    """A Frescobaldi document for use in the main editor view.
    Basically this is an AbstractDocument with signals added."""

    urlChanged = signals.Signal() # new url, old url
    closed = signals.Signal()
    loaded = signals.Signal()
    saving = signals.SignalContext()
    saved = signals.Signal()

    @classmethod
    def new_from_url(cls, url, encoding=None):
        d = super().new_from_url(url, encoding)
        if not url.isEmpty():
            d.loaded()
            app.documentLoaded(d)
        return d

    def __init__(self, url=None, encoding=None):
        super().__init__(url, encoding)
        self.modificationChanged.connect(self.slotModificationChanged)
        app.documents.append(self)
        app.documentCreated(self)

    def slotModificationChanged(self):
        app.documentModificationChanged(self)

    def close(self):
        self.closed()
        app.documentClosed(self)
        app.documents.remove(self)

    def load(self, url=None, encoding=None, keepUndo=False):
        super().load(url, encoding, keepUndo)
        self.loaded()
        app.documentLoaded(self)

    def save(self, url=None, encoding=None):
        url, filename = super().save(url, encoding)
        with self.saving(), app.documentSaving(self):
            self._save(url, filename)
        self.saved()
        app.documentSaved(self)

    def setUrl(self, url):
        old = super().setUrl(url)
        if url != old:
            self.urlChanged(url, old)
            app.documentUrlChanged(self, url, old)

    def cursorAtPosition(self, line, column=None):
        """Return a new QTextCursor set to the line and column given (each starting at 1).

        This method avoids common pitfalls associated with arbitrarily setting the cursor
        position via setCursorPosition.
        - The cursor will be set at a vaid position in a valid block.
        - Reasonable defaults are used for under/over-limit input.
        - Character counting based on UTF-8 matches LilyPond and Python conventions.
        - The cursor will not be set in the middle of a surrogate pair or composed glyph.

        """
        if line < 1:
            line = column = 1
        elif not column or column < 1:
            column = 1
        cursor = QTextCursor(self)
        block = self.findBlockByNumber(line - 1)
        if block.isValid():
            line_text = block.text()
            if len(line_text) >= column:
                qchar_offset = len(line_text[:column - 1].encode('utf_16_le')) // 2
                cursor.setPosition(block.position() + qchar_offset)
                # Escape to in front of what might be the middle of a composed glyph.
                cursor.movePosition(QTextCursor.NextCharacter)
                cursor.movePosition(QTextCursor.PreviousCharacter)
            else:
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.EndOfBlock)
        else:
            cursor.movePosition(QTextCursor.End)
        return cursor
