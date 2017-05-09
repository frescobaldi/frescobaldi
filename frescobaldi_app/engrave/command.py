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
Creates the commandline or Job to engrave a music document.
"""


import os, sys

from PyQt5.QtCore import QSettings

import job
import documentinfo
import lilypondinfo


def info(document):
    """Returns a LilyPondInfo instance that should be used by default to engrave the document."""
    version = documentinfo.docinfo(document).version()
    if version and QSettings().value("lilypond_settings/autoversion", False, bool):
        return lilypondinfo.suitable(version)
    return lilypondinfo.preferred()


def defaultJob(document, args=None):
    """Return a default job for the document.

    The 'args' argument, if given, must be a list of commandline arguments
    that are given to LilyPond, and may enable specific preview modes.

    If args is not given, the Job will cause LilyPond to run in Publish mode,
    with point and click turned off.

    """
    filename, includepath = documentinfo.info(document).jobinfo(True)

    i = info(document)
    j = job.Job()

    command = [i.abscommand() or i.command]
    s = QSettings()
    s.beginGroup("lilypond_settings")
    if s.value("delete_intermediate_files", True, bool):
        command.append('-ddelete-intermediate-files')
    else:
        command.append('-dno-delete-intermediate-files')

    if args:
        command.extend(args)
    else:
        # publish mode
        command.append('-dno-point-and-click')

    if s.value("default_output_target", "pdf", str) == "svg":
        # engrave to SVG
        command.append('-dbackend=svg')
    else:
        # engrave to PDF
        if not args:
            # publish mode
            if s.value("embed_source_code", False, bool) and i.version() >= (2, 19, 39):
                command.append('-dembed-source-code')
        command.append('--pdf')


    command.extend('-I' + path for path in includepath)
    j.directory = os.path.dirname(filename)
    command.append(filename)
    j.command = command
    j.environment['LD_LIBRARY_PATH'] = i.libdir()
    if s.value("no_translation", False, bool):
        j.environment['LANG'] = 'C'
        j.environment['LC_ALL'] = 'C'
    j.set_title("{0} {1} [{2}]".format(
        os.path.basename(i.command), i.versionString(), document.documentName()))
    return j
