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


__all__ = ['docinfo', 'info', 'mode']


def info(document):
    """Returns a DocumentInfo instance for the given Document."""
    return DocumentInfo.instance(document)


def docinfo(document):
    """Return a LyDocInfo instance for the document."""
    return info(document).lydocinfo()


def music(document):
    """Return a music.Document instance for the document."""
    return info(document).music()


def mode(document, guess=True):
    """Returns the type of the given document. See DocumentInfo.mode()."""
    return info(document).mode(guess)

    
class DocumentInfo(plugin.DocumentPlugin):
    """Computes and caches various information about a Document."""
    def __init__(self, document):
        document.contentsChanged.connect(self._reset)
        document.closed.connect(self._reset)
        self._reset()
        
    def _reset(self):
        """Called when the document is changed."""
        self._lydocinfo = None
        self._music = None
    
    def lydocinfo(self):
        """Return the lydocinfo instance for our document."""
        if self._lydocinfo is None:
            doc = lydocument.Document(self.document())
            v = variables.manager(self.document()).variables()
            self._lydocinfo = lydocinfo.DocInfo(doc, v)
        return self._lydocinfo
    
    def music(self):
        """Return the music.Document instance for our document."""
        if self._music is None:
            import music
            doc = lydocument.Document(self.document())
            self._music = music.Document(doc)
        self._music.include_path = self.includepath()
        return self._music
    
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
    
    def includepath(self):
        """Returns the configured include path. Currently the document does not matter."""
        try:
            include_path = QSettings().value("lilypond_settings/include_path", [], type(""))
        except TypeError:
            include_path = []
        return include_path
        
    def jobinfo(self, create=False):
        """Returns a two-tuple(filename, includepath).
        
        The filename is the file LilyPond shall be run on. This can be the 
        original filename of the document (if it has a filename and is not 
        modified), but also the filename of a temporarily saved copy of the 
        document.
        
        The includepath is the same as self.includepath(), but with the 
        directory of the original file prepended, only if a temporary 
        'scratchdir'-area is used and the document does include other files 
        (and therefore the original folder should be given in the include 
        path to LilyPond).
        
        """
        includepath = self.includepath()
        filename = self.document().url().toLocalFile()
        
        # Determine the filename to run the engraving job on
        if not filename or self.document().isModified():
            # We need to use a scratchdir to save our contents to
            import scratchdir
            scratch = scratchdir.scratchdir(self.document())
            if create:
                scratch.saveDocument()
            if filename and self.lydocinfo().include_args():
                includepath.insert(0, os.path.dirname(filename))
            if create or (scratch.path() and os.path.exists(scratch.path())):
                filename = scratch.path()
        return filename, includepath
    
    def includefiles(self):
        """Returns a set of filenames that are included by this document.
        
        The document's own filename is not added to the set.
        The configured include path is used to find files.
        Included files are checked recursively, relative to our file,
        relative to the including file, and if that still yields no file, relative
        to the directories in the includepath().
        
        This method uses caching for both the document contents and the other files.
        
        """
        return fileinfo.includefiles(self.lydocinfo(), self.includepath())

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
        output = variables.get(self.document(), 'output')
        filename = self.jobinfo()[0]
        if output:
            dirname = os.path.dirname(filename)
            return [os.path.join(dirname, name.strip())
                    for name in output.split(',')]
        
        mode = self.mode()
        
        if mode == "lilypond":
            return fileinfo.basenames(self.lydocinfo(), self.includefiles(), filename)
        
        elif mode == "html":
            pass
        
        elif mode == "texinfo":
            pass
        
        elif mode == "latex":
            pass
        
        elif mode == "docbook":
            pass
        
        return []


