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
The LogWidget.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import log


class LogWidget(log.Log):
    """A Log widget that tracks document changes in the MainWindow."""
    def __init__(self, logtool):
        super(LogWidget, self).__init__(logtool)
        logtool.mainwindow().currentDocumentChanged.connect(self.documentChanged)
        app.jobStarted.connect(self.jobStarted)
        self.documentChanged(logtool.mainwindow().currentDocument())
        
    def documentChanged(self, doc, prev=None):
        """Called when the document is changed."""
        import jobmanager
        if prev:
            job = jobmanager.job(prev)
            if job:
                job.output.disconnect(self.widget().write)
        job = jobmanager.job(doc)
        if job:
            self.clear()
            self.connectJob(job)
            
    def jobStarted(self, doc, job):
        if doc == self.parentWidget().mainwindow().currentDocument():
            self.clear()
            self.connectJob(job)


