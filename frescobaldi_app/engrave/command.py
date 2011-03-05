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

import ly.tokenize
import job
import scratchdir
import tokeniter
import documentinfo
import lilypondinfo
import variables


def jobFile(document, preview):
    """Returns a two tuple(filename, includepath) based on the given document.
    
    Preview mode is either True or False. The document contents is checked
    for the 'master', 'master-preview' and 'master-publish' variables to run
    the engraver on a different file instead, possibly based on preview mode.
    
    The includepath is most times empty, but may contain the document's directory,
    e.g. when it is modified but refers to other documents in it's own directory.
    
    """
    # Determine the filename to run LilyPond on
    filename = document.url().toLocalFile()
    v = variables.manager(document).variables()
    redir = v.get("master-preview" if preview else "master-publish", v.get("master"))
    mode = documentinfo.mode(document)
    
    includepath = []
    
    if filename and redir:
        # We have a local filename and the document wants another one as master
        filename = os.path.normpath(os.path.join(os.path.dirname(filename), redir))
        if os.path.exists(filename):
            try:
                with open(filename) as f:
                    text = f.read(1000).decode('utf-8', 'ignore')
            except (OSError, IOError):
                pass
            else:
                mode = ly.tokenize.guessMode(text)
    elif not filename or document.isModified():
        # We need to use a scratchdir to save our contents to
        scratch = scratchdir.scratchdir(document)
        scratch.saveDocument()
        if filename:
            for block in tokeniter.allBlocks(document):
                if "\\include" in tokeniter.tokens(block):
                    includepath.append(os.path.dirname(filename))
                    break
        filename = scratch.path()
    
    return filename, includepath
    

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
    filename, includepath = jobFile(document, preview)
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
    return j


