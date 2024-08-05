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
Run LilyPond to get various types of output.
"""


from PyQt6.QtCore import QSize, Qt

import app
import job
import log
import qutil
import widgets.dialog


class Dialog(widgets.dialog.Dialog):
    """Dialog to run a certain LilyPond command and simply show the log."""
    def __init__(self, parent):
        super().__init__(
            parent,
            buttons=('close',),
        )
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.log = log.Log(self)
        self.setMainWidget(self.log)

    def run_command(self, info, args, title=None):
        """Run lilypond from info with the args list, and a job title."""
        j = self.job = job.lilypond.LilyPondJob(info)
        j.command.extend(list(args))
        if title:
            j.set_title(title)
        self.log.connectJob(j)
        j.start()
