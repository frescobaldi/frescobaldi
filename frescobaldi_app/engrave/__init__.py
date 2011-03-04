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
Actions to engrave the music in the documents.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction, QKeySequence

import app
import actioncollection
import actioncollectionmanager
import jobmanager
import plugin
import icons


def engraver(mainwindow):
    return Engraver.instance(mainwindow)
    

class Engraver(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.engrave_runner.triggered.connect(self.engraveRunner)
        ac.engrave_preview.triggered.connect(self.engravePreview)
        ac.engrave_publish.triggered.connect(self.engravePublish)
        ac.engrave_custom.triggered.connect(self.engraveCustom)
        ac.engrave_abort.triggered.connect(self.engraveAbort)
        mainwindow.currentDocumentChanged.connect(self.documentChanged)
        
    def documentChanged(self, new, old):
        if old:
            jobmanager.manager(old).stateChanged.disconnect(self.updateActions)
        jobmanager.manager(new).stateChanged.connect(self.updateActions)
        self.updateActions()
    
    def runningJob(self):
        """Returns a Job for the current document if that is running."""
        job = jobmanager.job(self.mainwindow().currentDocument())
        if job and job.isRunning():
            return job
    
    def updateActions(self):
        running = bool(self.runningJob())
        ac = self.actionCollection
        ac.engrave_preview.setEnabled(not running)
        ac.engrave_publish.setEnabled(not running)
        ac.engrave_custom.setEnabled(not running)
        ac.engrave_abort.setEnabled(running)
        ac.engrave_runner.setIcon(icons.get('process-stop' if running else 'lilypond-run'))
    
    def engraveRunner(self):
        job = self.runningJob()
        if job:
            job.abort()
        else:
            self.engravePreview()
    
    def engravePreview(self):
        pass
    
    def engravePublish(self):
        pass
    
    def engraveCustom(self):
        pass
    
    def engraveAbort(self):
        job = self.runningJob()
        if job:
            job.abort()



class Actions(actioncollection.ActionCollection):
    name = "engrave"
    
    def createActions(self, parent=None):
        self.engrave_runner = QAction(parent)
        self.engrave_preview = QAction(parent)
        self.engrave_publish = QAction(parent)
        self.engrave_custom = QAction(parent)
        self.engrave_abort = QAction(parent)
        
        self.engrave_preview.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_M))

        self.engrave_preview.setIcon(icons.get('lilypond-run'))
        self.engrave_publish.setIcon(icons.get('lilypond-run'))
        self.engrave_custom.setIcon(icons.get('lilypond-run'))
        self.engrave_abort.setIcon(icons.get('process-stop'))
        

    def translateUI(self):
        self.engrave_runner.setText(_("Engrave"))
        self.engrave_preview.setText(_("&Engrave (preview)"))
        self.engrave_publish.setText(_("Engrave (&publish)"))
        self.engrave_custom.setText(_("Engrave (&custom)"))
        self.engrave_abort.setText(_("Abort Engraving &Job"))
        
        
