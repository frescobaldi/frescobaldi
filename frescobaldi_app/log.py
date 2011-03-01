# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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
A Log shows the output of a Job.
"""

import contextlib

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import job



class Log(QTextBrowser):
    """Widget displaying output from a Job."""
    def __init__(self, parent=None):
        super(Log, self).__init__(parent)
        self.cursor = QTextCursor(self.document())
        self._lasttype = None
        self._formats = self.logformats()
        
    def connectJob(self, job):
        """Gives us the output from the Job (past and upcoming)."""
        for msg, type in job.history():
            self.write(msg, type)
        job.output.connect(self.write)
        
    def textFormat(self, type):
        """Returns a QTextFormat() for the given type."""
        return self._formats[type]

    def write(self, message, type):
        """Writes the given message with the given type to the log."""
        with self.keepScrolledDown():
            changed = type != self._lasttype
            self._lasttype = type
            if changed and self.cursor.block().text() and not message.startswith('\n'):
                self.cursor.insertText('\n')
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
        """Returns a dictionary with QTextCharFormats for the different types of messages."""
        # TODO: make fonts and colors user-configurable
        output = QTextCharFormat()
        output.setFont(QFont("Monospace", 10))
        
        stdout = QTextCharFormat(output)
        stderr = QTextCharFormat(output)
        
        status = QTextCharFormat()
        status.setFontWeight(QFont.Bold)
        
        neutral = QTextCharFormat(status)
        
        success = QTextCharFormat(status)
        success.setForeground(QColor(Qt.green))
        
        failure = QTextCharFormat(status)
        failure.setForeground(QColor(Qt.red))
        
        return {
            job.STDOUT: stdout,
            job.STDERR: stderr,
            job.NEUTRAL: neutral,
            job.SUCCESS: success,
            job.FAILURE: failure,
        }




