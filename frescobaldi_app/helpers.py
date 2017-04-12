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
Helper application stuff.
"""


import os
import re
import subprocess
import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QMessageBox

def shell_split(cmd):
    """Split a string like the UNIX shell, returning a list.

    Double quoted parts are kept together with the quotes removed.

    """
    # remove double quotes, keeping quoted parts together
    # (because shlex does not yet work with unicode...)
    return [item.replace('"', '') for item in
        re.findall(r'[^\s"]*"[^"]*"[^\s"]*|[^\s"]+', cmd)]


def command(type):
    """Returns the command for the specified type as a list.

    Returns None if no command was specified.

    """
    cmd = QSettings().value("helper_applications/" + type, "")
    if not cmd:
        return

    if os.path.isabs(cmd) and os.access(cmd, os.X_OK):
        return [cmd]

    return shell_split(cmd)


def openUrl(url, type="browser"):
    """Opens the specified QUrl, using the specified type."""
    # be sure to pick a suitable type
    if url.scheme() == "mailto":
        type = "email"
    elif type == "browser" and url.toLocalFile():
        ext = os.path.splitext(url.toLocalFile())[1].lower()
        if os.path.isdir(url.toLocalFile()):
            type = "directory"
        elif ext == '.pdf':
            type = "pdf"
        elif ext in ('.png', '.jpg', '.jpeg'):
            type = "image"
        elif ext in ('.midi', '.mid'):
            type = "midi"

    # get the command
    cmd = command(type)
    if not cmd:
        if type != "shell":
            QDesktopServices.openUrl(url)
            return
        for cmd in terminalCommands():
            break # get the first

    prog = cmd.pop(0)

    workdir = None
    if url.toLocalFile():
        workdir = url.toLocalFile()
        if type != "shell":
            workdir = os.path.dirname(workdir)

    if any('$f' in a or '$u' in a for a in cmd):
        cmd = [a.replace('$u', url.toString())
                if '$u' in a else a.replace('$f', url.toLocalFile())
                for a in cmd]
    elif type in ("browser", "email"):
        cmd.append(url.toString())
    elif type != "shell":
        cmd.append(url.toLocalFile())

    try:
        subprocess.Popen([prog] + cmd, cwd=workdir)
    except OSError:
        QMessageBox.critical(None, _("Error"), _(
            "Could not start {program}.\n"
            "Please check path and permissions.").format(program=prog))


def terminalCommands():
    """Yields suitable commands to open a terminal/shell window.

    There is always yielded at least one, which is suitable as default.

    """
    if os.name == "nt":
        yield ['cmd.exe']
    elif sys.platform == 'darwin':
        yield ['open', '-a', 'Terminal', '$f']
    else:
        # find a default linux terminal
        paths = os.environ.get('PATH', os.defpath).split(os.pathsep)
        for cmd in (
            ['lxterminal', '--working-directory=$f'],
            ['xfce4-terminal', '--working-directory=$f'],
            ['konsole', '--workdir', '$f'],
            ['gnome-terminal', '--working-directory=$f'],
            ):
            for p in paths:
                if p:
                    prog = os.path.join(p, cmd[0])
                    if os.access(prog, os.X_OK):
                        yield cmd
        yield ['xterm']


