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
import jobmanager
import jobattributes
import scratchdir
import util


# finds file references (filename:line:col:) in messages
message_re = re.compile(br"^((.*?):(\d+)(?::(\d+))?)(?=:)", re.M)


def errors(document):
    return Errors.instance(document)


class Errors(plugin.DocumentPlugin):
    """Maintains the list of references (errors/warnings) to documents after a Job run."""

    def __init__(self, document):
        self._refs = {}
        mgr = jobmanager.manager(document)
        if mgr.job():
            self.connectJob(mgr.job())
        mgr.started.connect(self.connectJob)

    def connectJob(self, job):
        """Starts collecting the references of a started Job.

        Output already created by the Job is read and we start
        listening for new output.

        """
        # do not collect errors for auto-engrave jobs if the user has disabled it
        if jobattributes.get(job).hidden and QSettings().value("log/hide_auto_engrave", False, bool):
            return
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
        for msg, type in job.history():
            self.slotJobOutput(msg, type)
        job.output.connect(self.slotJobOutput)

    def slotJobOutput(self, message, type):
        """Called whenever the job has output.

        The output is checked for error messages that contain
        a filename:line:column expression.

        """
        if type == job.STDERR:
            enc = sys.getfilesystemencoding()
            for m in message_re.finditer(message.encode('latin1')):
                url = m.group(1).decode(enc)
                filename = m.group(2).decode(enc)
                filename = util.normpath(filename)
                line, column = int(m.group(3)), int(m.group(4) or 0)
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

        lines start numbering with 1, columns with 0 (LilyPond convention).

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
        b = document.findBlockByNumber(max(0, self._line - 1))
        if b.isValid():
            self._cursor = c = QTextCursor(document)
            c.setPosition(b.position() + self._column)
            document.closed.connect(self.unbind)
            if self._line > 0:
                bookmarks.bookmarks(document).setMark(self._line - 1, "error")
        else:
            self._cursor = None

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


