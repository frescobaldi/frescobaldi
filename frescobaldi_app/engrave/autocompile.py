# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Continuous Auto-compile the sticky or master document.

This is a (mainwindow) global action that can be enabled.

It runs LilyPond in preview mode, always using a temporary file.
When a document is modified after the last run, LilyPond is run again after
a certain time, if the document looks complete
(documentinfo.docinfo(doc).complete()).

The log is not displayed.

"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings, QTimer

import app
import documentinfo
import resultfiles
import jobattributes
import jobmanager
import plugin
import ly.lex

from . import engraver
from . import command


class AutoCompiler(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        self._enabled = False
        self._timer = QTimer(singleShot=True)
        self._timer.timeout.connect(self.slotTimeout)
    
    def setEnabled(self, enabled):
        """Switch the autocompiler on or off."""
        enabled = bool(enabled)
        if enabled == self._enabled:
            return
        self._enabled = enabled

        doc = self.mainwindow().currentDocument()
        if enabled:
            self.mainwindow().currentDocumentChanged.connect(self.slotDocumentChanged)
            app.documentSaved.connect(self.startTimer)
            if doc:
                self.slotDocumentChanged(doc, None)
        else:
            self.mainwindow().currentDocumentChanged.disconnect(self.slotDocumentChanged)
            app.documentSaved.disconnect(self.startTimer)
            if doc:
                self.slotDocumentChanged(None, doc)
    
    def slotDocumentChanged(self, new=None, old=None):
        """Called when the mainwindow changes the current document."""
        if old:
            old.contentsChanged.disconnect(self.startTimer)
            old.loaded.disconnect(self.startTimer)
        if new:
            new.contentsChanged.connect(self.startTimer)
            new.loaded.connect(self.startTimer)
            if self._enabled:
                self.startTimer()
    
    def startTimer(self):
        """Called to trigger a soon auto-compile try."""
        self._timer.start(750)
    
    def slotTimeout(self):
        """Called when the autocompile timer expires."""
        eng = engraver(self.mainwindow())
        doc = eng.document()
        rjob = jobmanager.job(doc)
        if rjob and rjob.isRunning() and not jobattributes.get(rjob).hidden:
            # a real job is running, come back when that is done
            rjob.done.connect(self.startTimer)
            return
        
        mgr = AutoCompileManager.instance(doc)
        may_compile = mgr.may_compile()
        if not may_compile:
            cur = self.mainwindow().currentDocument()
            if doc is not cur and not cur.isModified() and not cur.url().isEmpty():
                mgr = AutoCompileManager.instance(cur)
                may_compile = mgr.may_compile()
                if may_compile:
                    mgr.slotJobStarted()
        if may_compile:
            job = command.defaultJob(doc, ['-dpoint-and-click'])
            jobattributes.get(job).hidden = True
            eng.runJob(job, doc)


class AutoCompileManager(plugin.DocumentPlugin):
    def __init__(self, document):
        document.contentsChanged.connect(self.slotDocumentContentsChanged)
        document.saved.connect(self.slotDocumentSaved)
        if document.isModified():
            self._dirty = True
        else:
            # look for existing result files in the default output format
            s = QSettings()
            s.beginGroup("lilypond_settings")
            if s.value("default_output_target", "pdf", type("")) == "svg":
                ext = '.svg*'
            else:
                ext = '.pdf'
            self._dirty = not resultfiles.results(document).files(ext)
        self._hash = None if self._dirty else self.token_hash()
        jobmanager.manager(document).started.connect(self.slotJobStarted)
    
    def token_hash(self):
        """Return a hash for all non-whitespace tokens.
        
        Used to determine non-whitespace changes.
        
        """
        dinfo = documentinfo.docinfo(self.document())
        return hash(tuple(t for t in dinfo.tokens
                  if not isinstance(t, (ly.lex.Space, ly.lex.Comment))))
    
    def may_compile(self):
        """Return True if we could need to compile the document."""
        if self._dirty:
            dinfo = documentinfo.docinfo(self.document())
            if (dinfo.mode() == "lilypond"
                and dinfo.complete()
                and documentinfo.music(self.document()).has_output()):
                h = self.token_hash()
                if h != self._hash:
                    self._hash = h
                    if h != hash(tuple()):
                        return True
            self._dirty = False
    
    def slotDocumentContentsChanged(self):
        """Called when the user modifies the document."""
        self._dirty = True

    def slotDocumentSaved(self):
        """Called when the document is saved. Forces auto-compile once."""
        self._dirty = True
        self._hash = None
    
    def slotJobStarted(self):
        """Called when an engraving job is started on this document."""
        if self._dirty:
            self._dirty = False
            self._hash = self.token_hash()


