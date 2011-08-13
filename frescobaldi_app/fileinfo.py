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
Computes and caches various information about files.
"""

from __future__ import unicode_literals

import functools
import itertools
import os

import ly.parse
import ly.lex
import filecache
import util
import variables


def _cache(func):
    """Wraps a function to make it use a FileCache."""
    cache = filecache.FileCache()
    @functools.wraps(func)
    def wrapper(filename):
        try:
            return cache[filename]
        except KeyError:
            result = cache[filename] = func(filename)
            return result
    return wrapper


def textmode(text, guess=True):
    """Returns the type of the given text ('lilypond, 'html', etc.).
    
    Checks the mode variable and guesses otherwise if guess is True.
    
    """
    mode = variables.variables(text).get("mode")
    if mode in ly.lex.modes:
        return mode
    if guess:
        return ly.lex.guessMode(text)


@_cache
def mode(filename):
    """Returns the type of the text in the given filename."""
    with open(filename) as f:
        text = util.decode(f.read())
    return textmode(text)


def tokens(filename):
    """Returns a token stream from the given filename."""
    with open(filename) as f:
        text = util.decode(f.read())
    return ly.lex.state(textmode(text)).tokens(text)


@_cache
def includeargs(filename):
    """Returns the list of arguments of \\include commands in the given file.
    
    The return value is cached until the mtime of the file changes.
    
    """
    return list(ly.parse.includeargs(tokens(filename)))


def includefiles(filename, include_path=[], initial_args=None):
    """Returns a set of filenames that are included by the given pathname.
        
    The specified include path is used to find files.
    The filename is NOT itself added to the set.
    Included files are checked recursively, relative to our (master) file,
    relative to the including file, and if that still yields no file, relative
    to the directories in the include_path.
    
    If initial_args is given, the filename itself is not scanned for include_args.
    
    """
    files = set()
    
    def tryarg(directory, arg):
        path = os.path.join(directory, arg)
        if os.path.exists(path) and path not in files:
            files.add(path)
            args = includeargs(path)
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
    
    if initial_args is None:
        initial_args = includeargs(filename)
    basedir = os.path.dirname(filename)
    find(initial_args, basedir)
    return files


@_cache
def outputargs(filename):
    """Returns the list of arguments of \\bookOutputName, \\bookOutputSuffix etc. commands.
    
    See outputargs(). The return value is cached until the mtime of the file changes.
    
    """
    return list(ly.parse.outputargs(tokens(filename)))


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
    includes.discard(filename)
    
    if initial_outputargs is None:
        initial_outputargs = outputargs(filename)
    
    def args():
        yield initial_outputargs
        for filename in includes:
            yield outputargs(filename)
                
    for type, arg in itertools.chain.from_iterable(args()):
        if type == "suffix":
            arg = basename + '-' + arg
        path = os.path.normpath(os.path.join(dirname, arg))
        if path not in basenames:
            basenames.append(path)
    return basenames

@_cache
def version(filename):
    """Returns the LilyPond version if set in the file, as a tuple of ints.
    
    First the function searches inside LilyPond syntax.
    Then it looks at the 'version' document variable.
    Then, if the document is not a LilyPond document, it simply searches for a
    \\version command string, possibly embedded in a comment.
    
    The version is cached until the file changes.
    
    """
    mkver = lambda strings: tuple(map(int, strings))
    with open(filename) as f:
        text = util.decode(f.read())
    mode = textmode(text)
    tokens_ = list(ly.lex.state(mode).tokens(text))

    version = ly.parse.version(tokens_)
    if version:
        return mkver(re.findall(r"\d+", version))
    # look at document variables
    version = variables.variables(text).get("version")
    if version:
        return mkver(re.findall(r"\d+", version))
    # parse whole document for non-lilypond comments
    if mode != "lilypond":
        m = re.search(r'\\version\s*"(\d+\.\d+(\.\d+)*)"', text)
        if m:
            return mkver(m.group(1).split('.'))

