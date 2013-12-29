# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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

from PyQt4.QtCore import QTimer

import documentinfo
import resultfiles
import jobattributes
import jobmanager
import plugin
import ly.lex

from . import engraver
from . import command


class AutoCompiler(plugin.MainWindowPlugin):
    
    def setEnabled(self, enabled):
        try:
            timer = self._autocompile_timer
        except AttributeError:
            timer = self._autocompile_timer = QTimer()
            timer.timeout.connect(self.autocompileTimeout)
            timer.setSingleShot(False)
        if enabled:
            timer.start(1000)
        else:
            timer.stop()
    
    def autocompileTimeout(self):
        """Called when the autocompile timer expires."""
        eng = engraver(self.mainwindow())
        doc = eng.document()
        rjob = jobmanager.job(doc)
        if rjob and rjob.isRunning() and not jobattributes.get(rjob).hidden:
            return
        
        mgr = AutoCompileManager.instance(doc)
        may_compile = mgr.may_compile()
        if not may_compile:
            cur = self.mainwindow().currentDocument()
            if doc is not cur:
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
        self._dirty = document.isModified() or not resultfiles.results(document).files('.pdf')
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
            if (dinfo.mode() == "lilypond" and dinfo.complete()):
                h = self.token_hash()
                if h != self._hash:
                    self._hash = h
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


