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
Manages some actions and per-document preferences that are set in metainfo.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QAction, QKeySequence

import actioncollection
import actioncollectionmanager
import highlighter
import metainfo
import plugin
import icons


def get(mainwindow):
    """Returns the DocumentActions instance for the specified MainWindow."""
    return DocumentActions.instance(mainwindow)


class DocumentActions(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.view_goto_file_or_definition.triggered.connect(self.gotoFileOrDefinition)
        ac.edit_cut_assign.triggered.connect(self.cutAssign)
        ac.view_highlighting.triggered.connect(self.toggleHighlighting)
        ac.tools_indent_auto.triggered.connect(self.toggleAuto_indent)
        ac.tools_indent_indent.triggered.connect(self.re_indent)
        ac.tools_reformat.triggered.connect(self.reFormat)
        ac.tools_remove_trailing_whitespace.triggered.connect(self.removeTrailingWhitespace)
        ac.tools_convert_ly.triggered.connect(self.convertLy)
        ac.tools_quick_remove_articulations.triggered.connect(self.quickRemoveArticulations)
        ac.tools_quick_remove_ornaments.triggered.connect(self.quickRemoveOrnaments)
        ac.tools_quick_remove_instrument_scripts.triggered.connect(self.quickRemoveInstrumentScripts)
        ac.tools_quick_remove_slurs.triggered.connect(self.quickRemoveSlurs)
        ac.tools_quick_remove_dynamics.triggered.connect(self.quickRemoveDynamics)
        ac.tools_quick_remove_markup.triggered.connect(self.quickRemoveMarkup)
        
        mainwindow.currentDocumentChanged.connect(self.updateDocActions)
        mainwindow.selectionStateChanged.connect(self.updateSelectionActions)
        
    def updateDocActions(self, doc):
        minfo = metainfo.info(doc)
        if minfo.highlighting:
            highlighter.highlighter(doc)
        ac = self.actionCollection
        ac.view_highlighting.setChecked(minfo.highlighting)
        ac.tools_indent_auto.setChecked(minfo.auto_indent)
    
    def updateSelectionActions(self, selection):
        self.actionCollection.edit_cut_assign.setEnabled(selection)
        self.actionCollection.tools_quick_remove_articulations.setEnabled(selection)
        self.actionCollection.tools_quick_remove_ornaments.setEnabled(selection)
        self.actionCollection.tools_quick_remove_instrument_scripts.setEnabled(selection)
        self.actionCollection.tools_quick_remove_slurs.setEnabled(selection)
        self.actionCollection.tools_quick_remove_dynamics.setEnabled(selection)
        self.actionCollection.tools_quick_remove_markup.setEnabled(selection)
    
    def currentView(self):
        return self.mainwindow().currentView()
    
    def currentDocument(self):
        return self.mainwindow().currentDocument()
        
    def updateOtherDocActions(self):
        """Calls updateDocActions() in other instances that show same document."""
        doc = self.currentDocument()
        for i in self.instances():
            if i is not self and i.currentDocument() == doc:
                i.updateDocActions(doc)
    
    def gotoFileOrDefinition(self):
        import open_file_at_cursor
        result = open_file_at_cursor.open_file_at_cursor(self.mainwindow())
        if not result:
            import definition
            definition.goto_definition(self.mainwindow())
    
    def cutAssign(self):
        import cut_assign
        cut_assign.cut_assign(self.currentView().textCursor())
        
    def toggleAuto_indent(self):
        minfo = metainfo.info(self.currentDocument())
        minfo.auto_indent = not minfo.auto_indent
        self.updateOtherDocActions()
    
    def re_indent(self):
        import indent
        indent.re_indent(self.currentView().textCursor())
    
    def reFormat(self):
        import reformat
        reformat.reformat(self.currentView().textCursor())
    
    def removeTrailingWhitespace(self):
        import reformat
        reformat.remove_trailing_whitespace(self.currentView().textCursor())
    
    def toggleHighlighting(self):
        doc = self.currentDocument()
        minfo = metainfo.info(doc)
        minfo.highlighting = not minfo.highlighting
        highlighter.highlighter(doc).setHighlighting(minfo.highlighting)
        self.updateOtherDocActions()
    
    def convertLy(self):
        import convert_ly
        convert_ly.convert(self.mainwindow())
    
    def quickRemoveArticulations(self):
        import quickremove
        quickremove.articulations(self.mainwindow().textCursor())
    
    def quickRemoveOrnaments(self):
        import quickremove
        quickremove.ornaments(self.mainwindow().textCursor())
    
    def quickRemoveInstrumentScripts(self):
        import quickremove
        quickremove.instrument_scripts(self.mainwindow().textCursor())
    
    def quickRemoveSlurs(self):
        import quickremove
        quickremove.slurs(self.mainwindow().textCursor())
    
    def quickRemoveDynamics(self):
        import quickremove
        quickremove.dynamics(self.mainwindow().textCursor())
    
    def quickRemoveMarkup(self):
        import quickremove
        quickremove.markup(self.mainwindow().textCursor())


class Actions(actioncollection.ActionCollection):
    name = "documentactions"
    def createActions(self, parent):
        self.edit_cut_assign = QAction(parent)
        self.view_highlighting = QAction(parent)
        self.view_highlighting.setCheckable(True)
        self.view_goto_file_or_definition = QAction(parent)
        self.tools_indent_auto = QAction(parent)
        self.tools_indent_auto.setCheckable(True)
        self.tools_indent_indent = QAction(parent)
        self.tools_reformat = QAction(parent)
        self.tools_remove_trailing_whitespace = QAction(parent)
        self.tools_convert_ly = QAction(parent)
        self.tools_quick_remove_articulations = QAction(parent)
        self.tools_quick_remove_ornaments = QAction(parent)
        self.tools_quick_remove_instrument_scripts = QAction(parent)
        self.tools_quick_remove_slurs = QAction(parent)
        self.tools_quick_remove_dynamics = QAction(parent)
        self.tools_quick_remove_markup = QAction(parent)
        
        self.edit_cut_assign.setIcon(icons.get('edit-cut'))

        self.view_goto_file_or_definition.setShortcut(QKeySequence(Qt.ALT + Qt.Key_Return))
        self.edit_cut_assign.setShortcut(QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_X))
    
    def translateUI(self):
        self.edit_cut_assign.setText(_("Cut and Assign..."))
        self.view_highlighting.setText(_("Syntax &Highlighting"))
        self.view_goto_file_or_definition.setText(_("View File or Definition at &Cursor"))
        self.tools_indent_auto.setText(_("&Automatic Indent"))
        self.tools_indent_indent.setText(_("Re-&Indent"))
        self.tools_reformat.setText(_("&Format"))
        self.tools_remove_trailing_whitespace.setText(_("Remove Trailing &Whitespace"))
        self.tools_convert_ly.setText(_("&Update with convert-ly...")) 
        self.tools_quick_remove_articulations.setText(_("Remove &Articulations"))
        self.tools_quick_remove_ornaments.setText(_("Remove &Ornaments"))
        self.tools_quick_remove_instrument_scripts.setText(_("Remove &Instrument Scripts"))
        self.tools_quick_remove_slurs.setText(_("Remove &Slurs"))
        self.tools_quick_remove_dynamics.setText(_("Remove &Dynamics"))
        self.tools_quick_remove_markup.setText(_("Remove Text &Markup (from music)"))

