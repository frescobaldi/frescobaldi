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

import os, sys

from PyQt4.QtCore import QSettings

import job
import documentinfo
import lilypondinfo
import preview_mode


def info(document):
    """Returns a LilyPondInfo instance that should be used by default to engrave the document."""
    version = documentinfo.info(document).version()
    if version and QSettings().value("lilypond_settings/autoversion", False, bool):
        return lilypondinfo.suitable(version)
    return lilypondinfo.preferred()

# dictionary mapping internal option names to command line switches
previewoptions = {
    'skylines': '-ddebug-display-skylines', 
    'control-points': '-ddebug-control-points', 
    'voices': '-ddebug-voices', 
    'directions': '-ddebug-directions',
    'grob-anchors': '-ddebug-grob-anchors',
    'grob-names': '-ddebug-grob-names',
    'custom-file': '-ddebug-custom-file', 
    'paper-columns': '-ddebug-paper-columns', 
    'annotate-spacing': '-ddebug-annotate-spacing',
}

def check_option(s, command, key):
    """
    Append a command line switch if the option is set
    """    
    if s.value(key, False, bool):
        command.append(previewoptions[key])

def preview_options():
    """
    Conditionally append command line options for Debug Modes
    """
    s = QSettings()
    s.beginGroup("lilypond_settings")
    cmd_options = ['-dpoint-and-click']
    args = []
    
    # add options that are checked in the dockable panel
    check_option(s, args, 'control-points')
    check_option(s, args, 'voices')
    check_option(s, args, 'skylines')
    check_option(s, args, 'directions')
    check_option(s, args, 'grob-anchors')
    check_option(s, args, 'grob-names')
    check_option(s, args, 'paper-columns')
    check_option(s, args, 'annotate-spacing')
    if s.value('custom-file', False, bool):
        file_to_include = s.value('custom-filename', '', type(''))
        if file_to_include:
            args.append('-ddebug-custom-file=' + file_to_include)
    
    # only add the extra commands when at least one debug mode is used
    if args:
        cmd_options.extend(args)
        # Add subdir with preview-mode files to search path
        cmd_options.append('-I' + preview_mode.__path__[0])
    
        # File that conditionally includes different formatters
        cmd_options.append('-dinclude-settings=debug-layout-options.ly') 
   
    return cmd_options
    
def defaultJob(document, preview):
    """Returns a default job for the document."""
    filename, mode, includepath = documentinfo.info(document).jobinfo(True)
    includepath.extend(documentinfo.info(document).includepath())
    i = info(document)
    j = job.Job()
    
    command = [i.abscommand()]
    if not command[0]:
        return False
    s = QSettings()
    s.beginGroup("lilypond_settings")
    if s.value("delete_intermediate_files", True, bool):
        command.append('-ddelete-intermediate-files')
    else:
        command.append('-dno-delete-intermediate-files')
    if preview:
        # Conditionally add Debug Mode options
        command.extend(preview_options())
    else:
        command.append('-dno-point-and-click')
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
