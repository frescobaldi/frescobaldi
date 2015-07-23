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
The Manuscriot Viewer context menu additions.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QMenu, QAction, QActionGroup

from viewers import contextmenu

class ManuscriptViewerContextMenu(contextmenu.ViewerContextMenu):

    def __init__(self, panel):
        super(ManuscriptViewerContextMenu, self).__init__(panel)

    def addShowActions(self):
        """Adds a submenu giving access to the (other)
        opened manuscripts"""
        mds = self._panel.actionCollection.music_document_select
        docs = mds._documents
        document_actions = {}
        multi_docs = len(docs) > 1
        current_doc_filename = self._panel.widget().currentDocument().filename()

        m = self._menu
        sm = QMenu(m)
        sm.setTitle(_("Show"))
        sm.setEnabled(multi_docs)
        ag = QActionGroup(m)
        ag.triggered.connect(self._panel.widget().slotShowDocument)

        for d in docs:
            action = QAction(sm)
            action.setText(d.name())
            action._document_filename = d.filename()
            # TODO: Tooltips aren't shown by Qt (it seems)
            action.setToolTip(d.filename())
            action.setCheckable(True)
            action.setChecked(d.filename() == current_doc_filename)

            # variant a) doesn't work because the slot is never reached
            # action.triggered.connect(self.slotShowDocument)

            # variant b) doesn't work because it's always the *last*
            # entry that is triggered
#            document_actions[action] = d.filename()
            # @action.triggered.connect
            # def showDocument():
            #     # TODO: Problem is: action.toolTip() is obviously always
            #     # the one from the *last* entry.
            #     print document_actions[action]
            #     mds.setActiveDocument(document_actions[action])

            ag.addAction(action)
            sm.addAction(action)

        m.addSeparator()
        m.addMenu(sm)


    def addCloseActions(self):
        """Add actions to close documents.
        This is not implemented in the base class"""
        m = self._menu
        ac = self._panel.actionCollection
        docs = self._panel.actionCollection.music_document_select._documents
        if docs:
            sm = QMenu(m)
            sm.setTitle(_("Close"))
            m.addMenu(sm)
            sm.addAction(ac.manuscript_close)
            multi_docs = len(docs) > 1
            ac.manuscript_close_other.setEnabled(multi_docs)
            ac.manuscript_close_all.setEnabled(multi_docs)
            sm.addAction(ac.manuscript_close_other)
            sm.addAction(ac.manuscript_close_all)

    def addReloadAction(self):
        """Add action to reload document."""
        current_document = self._panel.widget().currentDocument()
        if current_document:
            m = self._menu
            ac = self._panel.actionCollection
            m.addAction(ac.music_reload)
