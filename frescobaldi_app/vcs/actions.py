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
VCS actions
"""

from PyQt5.QtWidgets import QAction

import icons
import actioncollection

class ActionCollection(actioncollection.ActionCollection):
    name = "vcs"
    def createActions(self, parent=None):
        #TODO: Not implemented yet: use git add to track the current document.
        # Must be enabled according to tracked state of the current view.
        self.vcs_track_doc = QAction(parent)
        self.vcs_revert_hunk = QAction(parent)
        self.vcs_revert_file = QAction(parent)

        # icons
        # TODO: Find proper icon
        self.vcs_track_doc.setIcon(icons.get('document-new'))


    def translateUI(self):
        self.vcs_track_doc.setText(_("action: track document", "&Track document"))
        self.vcs_revert_hunk.setText(_("action: revert hunk", "Revert current &hunk"))
        self.vcs_revert_file.setText(_("action: revert file", "Revert current &file"))
