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

from viewers import contextmenu

class ManuscriptViewerContextMenu(contextmenu.ViewerContextMenu):

    def __init__(self, panel):
        super(ManuscriptViewerContextMenu, self).__init__(panel)

    def addCloseActions(self):
        """Add actions to close documents.
        This is not implemented in the base class"""
        m = self._menu
        ac = self._panel.actionCollection
        docs = self._panel.actionCollection.music_document_select._documents
        if docs:
            m.addSeparator()
            m.addAction(ac.manuscript_close)
            multi_docs = len(docs) > 1
            ac.manuscript_close_other.setEnabled(multi_docs)
            ac.manuscript_close_all.setEnabled(multi_docs)
            m.addAction(ac.manuscript_close_other)
            m.addAction(ac.manuscript_close_all)
