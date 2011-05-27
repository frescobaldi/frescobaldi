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
import ly.parse
import app
import fileinfo
import tokeniter
import plugin
import variables


__all__ = ['info', 'mode']


def info(document):
    """Returns a DocumentInfo instance for the given Document."""
    return DocumentInfo.instance(document)


def mode(document, guess=True):
    """Returns the type of the given document. See DocumentInfo.mode()."""
    return info(document).mode(guess)


def resetoncontentschanged(func):
    """Caches a value until the document emits the contentsChanged signal.
    
    Use this to decorate methods of the DocumentInfo class.
    
    """
    _cache = weakref.WeakKeyDictionary()
    @functools.wraps(func)
    def wrapper(self):
        try:
            return _cache[self]
        except KeyError:
            def reset(selfref=weakref.ref(self)):
                self = selfref()
                if self:
                    del _cache[self]
                    self.document().contentsChanged.disconnect(reset)
            result = _cache[self] = func(self)
            self.document().contentsChanged.connect(reset)
            return result
    return wrapper


class DocumentInfo(plugin.DocumentPlugin):
    """Computes and caches various information about a Document."""
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
            return ly.lex.guessMode(self.document().toPlainText())
    
    def tokens(self):
        """Iterates over all the tokens in a document, parsing if the document has not yet materialized."""
        if self.document().firstBlock().userState() != -1:
            return tokeniter.allTokens(self.document())
        else:
            return ly.lex.state(self.mode()).tokens(self.document().toPlainText())

    @resetoncontentschanged
    def version(self):
        """Returns the LilyPond version if set in the document, as a tuple of ints.
        
        First the functions searches inside LilyPond syntax.
        Then it looks at the 'version' document variable.
        Then, if the document is not a LilyPond document, it simply searches for a
        \\version command string, possibly embedded in a comment.
        
        The version is cached until the documents contents change.
        
        """
        mkver = lambda strings: tuple(map(int, strings))
        
        version = ly.parse.version(self.tokens())
        if version:
            return mkver(re.findall(r"\d+", version))
        # look at document variables
        version = variables.get(self.document(), "version")
        if version:
            return mkver(re.findall(r"\d+", version))
        # parse whole document for non-lilypond documents
        if self.mode() != "lilypond":
            m = re.search(r'\\version\s*"(\d+\.\d+(\.\d+)*)"', self.document().toPlainText())
            if m:
                return mkver(m.group(1).split('.'))
    
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
        return QSettings().value("lilypond_settings/include_path", []) or []
        
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
            mode_ = fileinfo.mode(filename)
        else:
            filename = self.document().url().toLocalFile()
            mode_ = self.mode()
        
            if not filename or self.document().isModified():
                # We need to use a scratchdir to save our contents to
                import scratchdir
                scratch = scratchdir.scratchdir(self.document())
                if create:
                    scratch.saveDocument()
                    if filename and self.includeargs():
                        includepath.append(os.path.dirname(filename))
                    filename = scratch.path()
                elif scratch.path() and os.path.exists(scratch.path()):
                    filename = scratch.path()
        
        return filename, mode_, includepath
    
    @resetoncontentschanged
    def includeargs(self):
        """Returns a list of \\include arguments in our document.
        
        See ly.parse.includeargs().
        
        """
        return list(ly.parse.includeargs(self.tokens()))

    def includefiles(self):
        """Returns a set of filenames that are included by the given document.
        
        The document's own filename is also added to the set.
        The configured include path is used to find files.
        Included files are checked recursively, relative to our (master) file,
        relative to the including file, and if that still yields no file, relative
        to the directories in the includepath().
        
        This method uses caching for both the document contents and the other files.
        
        """
        files = set()
        ipath = self.includepath()
        
        def tryarg(directory, arg):
            path = os.path.join(directory, arg)
            if os.path.exists(path) and path not in files:
                files.add(path)
                args = fileinfo.includeargs(path)
                find(args, os.path.dirname(path))
                return True
                
        def find(incl_args, directory):
            for arg in incl_args:
                # new, recursive, relative include
                if not (directory and tryarg(directory, arg)):
                    # old include (relative to master file)
                    if not (basedir and tryarg(basedir, arg)):
                        # if path is given, also search there:
                        for p in ipath:
                            if tryarg(p, arg):
                                break
                    
        filename = self.master()
        if filename:
            incl_args = fileinfo.includeargs(filename)
        else:
            filename = self.document().url().toLocalFile()
            if filename:
                incl_args = self.includeargs()
        if filename:
            files.add(filename)
            basedir = os.path.dirname(filename)
            find(incl_args, basedir)
        return files

    @resetoncontentschanged
    def outputargs(self):
        """Returns a list of output arguments in our document.
        
        See ly.parse.outputargs().
        
        """
        return list(ly.parse.outputargs(self.tokens()))
        
    def basenames(self):
        """Returns a list of basenames that our document is expected to create.
        
        The list is created based on include files and the define output-suffix and
        \bookOutputName and \bookOutputSuffix commands.
        You should add '.ext' and/or '-[0-9]+.ext' to find created files.
        
        """
        basenames = []
        filename, mode = self.jobinfo()[:2]
        basepath = os.path.splitext(filename)[0]
        dirname, basename = os.path.split(basepath)
        
        if mode == "lilypond":
            includes = self.includefiles()
            if basepath:
                basenames.append(basepath)
                
            def args():
                if not self.master():
                    includes.discard(self.document().url().toLocalFile())
                    yield self.outputargs()
                for filename in includes:
                    yield fileinfo.outputargs(filename)
                        
            for type, arg in itertools.chain.from_iterable(args()):
                if type == "suffix":
                    arg = basename + '-' + arg
                path = os.path.normpath(os.path.join(dirname, arg))
                if path not in basenames:
                    basenames.append(path)
        
        elif mode == "html":
            pass
        
        elif mode == "texinfo":
            pass
        
        elif mode == "latex":
            pass
        
        elif mode == "docbook":
            pass
        
        return basenames


