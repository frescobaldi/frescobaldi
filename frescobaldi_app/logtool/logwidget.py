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
The LogWidget.
"""


import itertools
import os
import re
import sys
import weakref

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import (
    QColor, QTextCharFormat, QTextCursor, QTextFormat)
from PyQt5.QtWidgets import QTextEdit

import app
import log
import job
import jobmanager
import jobattributes
import qutil

from . import errors


class LogWidget(log.Log):
    """A Log widget that tracks document changes in the MainWindow."""
    def __init__(self, logtool):
        super(LogWidget, self).__init__(logtool)
        self._rawView = True
        self._document = lambda: None
        self._errors = []
        self._currentErrorIndex = -1
        self.readSettings()
        self.anchorClicked.connect(self.slotAnchorClicked)
        logtool.mainwindow().currentDocumentChanged.connect(self.switchDocument)
        app.documentClosed.connect(self.documentClosed)
        app.settingsChanged.connect(self.readSettings)
        doc = logtool.mainwindow().currentDocument()
        if doc:
            self.switchDocument(doc)

    def readSettings(self):
        self._formats = self.logformats()
        self._rawView = QSettings().value("log/rawview", True, bool)
        if self._document():
            self.switchDocument(self._document()) # reload

    def switchDocument(self, doc):
        """Called when the document is changed."""
        job = jobmanager.job(doc)
        if job:
            # do not show the messages for auto-engrave jobs if the user has disabled it
            if jobattributes.get(job).hidden and QSettings().value("log/hide_auto_engrave", False, bool):
                return
            prevDoc = self._document()
            if prevDoc and prevDoc != doc:
                prevJob = jobmanager.job(prevDoc)
                if prevJob:
                    prevJob.output.disconnect(self.write)
            self._document = weakref.ref(doc)
            self.clear()
            self.connectJob(job)

    def documentClosed(self, doc):
        if doc == self._document():
            self.clear()

    def clear(self):
        self._errors = []
        self._currentErrorIndex = -1
        self.setExtraSelections([])
        super(LogWidget, self).clear()

    def writeMessage(self, message, type):
        """This writes both status and output messages to the log.

        For output messages also the correct encoding is re-applied:
        LilyPond writes filenames out in the system's filesystemencoding,
        while the messages are always written in UTF-8 encoding...

        """
        if type == job.STDERR:
            # find filenames in message:
            parts = iter(errors.message_re.split(message.encode('latin1')))
            msg = next(parts).decode('utf-8', 'replace')
            self.cursor.insertText(msg, self.textFormat(type))
            enc = sys.getfilesystemencoding()

            for url, path, line, col, msg in zip(*itertools.repeat(parts, 5)):
                url = url.decode(enc)
                path = path.decode(enc)
                msg = msg.decode('utf-8', 'replace')
                if self._rawView:
                    fmt = QTextCharFormat(self.textFormat(type))
                    display_url = url
                else:
                    fmt = QTextCharFormat(self.textFormat("link"))
                    display_url = os.path.basename(path)
                fmt.setAnchor(True)
                fmt.setAnchorHref(str(len(self._errors)))
                fmt.setToolTip(_("Click to edit this file"))

                pos = self.cursor.position()
                self.cursor.insertText(display_url, fmt)
                self.cursor.insertText(msg, self.textFormat(type))
                self._errors.append((pos, self.cursor.position(), url))
        else:
            if type == job.STDOUT:
                # we use backslashreplace because LilyPond sometimes seems to write
                # incorrect utf-8 to standard output in \displayMusic, \displayScheme
                # functions etc.
                message = message.encode('latin1').decode('utf-8', 'backslashreplace')
            super(LogWidget, self).writeMessage(message, type)

    def slotAnchorClicked(self, url):
        """Called when the user clicks a filename in the log."""
        index = int(url.toString())
        if 0 <= index < len(self._errors):
            self.highlightError(index)

    def gotoError(self, direction):
        """Jumps to the next (1) or previous (-1) error message."""
        if self._errors:
            i = self._currentErrorIndex + direction
            if i < 0:
                i = len(self._errors) - 1
            elif i >= len(self._errors):
                i = 0
            self.highlightError(i)

    def highlightError(self, index):
        """Hihglights the error message at the given index and jumps to its location."""
        self._currentErrorIndex = index
        # set text format
        pos, anchor, url = self._errors[index]
        es = QTextEdit.ExtraSelection()
        es.cursor = QTextCursor(self.document())
        es.cursor.setPosition(pos)
        es.cursor.setPosition(anchor, QTextCursor.KeepAnchor)
        bg = qutil.mixcolor(self.palette().highlight().color(), self.palette().base().color(), 0.4)
        es.format.setBackground(bg)
        es.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setExtraSelections([es])
        # scroll log to the message
        cursor = QTextCursor(self.document())
        cursor.setPosition(anchor)
        self.setTextCursor(cursor)
        cursor.setPosition(pos)
        self.setTextCursor(cursor)
        # jump to the error location
        cursor = errors.errors(self._document()).cursor(url, True)
        if cursor:
            self.parentWidget().mainwindow().setTextCursor(cursor, findOpenView=True)


