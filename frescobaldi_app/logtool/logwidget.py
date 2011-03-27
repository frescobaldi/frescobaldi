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
The LogWidget.
"""

import itertools
import os
import re
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import log
import job

from . import errors


class LogWidget(log.Log):
    """A Log widget that tracks document changes in the MainWindow."""
    def __init__(self, logtool):
        super(LogWidget, self).__init__(logtool)
        self._rawView = True
        self._document = lambda: None
        self.readSettings()
        self.anchorClicked.connect(self.slotAnchorClicked)
        logtool.mainwindow().currentDocumentChanged.connect(self.switchDocument)
        app.jobStarted.connect(self.jobStarted)
        app.documentClosed.connect(self.documentClosed)
        app.settingsChanged.connect(self.readSettings)
        self.switchDocument(logtool.mainwindow().currentDocument())
    
    def readSettings(self):
        self._formats = self.logformats()
        self._rawView = QSettings().value("log/rawview", True) not in (False, "false")
        if self._document():
            self.switchDocument(self._document()) # reload
    
    def switchDocument(self, doc):
        """Called when the document is changed."""
        import jobmanager
        job = jobmanager.job(doc)
        if job:
            prevDoc = self._document()
            if prevDoc and prevDoc != doc:
                prevJob = jobmanager.job(prevDoc)
                if prevJob:
                    prevJob.output.disconnect(self.write)
            self._document = weakref.ref(doc)
            self.clear()
            self.connectJob(job)
            
    def jobStarted(self, doc, job):
        if doc == self.parentWidget().mainwindow().currentDocument():
            self.switchDocument(doc)

    def documentClosed(self, doc):
        if doc == self._document():
            self.clear()

    def writeMessage(self, message, type):
        if type == job.STDERR:
            # find filenames in message:
            parts = iter(errors.message_re.split(message))
            self.cursor.insertText(next(parts), self.textFormat(type))
            
            for url, path, line, col, msg in zip(*itertools.repeat(parts, 5)):
                
                if self._rawView:
                    fmt = QTextCharFormat(self.textFormat(type))
                    display_url = url
                else:
                    fmt = QTextCharFormat(self.textFormat("link"))
                    display_url = os.path.basename(path)
                fmt.setAnchor(True)
                fmt.setAnchorHref(url)
                fmt.setAnchorNames([url])
                fmt.setToolTip(_("Click to edit this file"))
                self.cursor.insertText(display_url, fmt)
                self.cursor.insertText(msg, self.textFormat(type))
        else:
            super(LogWidget, self).writeMessage(message, type)

    def slotAnchorClicked(self, url):
        """Called when the user clicks a filename in the log."""
        cursor = errors.errors(self._document()).cursor(url.toString(), True)
        if cursor:
            self.parentWidget().mainwindow().setTextCursor(cursor, findOpenView=True)




