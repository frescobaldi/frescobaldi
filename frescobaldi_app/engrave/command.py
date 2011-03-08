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
Creates the commandline or Job to engrave a music document.
"""

import os

from PyQt4.QtCore import QSettings

import job
import documentinfo
import lilypondinfo


def info(document):
    """Returns a LilyPondInfo instance that should be used by default to engrave the document."""
    infos = lilypondinfo.infos()
    if not infos:
        return lilypondinfo.LilyPondInfo("lilypond")
    elif len(infos) == 1:
        return infos[0]
    s = QSettings()
    s.beginGroup("lilypond_settings")
    if s.value("autoversion", True) in (True, "true"):
        # Determine version set in document
        infos.sort(key=lambda i: i.version)
        version = documentinfo.version(document)
        if version:
            for i in infos:
                if i.version >= version:
                    return i
            return infos[-1]
    # find default version
    default = s.value("default", "lilypond")
    for i in infos:
        if i.command == default:
            return i
    for i in infos:
        if i.command == "lilypond":
            return i
    return infos[0]
        

def defaultJob(document, preview):
    """Returns a default job for the document."""
    filename, mode, includepath = documentinfo.jobinfo(document, True)
    i = info(document)
    j = job.Job()
    
    # TEMP!!!
    command = [i.command]
    command.append('-dpoint-and-click' if preview else '-dno-point-and-click')
    command.append('--pdf')
    command.extend('-I' + path for path in includepath)
    j.directory, filename = os.path.split(filename)
    command.append(filename)
    j.command = command
    j.setTitle("{0} {1}".format(os.path.basename(i.command), i.versionString))
    return j


