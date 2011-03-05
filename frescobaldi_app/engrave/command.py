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

import itertools
import os
import re

from PyQt4.QtCore import QSettings

import ly.tokenize.lilypond
import job
import mode
import variables
import scratchdir
import tokeniter
import lilypondinfo


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
    documentMode = mode.documentMode(document)
    
    includepath = []
    
    if filename and redir:
        # We have a local filename and the document wants another one as master
        filename = os.path.normpath(os.path.join(os.path.dirname(filename), redir))
        if os.path.exists(filename):
            documentMode = mode.fileMode(filename)
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
        version = documentVersion(document)
        if version:
            for i in infos:
                if i.version >= version:
                    return i
    # find default version
    default = s.value("default", "lilypond")
    for i in infos:
        if info.command == default:
            return info
    for i in infos:
        if info.command == "lilypond":
            return info
    return infos[0]
        

def documentVersion(document):
    """Returns the LilyPond version set in the document as a tuple of ints, if present."""
    source = iter(t for block in tokeniter.allBlocks(document) for t in tokeniter.tokens(block))
    for token in source:
        if isinstance(token, ly.tokenize.lilypond.Keyword) and token == "\\version":
            for token in source:
                if not isinstance(token, (ly.tokenize.Space, ly.tokenize.Comment)):
                    break
            if token == '"':
                pred = lambda t: t != '"'
            else:
                pred = lambda t: not isinstance(t, ly.tokenize.Space, ly.tokenize.Comment)
            version = ''.join(itertools.takewhile(pred, source))
            return tuple(map(int, re.findall(r"\d+", version)))        
    # if no result, just search the whole document
    m = re.search(r'\\version\s*"(\d+\.\d+(\.\d+)*)"', document.toPlainText())
    if m:
        return tuple(map(int, m.group(1).split('.')))

