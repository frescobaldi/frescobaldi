# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
A tool to display an engraver's copy in a dock.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QSettings, Qt
from PyQt4.QtGui import (
    QAction, QKeySequence, QVBoxLayout, QToolButton,
    QHBoxLayout, QPushButton, QMessageBox)

import actioncollection
import actioncollectionmanager
import app
import icons
import panel
import userguide.util

import viewers
from viewers import popplerwidget
from viewers import documents

class ManuscriptViewPanel(viewers.AbstractViewPanel):
    """Manuscript Viewer Tool."""
    def __init__(self, mainwindow):
        super(ManuscriptViewPanel, self).__init__(mainwindow, ManuscriptActions)
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+A"))
        mainwindow.addDockWidget(Qt.RightDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("Manuscript"))
        self.toggleViewAction().setText(_("Manuscript Viewer"))

    def createWidget(self):
        from . import widget
        return super(ManuscriptViewPanel, self).configureWidget(widget.ManuscriptViewWidget(self))

    @viewers.activate
    def reloadView(self):
        active_manuscript = self.widget().currentDocument()
        if active_manuscript:
            reread = documents.Document(active_manuscript.filename())
            mds = self.actionCollection.music_document_select
            mds.replaceManuscript(active_manuscript, reread)

    def _openMusicCaption(self):
        """Returns the caption for the file open dialog."""
        return app.caption(_("dialog title", "Open Manuscript(s)"))


class ManuscriptActions(viewers.Actions):
    name = "manuscript"

    def createActions(self, parent=None):
        super(ManuscriptActions, self).createActions(parent)
        # overridden actions
        self.music_document_select = ManuscriptDocumentChooserAction(parent)
        # new actions
        self.music_open = QAction(parent)
        self.music_open.setIcon(icons.get('document-open'))
        self.manuscript_close = QAction(parent)
        self.manuscript_close.setIcon(icons.get('document-close'))
        self.manuscript_close_other = QAction(parent)
        # don't set an icon? self.manuscript_close_other.setIcon(icons.get())
        self.manuscript_close_all = QAction(parent)
        # don't set an icon?

    def translateUI(self):
        super(ManuscriptActions, self).translateUI()
        self.music_document_select.setText(_("Select Manuscript Document"))
        self.music_open.setText(_("Open manuscript(s)"))
        self.music_open.setIconText(_("Open"))
        self.manuscript_close.setText(_("Close manuscript"))
        self.manuscript_close.setIconText(_("Close"))
        self.manuscript_close_other.setText(_("Close other manuscripts"))
        self.manuscript_close_all.setText(_("Close all manuscripts"))

    def title(self):
        return _("Manuscript")


class ManuscriptDocumentChooserAction(viewers.DocumentChooserAction):
    """Extends the parent class and also keeps track of when a document is
    opened or closed in the manuscript viewer.
    """

    def __init__(self, panel):
        super(ManuscriptDocumentChooserAction, self).__init__(panel)

    def slotDocumentChanged(self, doc):
        """Called when the mainwindow changes its current document."""
        # for now do nothing
        # when we have a tie between documents and manuscripts
        # something will have to be done here
        pass

    def slotDocumentUpdated(self, doc, job):
        """Called when a Job, finished on the document, has created new PDFs."""
        # for now do nothing
        pass

    def removeManuscript(self, document):
        if document:
            self._documents.remove(document)
            self.updateDocument()

    def removeOtherManuscripts(self, document):
        self._documents = [document]
        self.updateDocument()

    def removeAllManuscripts(self):
        self._documents = []
        self.updateDocument()

    def loadManuscripts(self, manuscripts, active_manuscript = "",
                        clear = False, sort = False):
        """Load or add the manuscripts from a list of filenames"""

        # When switching sessions we replace the manuscripts
        # otherwise the loaded manuscripts are added.
        if clear:
            self.removeAllManuscripts()
            self.parent().widget().clear()

        # process manuscripts, adding fallback position if required.
        # load manuscript or add to list of missing filenames
        missing = []
        for m in manuscripts:
            if isinstance(m, tuple):
                file = m[0]
                position = m[1]
            else:
                file = m
                position = (0, 0, 0)
            if os.path.isfile(file):
                doc = documents.Document(file)
                self._documents.append(doc)
                self.parent().widget()._positions[doc] = position
            else:
                missing.append(file)

        # bring active document to front
        # (will automatically 'pass' if empty)
        self.setActiveDocument(active_manuscript)

        # Hack to suppress the resize event that
        # clears the position of the current document
        self.parent().widget().view._centerPos = None

        if sort:
            self.sortManuscripts()
        else:
            self.updateDocument()

        # report missing docs
        if missing:
            self.documentsMissing.emit(missing)

    def sortManuscripts(self):
        """sort the open manuscripts alphabetically."""
        # This is completly dysfunctional. I just copied it
        # over from loadManuscripts().

        # build a list of manuscript files taking the existing list
        # and adding the to-be-opened ones. Check for duplicates.
        msfiles = [d.filename() for d in self._documents]
        for m in in_names:
            if not m in msfiles:
                msfiles.append(m)

        # create a dict structure to sort and access all files
        name_dict = {}
        msnames = []
        for f in msfiles:
            name = os.path.basename(f)
            if name in name_dict: # handle duplicate filenames
                name_dict[name].append(f)
            else:
                name_dict[name] = [f]
                msnames.append(name)
        # sorted list of unique filenames.
        # a filename *may* refer to several files in different directories
        msnames = sorted(msnames)

        # iterate over manuscript names (and potential duplicates)
        # and build new documents list. This ensures that the documents are
        # sorted by their file name (ignoring directory names).
        # Take existing Document objects if available
        docs = []
        missing = []
        for n in msnames:
            for f in name_dict[n]:
                index = msfiles.index(f)
                if index >= len(self._documents): # no document object yet
                    if os.path.isfile(f):
                        doc = documents.Document(f)
                        docs.append(doc)
                        self._positions[doc] = manuscripts[msfiles.index(f)][1]
                        print "position:",self._positions[doc]
                    else:
                        missing.append(f)
                else:
                    docs.append(self._documents[index])
                if f == active_manuscript_filename:
                    self._currentIndex = len(docs) - 1

        # apply results
        self._documents = docs
        self.updateDocument()

    def addManuscript(self, document):
        """Add a manuscript to our chooser."""
        self._documents.append(document)
        self._currentIndex = len(self._documents) - 1
        self.updateDocument()

    def replaceManuscript(self, olddoc, newdoc):
        """Instead of adding a new document replace an existing."""
        try:
            docindex = self._documents.index(olddoc)
            self._documents[docindex] = newdoc
            self.updateDocument()
        except ValueError:
            # no replacement possible because the original doc isn't found
            pass

    def setActiveDocument(self, filename):
        """Activate the given document if it's in the list of documents"""
        filenames = [d.filename() for d in self._documents]
        if filename in filenames:
            self._currentIndex = filenames.index(filename)
            self.updateDocument()
