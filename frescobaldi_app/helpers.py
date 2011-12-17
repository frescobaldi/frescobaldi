# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

import os
import re
import subprocess

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QDesktopServices

def command(type):
    """Returns the command for the specified type as a list.
    
    Returns None if no command was specified.
    
    """
    cmd = QSettings().value("helper_applications/" + type, "")
    if not cmd:
        return
    
    if os.path.isabs(cmd) and os.access(cmd, X_OK):
        return [cmd]

    # remove double quotes, keeping quoted parts together
    # (because shlex does not yet work with unicode...)
    command = [item.replace('"', '') for item in 
        re.findall(r'[^\s"]*"[^"]*"[^\s"]*|[^\s"]+', cmd)]
    
    return command


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
        QDesktopServices.openUrl(url)
        return
    
    prog = cmd.pop(0)
    
    workdir = None
    if url.toLocalFile():
        workdir = os.path.dirname(url.toLocalFile())
    
    if any('$f' in a or '$u' in a for a in cmd):
        cmd = [a.replace('$u', url.toString())
                if '$u' in a else a.replace('$f', url.toLocalFile())
                for a in cmd]
    elif type in ("browser", "email"):
        cmd.append(url.toString())
    elif type != "shell":
        cmd.append(url.toLocalFile())
    
    subprocess.Popen([prog] + cmd, cwd=workdir)


