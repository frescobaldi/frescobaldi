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
Delivers information about a document.
"""

from __future__ import unicode_literals

import itertools
import functools
import os
import re
import weakref

from PyQt4.QtCore import QSettings, QUrl

import ly.lex
import lydocinfo
import lydocument
import app
import fileinfo
import cursortools
import tokeniter
import plugin
import variables


__all__ = ['info', 'mode']


def info(document):
    """Returns a DocumentInfo instance for the given Document."""
    return DocumentInfo.instance(document)


def docinfo(document):
    """Return a LyDocInfo instance for the document."""
    return info(document).lydocinfo()


def mode(document, guess=True):
    """Returns the type of the given document. See DocumentInfo.mode()."""
    return info(document).mode(guess)


class _LyDocInfo(lydocinfo.DocInfoBase):
    def variables(self):
        return variables.get(self.document.document)

    
class DocumentInfo(plugin.DocumentPlugin):
    """Computes and caches various information about a Document."""
    def _reset(self):
        """Called when the document is changed."""
        del self._lydocinfo
        self.document().contentsChanged.disconnect(self._reset)
    
    def lydocinfo(self):
        """Return the lydocinfo instance for our document."""
        try:
            return self._lydocinfo
        except AttributeError:
            info = self._lydocinfo = _LyDocInfo(lydocument.Document(self.document()))
            self.document().contentsChanged.connect(self._reset)
            return info
    
    def mode(self, guess=True):
        """Returns the type of document ('lilypond, 'html', etc.).
        
        The mode can be set using the "mode" document variable.
        If guess is True (default), the mode is auto-recognized based on the contents
        if not set explicitly using the "mode" variable. In this case, this function
        always returns an existing mode.
        
        If guess is False, auto-recognizing is not done and the function returns None
        if the mode wasn't set explicitly.
        
        """
        mode = variables.get(self.document(), "mode")
        if mode in ly.lex.modes:
            return mode
        if guess:
            return self.lydocinfo().mode()
    
    def master(self):
        """Returns the master filename for the document, if it exists."""
        filename = self.document().url().toLocalFile()
        redir = variables.get(self.document(), "master")
        if filename and redir:
            path = os.path.normpath(os.path.join(os.path.dirname(filename), redir))
            if os.path.exists(path) and path != filename:
                return path

    def includepath(self):
        """Returns the configured include path. Currently the document does not matter."""
        try:
            include_path = QSettings().value("lilypond_settings/include_path", [], type(""))
        except TypeError:
            include_path = []
        return include_path
        
    def jobinfo(self, create=False):
        """Returns a three tuple(filename, mode, includepath) based on the given document.
        
        If the document is a local file, its contents is checked for the 'master' variable
        to run the engraver on a different file instead. The mode is then also chosen
        based on the contents of that other file.
        
        If no redirecting variables are found and the document is modified, its text
        is saved to a temporary area and that filename is returned. If the 'create'
        argument is False (the default), no temporary file is created, and in that
        case, the existing filename (may be empty) is returned.
        
        If a scratch area is used but the document has a local filename and includes
        other files, the original directory is given in the includepath list.
        
        """
        # Determine the filename to run the engraving job on
        includepath = []
        filename = self.master()
        if filename:
            mode_ = fileinfo.docinfo(filename).mode()
        else:
            filename = self.document().url().toLocalFile()
            mode_ = self.mode()
        
            if not filename or self.document().isModified():
                # We need to use a scratchdir to save our contents to
                import scratchdir
                scratch = scratchdir.scratchdir(self.document())
                if create:
                    scratch.saveDocument()
                    if filename and self.lydocinfo().include_args():
                        includepath.append(os.path.dirname(filename))
                    filename = scratch.path()
                elif scratch.path() and os.path.exists(scratch.path()):
                    filename = scratch.path()
        
        return filename, mode_, includepath
    
    def includefiles(self):
        """Returns a set of filenames that are included by the given document.
        
        The document's own filename is not added to the set.
        The configured include path is used to find files.
        Included files are checked recursively, relative to our (master) file,
        relative to the including file, and if that still yields no file, relative
        to the directories in the includepath().
        
        This method uses caching for both the document contents and the other files.
        
        """
        filename = self.master()
        includeargs = None
        if not filename:
            filename = self.document().url().toLocalFile()
            if not filename:
                return set()
            includeargs = self.lydocinfo().include_args()
        files = fileinfo.includefiles(filename, self.includepath(), includeargs)
        return files

    def child_urls(self):
        """Return a tuple of urls included by the Document.
        
        This only returns urls that are referenced directly, not searching
        via an include path. If the Document has no url set, an empty tuple
        is returned. 
        
        """
        url = self.document().url()
        if url.isEmpty():
            return ()
        return tuple(url.resolved(QUrl(arg)) for arg in self.lydocinfo().include_args())
        
    def basenames(self):
        """Returns a list of basenames that our document is expected to create.
        
        The list is created based on include files and the define output-suffix and
        \bookOutputName and \bookOutputSuffix commands.
        You should add '.ext' and/or '-[0-9]+.ext' to find created files.
        
        """
        # if the file defines an 'output' variable, it is used instead
        filename = self.master()
        if filename:
            output = fileinfo.docinfo(filename).variables().get('output')
        else:
            output = variables.get(self.document(), 'output')
        
        filename, mode = self.jobinfo()[:2]
        
        if output:
            dirname = os.path.dirname(filename)
            return [os.path.join(dirname, name.strip())
                    for name in output.split(',')]
        
        if mode == "lilypond":
            return fileinfo.basenames(filename, self.includefiles(), self.lydocinfo().output_args())
        
        elif mode == "html":
            pass
        
        elif mode == "texinfo":
            pass
        
        elif mode == "latex":
            pass
        
        elif mode == "docbook":
            pass
        
        return []


