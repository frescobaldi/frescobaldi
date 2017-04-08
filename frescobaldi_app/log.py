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
A Log shows the output of a Job.
"""


import contextlib

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import (QFont, QPalette, QTextCharFormat, QTextCursor,
                         QTextFormat)
from PyQt5.QtWidgets import QApplication, QTextBrowser

import job
import qutil


class Log(QTextBrowser):
    """Widget displaying output from a Job."""
    def __init__(self, parent=None):
        super(Log, self).__init__(parent)
        self.setOpenLinks(False)
        self.cursor = QTextCursor(self.document())
        self._types = job.ALL
        self._lasttype = None
        self._formats = self.logformats()

    def setMessageTypes(self, types):
        """Set the types of Job output to display.

        types is a constant bitmask from job, like job.STDOUT etc.
        By default job.ALL is used.

        """
        self._types = types

    def messageTypes(self):
        """Return the set message types (job.ALL by default)."""
        return self._types

    def connectJob(self, job):
        """Gives us the output from the Job (past and upcoming)."""
        for msg, type in job.history():
            self.write(msg, type)
        job.output.connect(self.write)

    def textFormat(self, type):
        """Returns a QTextFormat() for the given type."""
        return self._formats[type]

    def write(self, message, type):
        """Writes the given message with the given type to the log.

        The keepScrolledDown context manager is used to scroll the log further
        down if it was scrolled down at that moment.

        If two messages of a different type are written after each other a newline
        is inserted if otherwise the message would continue on the same line.

        """
        if type & self._types:
            with self.keepScrolledDown():
                changed = type != self._lasttype
                self._lasttype = type
                if changed and self.cursor.block().text() and not message.startswith('\n'):
                    self.cursor.insertText('\n')
                self.writeMessage(message, type)

    def writeMessage(self, message, type):
        """Inserts the given message in the text with the textformat belonging to type."""
        self.cursor.insertText(message, self.textFormat(type))

    @contextlib.contextmanager
    def keepScrolledDown(self):
        """Performs a function, ensuring the log stays scrolled down if it was scrolled down on start."""
        vbar = self.verticalScrollBar()
        scrolleddown = vbar.value() == vbar.maximum()
        try:
            yield
        finally:
            if scrolleddown:
                vbar.setValue(vbar.maximum())

    def logformats(self):
        """Returns a dictionary with QTextCharFormats for the different types of messages.

        Besides the STDOUT, STDERR, NEUTRAL, FAILURE and SUCCESS formats there is also
        a "link" format, that looks basically the same as the output formats, but blueish
        and underlined, to make parts of the output (e.g. filenames) look clickable.

        """
        textColor = QApplication.palette().color(QPalette.WindowText)
        successColor = qutil.addcolor(textColor, 0, 128, 0) # more green
        failureColor = qutil.addcolor(textColor, 128, 0, 0) # more red
        linkColor    = qutil.addcolor(textColor, 0, 0, 128) # more blue
        stdoutColor  = qutil.addcolor(textColor, 64, 64, 0) # more purple

        s = QSettings()
        s.beginGroup("log")
        outputFont = QFont(s.value("fontfamily", "monospace", str))
        outputFont.setPointSizeF(s.value("fontsize", 9.0, float))

        output = QTextCharFormat()
        output.setFont(outputFont)
        # enable zooming the log font size
        output.setProperty(QTextFormat.FontSizeAdjustment, 0)

        stdout = QTextCharFormat(output)
        stdout.setForeground(stdoutColor)

        stderr = QTextCharFormat(output)
        link   = QTextCharFormat(output)
        link.setForeground(linkColor)
        link.setFontUnderline(True)

        status = QTextCharFormat()
        status.setFontWeight(QFont.Bold)

        neutral = QTextCharFormat(status)

        success = QTextCharFormat(status)
        success.setForeground(successColor)

        failure = QTextCharFormat(status)
        failure.setForeground(failureColor)

        return {
            job.STDOUT: stdout,
            job.STDERR: stderr,
            job.NEUTRAL: neutral,
            job.SUCCESS: success,
            job.FAILURE: failure,
            'link': link,
        }



