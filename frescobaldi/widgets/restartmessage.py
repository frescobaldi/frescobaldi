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
A message box suggesting a restart.

Some operations make it necessary to restart Frescobaldi,
either for simply taking effect or to avoid possible instabilities.
These include switching the Git branch or removing extensions.
"""

from PyQt6.QtWidgets import QMessageBox

import app

def suggest_restart(operation):
    """Show a message box informing about the need to
    restart the application. the 'operation' argument
    is used to customize the message."""

    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Icon.Warning)
    msgBox.setText(_("Restart Required"))

    # Translate first, then use format
    translated_template = _(
        "An operation requires a restart of Frescobaldi:\n\n"
        "   {}\n\n"
        "Some new functionality may not be available before, "
        "or the application may even become unstable.\n\n"
        "Do you want to restart now?\n"
        "You can also save open files first and restart manually."
    )
    formatted_message = translated_template.format(operation)
    msgBox.setInformativeText(formatted_message)

    msgBox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    if msgBox.exec() == QMessageBox.StandardButton.Ok:
        app.activeWindow().restart()
