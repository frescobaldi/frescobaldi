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
Computes and caches various information about files.
"""

from __future__ import unicode_literals

import functools
import itertools
import os
import re

import ly.parse
import ly.lex
import filecache
import cachedproperty
import util
import variables


class FileInfo(object):
    """Caches information about files."""
    _cache = filecache.FileCache()
    
    @classmethod
    def info(cls, filename):
        try:
            info = cls._cache[filename]
        except KeyError:
            info = cls._cache[filename] = cls(filename)
        return info
    
    def __init__(self, filename):
        self.filename = filename
        self._tokens = []
        self._tokensource = None
    
    @cachedproperty.cachedproperty
    def text(self):
        """The text of the file (as unicode string)."""
        with open(self.filename) as f:
            return util.decode(f.read())
    
    @cachedproperty.cachedproperty(depends=text)
    def variables(self):
        """A dictionary with variables defined in the text."""
        return variables.variables(self.text())
    
    @cachedproperty.cachedproperty(depends=variables)
    def mode(self):
        """The mode of the text (e.g. 'lilypond', 'html', etc)."""
        mode = self.variables().get("mode")
        if mode in ly.lex.modes:
            return mode
        return ly.lex.guessMode(self.text())
        
    def tokens(self):
        """Generator, yielding the token stream from the file."""
        if self._tokensource is False:
            return iter(self._tokens)
        elif self._tokensource is None:
            self._tokensource = ly.lex.state(self.mode()).tokens(self.text())
        return self._token_iterator()
    
    def _token_iterator(self):
        """(Internal) the caching iterator self.tokens() uses."""
        for i in itertools.count():
            try:
                yield self._tokens[i]
            except IndexError:
                if self._tokensource is False:
                    return
                try:
                    token = next(self._tokensource)
                    self._tokens.append(token)
                    yield token
                except StopIteration:
                    self._tokensource = False
    
    @cachedproperty.cachedproperty(depends=variables)
    def version(self):
        """Returns the LilyPond version if set in the file, as a tuple of ints.
        
        First the function searches inside LilyPond syntax.
        Then it looks at the 'version' document variable.
        Then, if the document is not a LilyPond document, it simply searches for a
        \\version command string, possibly embedded in a comment.
        
        """
        mkver = lambda strings: tuple(map(int, strings))
        version = ly.parse.version(self.tokens())
        if version:
            return mkver(re.findall(r"\d+", version))
        # look at document variables
        version = self.variables().get("version")
        if version:
            return mkver(re.findall(r"\d+", version))
        # parse whole document for non-lilypond comments
        m = re.search(r'\\version\s*"(\d+\.\d+(\.\d+)*)"', self.text())
        if m:
            return mkver(m.group(1).split('.'))

    @cachedproperty.cachedproperty(depends=mode)
    def includeargs(self):
        """The list of arguments of \\include commands in the given file."""
        return list(ly.parse.includeargs(self.tokens()))

    @cachedproperty.cachedproperty(depends=mode)
    def outputargs(self):
        """The list of arguments of \\bookOutputName, \\bookOutputSuffix etc."""
        return list(ly.parse.outputargs(self.tokens()))

    @cachedproperty.cachedproperty(depends=mode)
    def names(self):
        """The list of LilyPond identifiers that the file defines."""
        maybe_name = True
        result = []
        for t in self.tokens():
            if maybe_name and isinstance(t, ly.lex.lilypond.Name):
                result.append(t)
                maybe_name = False
            elif t.isspace():
                if '\n' in t:
                    maybe_name = True
            else:
                maybe_name = False
        return result
    
    @cachedproperty.cachedproperty(depends=mode)
    def markup_commands(self):
        """The list of markup commands the file defines."""
        return list(ly.parse.markup_commands(self.tokens()))


def textmode(text, guess=True):
    """Returns the type of the given text ('lilypond, 'html', etc.).
    
    Checks the mode variable and guesses otherwise if guess is True.
    
    """
    mode = variables.variables(text).get("mode")
    if mode in ly.lex.modes:
        return mode
    if guess:
        return ly.lex.guessMode(text)


def includefiles(filename, include_path=[], initial_args=None):
    """Returns a set of filenames that are included by the given pathname.
        
    The specified include path is used to find files.
    The filename is NOT itself added to the set.
    Included files are checked recursively, relative to our (master) file,
    relative to the including file, and if that still yields no file, relative
    to the directories in the include_path.
    
    If initial_args is given, the filename itself is not scanned for include_args.
    
    If the filename is None, only the include_path is searched for files.
    
    """
    files = set()
    
    def tryarg(directory, arg):
        path = os.path.join(directory, arg)
        if path not in files and os.path.isfile(path):
            files.add(path)
            args = FileInfo.info(path).includeargs()
            find(args, os.path.dirname(path))
            return True
            
    def find(incl_args, directory):
        for arg in incl_args:
            # new, recursive, relative include
            if not (directory and tryarg(directory, arg)):
                # old include (relative to master file)
                if not (basedir and tryarg(basedir, arg)):
                    # if path is given, also search there:
                    for p in include_path:
                        if tryarg(p, arg):
                            break
    
    basedir = os.path.dirname(filename) if filename else None
    if initial_args is None:
        initial_args = FileInfo.info(filename).includeargs() if filename else ()
    find(initial_args, basedir)
    return files


def basenames(filename, includefiles = None, initial_outputargs = None):
    """Returns the list of basenames a document is expected to create.
    
    The list is created based on includefiles and the define output-suffix and
    \bookOutputName and \bookOutputSuffix commands.
    You should add '.ext' and/or '-[0-9]+.ext' to find created files.
    
    """
    basenames = []
    basepath = os.path.splitext(filename)[0]
    dirname, basename = os.path.split(basepath)

    if basepath:
        basenames.append(basepath)
    
    includes = set(includefiles) if includefiles else set()
    
    if initial_outputargs is None:
        initial_outputargs = FileInfo.info(filename).outputargs()
    
    def args():
        yield initial_outputargs
        for filename in includes:
            yield FileInfo.info(filename).outputargs()
                
    for type, arg in itertools.chain.from_iterable(args()):
        if type == "suffix":
            arg = basename + '-' + arg
        path = os.path.normpath(os.path.join(dirname, arg))
        if path not in basenames:
            basenames.append(path)
    return basenames


