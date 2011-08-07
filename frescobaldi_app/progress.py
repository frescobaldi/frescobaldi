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

"""
Manages the progress bar in the status bar of ViewSpaces.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt, QTimeLine, QTimer
from PyQt4.QtGui import QProgressBar

import app
import plugin
import jobmanager
import metainfo


metainfo.define('buildtime', 0.0, float)


class ProgressBar(plugin.ViewSpacePlugin):
    """A Simple progress bar to show a Job is running."""
    def __init__(self, viewSpace):
        bar = self._bar = QProgressBar(minimum=0, maximum=100)
        bar.setMaximumHeight(14)
        bar.setMinimum(0)
        viewSpace.status.layout().addWidget(bar, 1)
        bar.hide()
        self._timeline = QTimeLine(updateInterval=125, frameChanged=bar.setValue)
        self._timeline.setFrameRange(0, 100)
        self._hideTimer = QTimer(timeout=bar.hide, singleShot=True)
        viewSpace.viewChanged.connect(self.viewChanged)
        app.jobStarted.connect(self.jobStarted)
        app.jobFinished.connect(self.jobFinished)
        
    def viewChanged(self, view):
        self.showProgress(view.document())
        
    def showProgress(self, document):
        self._hideTimer.stop()
        job = jobmanager.job(document)
        if job and job.isRunning():
            buildtime = metainfo.info(document).buildtime
            if not buildtime:
                buildtime = 3.0 + document.blockCount() / 20 # very arbitrary estimate...
            self._timeline.setDuration(buildtime*1000)
            self._timeline.setCurrentTime(job.elapsed()*1000)
            self._timeline.start()
            self._bar.show()
        else:
            self._timeline.stop()
            self._bar.hide()
            
    def jobStarted(self, document):
        if document == self.viewSpace().document():
            self.showProgress(document)
            
    def jobFinished(self, document, job, success):
        if document == self.viewSpace().document():
            self._timeline.stop()
            if success:
                metainfo.info(document).buildtime = job.elapsed()
                self._bar.setValue(100)
                self._hideTimer.start(3000)
            else:
                self._bar.hide()


app.viewSpaceCreated.connect(ProgressBar.instance)
