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
The Manuscript viewer panel widget.
"""


from viewers import popplerwidget
from . import contextmenu
from . import toolbar
import userguide.util

class ManuscriptViewWidget(popplerwidget.AbstractPopplerWidget):
    def __init__(self, panel):
        """Widget holding a manuscript view."""
        super(ManuscriptViewWidget, self).__init__(panel)

    def translateUI(self):
        self.setWhatsThis(_(
            "<p>The Manuscript Viewer displays an original manuscript " +
            "one is copying from.</p>\n"
            "<p>See {link} for more information.</p>").format(link=
                userguide.util.format_link(self.parent().viewerName())))

    def createContextMenu(self):
        """Creates the context menu."""
        self._contextMenu = contextmenu.ManuscriptViewerContextMenu(self.parent())

    def createToolbar(self):
        """Creates the toolbar."""
        return toolbar.ManuscriptViewerToolbar(self)
