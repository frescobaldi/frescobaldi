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

import ly.lex.lilypond
import ly.parse
import ly.pitch
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
        
        version = ly.parse.version(tokeniter.all_tokens(self.document()))
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
    
    def versionString(self):
        """Returns the version of the document as a string, or an empty string."""
        return '.'.join(map(str, self.version() or ()))
    
    @resetoncontentschanged
    def pitchLanguage(self):
        """Returns the pitchname language used in the document, if defined."""
        languages = ly.pitch.pitchInfo.keys()
        for block in cursortools.all_blocks(self.document()):
            tokens = tokeniter.tokens(block)
            try:
                i = tokens.index('\\language')
            except ValueError:
                try:
                    i = tokens.index('\\include')
                except ValueError:
                    continue
            if isinstance(tokens[i], ly.lex.lilypond.Keyword):
                for t in tokens[i+1:]:
                    if isinstance(t, ly.lex.Space):
                        continue
                    elif t == '"':
                        continue
                    lang = t[:-3] if t.endswith('.ly') else t[:]
                    if lang in languages:
                        return lang
    
    @resetoncontentschanged
    def globalStaffSize(self, default=20):
        """Returns the global staff size, if set, else the default value."""
        for block in cursortools.all_blocks(self.document()):
            tokens = tokeniter.tokens(block)
            try:
                i = tokens.index('set-global-staff-size')
            except ValueError:
                continue
            try:
                return int(tokens[i+2], 10)
            except (IndexError, ValueError):
                pass
        return default
    
    @resetoncontentschanged
    def looksComplete(self):
        """Return True when the document looks couplete and could be valid.
        
        This is determined by looking at the depth of the state at the end of
        the last line: if it is 1 it could be a valid document.
        
        """
        return tokeniter.state_end(self.document().lastBlock()).depth() == 1
    
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
            mode_ = fileinfo.FileInfo.info(filename).mode()
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
        return list(ly.parse.includeargs(tokeniter.all_tokens(self.document())))

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
            includeargs = self.includeargs()
        files = fileinfo.includefiles(filename, self.includepath(), includeargs)
        return files

    @resetoncontentschanged
    def outputargs(self):
        """Returns a list of output arguments in our document.
        
        See ly.parse.outputargs().
        
        """
        return list(ly.parse.outputargs(tokeniter.all_tokens(self.document())))
        
    def basenames(self):
        """Returns a list of basenames that our document is expected to create.
        
        The list is created based on include files and the define output-suffix and
        \bookOutputName and \bookOutputSuffix commands.
        You should add '.ext' and/or '-[0-9]+.ext' to find created files.
        
        """
        # if the file defines an 'output' variable, it is used instead
        filename = self.master()
        if filename:
            output = fileinfo.FileInfo.info(filename).variables().get('output')
        else:
            output = variables.get(self.document(), 'output')
        
        filename, mode = self.jobinfo()[:2]
        
        if output:
            dirname = os.path.dirname(filename)
            return [os.path.join(dirname, name.strip())
                    for name in output.split(',')]
        
        if mode == "lilypond":
            return fileinfo.basenames(filename, self.includefiles(), self.outputargs())
        
        elif mode == "html":
            pass
        
        elif mode == "texinfo":
            pass
        
        elif mode == "latex":
            pass
        
        elif mode == "docbook":
            pass
        
        return []


