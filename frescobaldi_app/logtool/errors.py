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
Manages cursor positions of file-references in error messages.
"""


import os
import re
import sys

from PyQt5.QtCore import QSettings, QUrl
from PyQt5.QtGui import QTextCursor

import app
import bookmarks
import plugin
import job
import scratchdir
import util


# finds file references (filename:line:col:) in messages
message_re = re.compile(br"^((.*?):([1-9]\d*)(?::([1-9]\d*))?)(?=:)", re.M)


def errors(document):
    return Errors.instance(document)


class Errors(plugin.DocumentPlugin):
    """Maintains the list of references (errors/warnings) to documents after a Job run."""

    def __init__(self, document):
        self._refs = {}
        self._job = None
        mgr = job.manager.manager(document)
        if mgr.job():
            self.connectJob(mgr.job())
        mgr.started.connect(self.connectJob)

    def connectJob(self, j):
        """Starts collecting the references of a started Job.

        Output already created by the Job is read and we start
        listening for new output.

        """
        # do not collect errors for auto-engrave jobs if the user has disabled it
        if job.attributes.get(j).hidden and QSettings().value("log/hide_auto_engrave", False, bool):
            return
        self._job = j
        # clear earlier set error marks
        docs = {self.document()}
        for ref in self._refs.values():
            c = ref.cursor(False)
            if c:
                docs.add(c.document())
        for doc in docs:
            bookmarks.bookmarks(doc).clear("error")
        self._refs.clear()
        # take over history and connect
        for msg, type in j.history():
            self.slotJobOutput(msg, type)
        j.output.connect(self.slotJobOutput)

    def slotJobOutput(self, message, type):
        """Called whenever the job has output.

        The output is checked for error messages that contain
        a filename:line:column expression.

        """
        if type == job.STDERR:
            enc = sys.getfilesystemencoding()
            job_enc = self._job._encoding
            for m in message_re.finditer(message.encode(job_enc)):
                url = m.group(1).decode(enc)
                filename = m.group(2).decode(enc)
                filename = util.normpath(filename)
                line, column = int(m.group(3)), int(m.group(4) or 1)
                self._refs[url] = Reference(filename, line, column)

    def cursor(self, url, load=False):
        """Returns a QTextCursor belonging to the url (string).

        If load (defaulting to False) is True, the document is loaded
        if it wasn't already loaded.
        Returns None if the url was not valid or the document could not be loaded.

        """
        return self._refs[url].cursor(load)


class Reference(object):
    """Represents a reference to a line/column pair (a cursor position) in a Document."""
    def __init__(self, filename, line, column):
        """Creates the reference to filename, line and column.

        By LilyPond convention, lines and columns are numbered starting with 1.

        If a document with the given filename is already loaded (or the filename
        refers to the scratchdir for a document) a QTextCursor is created immediately.

        Otherwise, when a Document is loaded later with our filename, a QTextCursor
        is created then (by the bind() method).

        """
        self._filename = filename
        self._line = line
        self._column = column
        self._cursor = None

        app.documentLoaded.connect(self.trybind)
        d = scratchdir.findDocument(filename)
        if d:
            self.bind(d)

    def bind(self, document):
        """Called when a document is loaded this Reference points to.

        Creates a QTextCursor so the position is maintained even if the document
        changes.

        """
        # message_re and Errors.slotJobOutput ensure that _line and _column are >= 1.
        # _line or _column overrun defaults to end of document or line respectively.
        self._cursor = c = QTextCursor(document)
        document.closed.connect(self.unbind)
        b = document.findBlockByNumber(self._line - 1)
        if b.isValid():
            bookmarks.bookmarks(document).setMark(self._line - 1, "error")
            line_text = b.text()
            if len(line_text) >= self._column:
                qchar_offset = len(line_text[:self._column - 1].encode('utf_16_le')) // 2
                c.setPosition(b.position() + qchar_offset)
                # escape to in front of what might be the middle of a composed glyph
                c.movePosition(QTextCursor.NextCharacter)
                c.movePosition(QTextCursor.PreviousCharacter)
            else:
                c.setPosition(b.position())
                c.movePosition(QTextCursor.EndOfBlock)
        else:
            c.movePosition(QTextCursor.End)

    def unbind(self):
        """Called when previously "bound" document is closed."""
        self._cursor = None

    def trybind(self, document):
        """Called whenever a new Document is loaded, checks the filename."""
        if document.url().toLocalFile() == self._filename:
            self.bind(document)

    def cursor(self, load):
        """Returns a QTextCursor for this reference.

        load should be True or False and determines if a not-loaded document should be loaded.
        Returns None if the document could not be loaded.

        """
        if self._cursor:
            return self._cursor
        if load:
            win = app.activeWindow()
            if win:
                try:
                    win.openUrl(QUrl.fromLocalFile(self._filename)) # also calls bind
                except IOError:
                    pass
                if self._cursor:
                    return self._cursor
