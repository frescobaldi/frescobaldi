# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Manages the progress bar in the status bar of ViewSpaces.
"""


from PyQt4.QtCore import Qt
from PyQt4.QtGui import QProgressBar

import app
import plugin


class ProgressBar(plugin.ViewSpacePlugin):
    """A Simple progress bar to show a Job is running."""
    def __init__(self, viewSpace):
        bar = self._bar = QProgressBar()
        bar.setMaximumHeight(14)
        layout = viewSpace.status.layout()
        layout.addWidget(self._bar, 1)
        


app.viewSpaceCreated.connect(ProgressBar.instance)
