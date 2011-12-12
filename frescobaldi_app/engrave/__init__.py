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
Actions to engrave the music in the documents.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import QAction, QApplication, QKeySequence

import app
import actioncollection
import actioncollectionmanager
import jobmanager
import jobattributes
import plugin
import icons
import signals

def engraver(mainwindow):
    return Engraver.instance(mainwindow)
    

class Engraver(plugin.MainWindowPlugin):
    
    stickyChanged = signals.Signal()
    
    def __init__(self, mainwindow):
        self._currentStickyDocument = None
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.engrave_sticky.triggered.connect(self.stickyToggled)
        ac.engrave_runner.triggered.connect(self.engraveRunner)
        ac.engrave_preview.triggered.connect(self.engravePreview)
        ac.engrave_publish.triggered.connect(self.engravePublish)
        ac.engrave_custom.triggered.connect(self.engraveCustom)
        ac.engrave_abort.triggered.connect(self.engraveAbort)
        mainwindow.currentDocumentChanged.connect(self.updateActions)
        app.jobStarted.connect(self.updateActions)
        app.jobFinished.connect(self.updateActions)
        app.languageChanged.connect(self.updateStickyActionText)
        self.updateStickyActionText()
        
    def runningJob(self):
        """Returns a Job for the sticky or current document if that is running."""
        doc = self.stickyDocument() or self.mainwindow().currentDocument()
        job = jobmanager.job(doc)
        if job and job.isRunning():
            return job
    
    def updateActions(self):
        running = bool(self.runningJob())
        ac = self.actionCollection
        ac.engrave_preview.setEnabled(not running)
        ac.engrave_publish.setEnabled(not running)
        ac.engrave_abort.setEnabled(running)
        ac.engrave_runner.setIcon(icons.get('process-stop' if running else 'lilypond-run'))
    
    def engraveRunner(self):
        job = self.runningJob()
        if job:
            job.abort()
        elif QApplication.keyboardModifiers() & Qt.SHIFT:
            self.engraveCustom()
        else:
            self.engravePreview()
    
    def engravePreview(self):
        """Starts an engrave job in preview mode (with point and click turned on)."""
        self.engrave(True)
    
    def engravePublish(self):
        """Starts an engrave job in publish mode (with point and click turned off)."""
        self.engrave(False)
        
    def engraveCustom(self):
        """Opens a dialog to configure the job before starting it."""
        try:
            dlg = self._customDialog
        except AttributeError:
            from . import custom
            dlg = self._customDialog = custom.Dialog(self.mainwindow())
            dlg.setWindowModality(Qt.WindowModal)
        doc = self.stickyDocument() or self.mainwindow().currentDocument()
        dlg.setDocument(doc)
        if dlg.exec_():
            self.runJob(dlg.getJob(doc), doc)
    
    def engrave(self, preview, document=None):
        """Starts a default engraving job.
        
        The bool preview specifies preview mode.
        If document is not specified, it is either the sticky or current
        document.
        
        """
        from . import command
        doc = document or self.stickyDocument() or self.mainwindow().currentDocument()
        self.runJob(command.defaultJob(doc, preview), doc)
    
    def engraveAbort(self):
        job = self.runningJob()
        if job:
            job.abort()
    
    def runJob(self, job, document):
        """Runs the engraving job on behalf of document."""
        # save the current document if desired and it makes sense 
        # (i.e. the document is modified and has a local filename)
        if QSettings().value("lilypond_settings/save_on_run", False) in (True, "true"):
            doc = self.mainwindow().currentDocument()
            if doc.isModified() and doc.url().toLocalFile():
                doc.save()
        jobattributes.get(job).mainwindow = self.mainwindow()
        jobmanager.manager(document).startJob(job)
    
    def stickyToggled(self):
        """Called when the user toggles the 'Sticky' action."""
        self.setStickyDocument(None if self.stickyDocument() else self.mainwindow().currentDocument())
    
    def setStickyDocument(self, doc=None):
        """Sticks to the given document or removes the 'stick' when None."""
        cur = self._currentStickyDocument
        self._currentStickyDocument = doc
        if cur:
            cur.closed.disconnect(self.slotUnStickDocument)
            cur.loaded.disconnect(self.slotUnStickDocument)
            cur.urlChanged.disconnect(self.updateStickyActionText)
            self.stickyChanged(cur)
        if doc:
            doc.closed.connect(self.slotUnStickDocument)
            doc.loaded.connect(self.slotUnStickDocument)
            doc.urlChanged.connect(self.updateStickyActionText)
            self.stickyChanged(doc)
        self.actionCollection.engrave_sticky.setChecked(bool(doc))
        self.updateStickyActionText()
        self.updateActions()
        
    def stickyDocument(self):
        """Returns the document currently marked as 'Sticky', if any."""
        return self._currentStickyDocument
    
    def slotUnStickDocument(self):
        """Called when the document that is currently sticky closes or reloads."""
        self.setStickyDocument(None)

    def updateStickyActionText(self):
        """Called when the sticky action toggles or when the language is changed."""
        doc = self.stickyDocument()
        if doc:
            text = _("&Always Engrave [{docname}]").format(docname = doc.documentName())
        else:
            text = _("&Always Engrave This Document")
        self.actionCollection.engrave_sticky.setText(text)
        

class Actions(actioncollection.ActionCollection):
    name = "engrave"
    
    def createActions(self, parent=None):
        self.engrave_sticky = QAction(parent)
        self.engrave_sticky.setCheckable(True)
        self.engrave_runner = QAction(parent)
        self.engrave_preview = QAction(parent)
        self.engrave_publish = QAction(parent)
        self.engrave_custom = QAction(parent)
        self.engrave_abort = QAction(parent)
        
        self.engrave_preview.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_M))
        self.engrave_publish.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_P))
        self.engrave_custom.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_M))
        self.engrave_abort.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Pause))
        
        self.engrave_sticky.setIcon(icons.get('pushpin'))
        self.engrave_preview.setIcon(icons.get('lilypond-run'))
        self.engrave_publish.setIcon(icons.get('lilypond-run'))
        self.engrave_custom.setIcon(icons.get('lilypond-run'))
        self.engrave_abort.setIcon(icons.get('process-stop'))
        

    def translateUI(self):
        self.engrave_runner.setText(_("Engrave"))
        self.engrave_preview.setText(_("&Engrave (preview)"))
        self.engrave_publish.setText(_("Engrave (&publish)"))
        self.engrave_custom.setText(_("Engrave (&custom)..."))
        self.engrave_abort.setText(_("Abort Engraving &Job"))
        
        
