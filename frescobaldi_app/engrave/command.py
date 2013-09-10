# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Creates the commandline or Job to engrave a music document.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QSettings

import job
import documentinfo
import lilypondinfo


def info(document):
    """Returns a LilyPondInfo instance that should be used by default to engrave the document."""
    version = documentinfo.info(document).version()
    if version and QSettings().value("lilypond_settings/autoversion", False, bool):
        return lilypondinfo.suitable(version)
    return lilypondinfo.preferred()
        

def defaultJob(document, preview):
    """Returns a default job for the document."""
    filename, mode, includepath = documentinfo.info(document).jobinfo(True)
    includepath.extend(documentinfo.info(document).includepath())
    i = info(document)
    j = job.Job()
    
    command = [i.abscommand()]
    s = QSettings()
    s.beginGroup("lilypond_settings")
    if s.value("delete_intermediate_files", True, bool):
        command.append('-ddelete-intermediate-files')
    else:
        command.append('-dno-delete-intermediate-files')
    command.append('-dpoint-and-click' if preview else '-dno-point-and-click')
    command.append('--pdf')
    command.extend('-I' + path for path in includepath)
    j.directory = os.path.dirname(filename)
    command.append(filename)
    j.command = command
    if s.value("no_translation", False, bool):
        j.environment['LANG'] = 'C'
    j.setTitle("{0} {1} [{2}]".format(
        os.path.basename(i.command), i.versionString(), document.documentName()))
    return j


