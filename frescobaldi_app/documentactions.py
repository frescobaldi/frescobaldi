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
Manages some actions and per-document preferences that are set in metainfo.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QAction

import actioncollection
import actioncollectionmanager
import highlighter
import metainfo
import plugin


def get(mainwindow):
    """Returns the DocumentActions instance for the specified MainWindow."""
    return DocumentActions.instance(mainwindow)


class DocumentActions(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.view_highlighting.triggered.connect(self.toggleHighlighting)
        ac.tools_indent_auto.triggered.connect(self.toggleAutoIndent)
        ac.tools_indent_indent.triggered.connect(self.reIndent)
        mainwindow.currentDocumentChanged.connect(self.updateDocActions)
        
    def updateDocActions(self, doc):
        minfo = metainfo.info(doc)
        if minfo.highlighting:
            highlighter.highlighter(doc)
        ac = self.actionCollection
        ac.view_highlighting.setChecked(minfo.highlighting)
        ac.tools_indent_auto.setChecked(minfo.autoindent)
        
    def updateOtherDocActions(self):
        """Calls updateDocActions() in other instances that show same document."""
        doc = self.mainwindow().currentDocument()
        for i in self.instances():
            if i is not self and i.mainwindow().currentDocument() == doc:
                i.updateDocActions(doc)
        
    def toggleAutoIndent(self):
        doc = self.mainwindow().currentDocument()
        minfo = metainfo.info(doc)
        minfo.autoindent = not minfo.autoindent
        self.updateOtherDocActions()
    
    def reIndent(self):
        import indent
        indent.reIndent(self.mainwindow().currentView().textCursor())
        
    def toggleHighlighting(self):
        doc = self.mainwindow().currentDocument()
        minfo = metainfo.info(doc)
        minfo.highlighting = not minfo.highlighting
        highlighter.highlighter(doc).setHighlighting(minfo.highlighting)
        self.updateOtherDocActions()
        

class Actions(actioncollection.ActionCollection):
    name = "documentactions"
    def createActions(self, parent):
        self.view_highlighting =QAction(parent)
        self.view_highlighting.setCheckable(True)
        self.tools_indent_auto = QAction(parent)
        self.tools_indent_auto.setCheckable(True)
        self.tools_indent_indent = QAction(parent)
        
    def translateUI(self):
        self.view_highlighting.setText(_("Syntax &Highlighting"))
        self.tools_indent_auto.setText(_("&Automatic Indent"))
        self.tools_indent_indent.setText(_("Re-&Indent"))


