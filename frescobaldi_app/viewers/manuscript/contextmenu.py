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

from PyQt4.QtGui import QMenu

from viewers import contextmenu

class ManuscriptViewerContextMenu(contextmenu.AbstractViewerContextMenu):

    def __init__(self, panel):
        super(ManuscriptViewerContextMenu, self).__init__(panel)


    def addReloadAction(self):
        """Add action to reload document."""
        current_document = self._panel.widget().currentViewdoc()
        if current_document:
            m = self._menu
            ac = self._actionCollection
            m.addAction(ac.viewer_reload)

    def show(self, position, link, cursor):
        """Build the panel's context menu dynamically.
        Implements the template method pattern to allow
        subclasses to override each step."""
        methods = [self.addCopyImageAction,
            self.addCursorLinkActions,
            # Actions affecting the currently opened documents
            self.addShowActions,
            self.addOpenCloseActions,
            self.addReloadAction,
            # Actions affecting the viewer's state
            self.addZoomActions,
            self.addSynchronizeAction,
            self.addShowToolbarAction]
        super(ManuscriptViewerContextMenu, self).show(position, link, cursor, methods)
