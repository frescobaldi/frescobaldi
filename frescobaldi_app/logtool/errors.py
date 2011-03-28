# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Manages cursor positions of file-references in error messages.
"""

import re

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QTextCursor

import app
import bookmarks
import plugin
import job
import jobmanager
import scratchdir


# finds file references (filename:line:col:) in messages
message_re = re.compile(r"^((.*?):(\d+)(?::(\d+))?)(?=:)", re.M)


def errors(document):
    return Errors.instance(document)


class Errors(plugin.DocumentPlugin):
    """Maintains the list of references (errors/warnings) to documents after a Job run."""
    
    def __init__(self, document):
        self._refs = {}
        mgr = jobmanager.manager(document)
        if mgr.job():
            self.connectJob(mgr.job())
        mgr.stateChanged.connect(self.slotJobManagerStateChanged)
        
    def slotJobManagerStateChanged(self, job):
        if job:
            self.connectJob(job)
        
    def connectJob(self, job):
        """Starts collecting the references of a started Job."""
        # clear earlier set error marks
        docs = set([self.document()])
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
        if type == job.STDERR:
            for m in message_re.finditer(message):
                url, filename = m.group(1, 2)
                line, column = int(m.group(3)), int(m.group(4) or "0")
                self._refs[url] = Reference(filename, line, column)
        
    def cursor(self, url, load=False):
        """Returns a QTextCursor belonging to the url (string).
        
        If load (defaulting to False) is True, the document is loaded
        if it wasn't already loaded.
        Returns None if the url was not valid or the document could not be loaded.
        
        """
        return self._refs[url].cursor(load)


class Reference(object):
    def __init__(self, filename, line, column):
        self._filename = filename
        self._line = line
        self._column = column
        self._cursor = None
        
        app.documentLoaded.connect(self.trybind)
        for d in app.documents:
            if (scratchdir.scratchdir(d).path() == filename
                or d.url().toLocalFile() == filename):
                self.bind(d)
                break
    
    def bind(self, document):
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
        self._cursor = None
    
    def trybind(self, document):
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
            app.openUrl(QUrl.fromLocalFile(self._filename)) # also calls bind
            if self._cursor:
                return self._cursor


