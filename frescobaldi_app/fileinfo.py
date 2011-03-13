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
Computes and caches various information about files.
"""

import ly.parse
import ly.tokenize
import filecache
import util
import variables


_include_args_cache = filecache.FileCache()
_output_args_cache = filecache.FileCache()
_mode_cache = filecache.FileCache()


def textmode(text, guess=True):
    """Returns the type of the given text ('lilypond, 'html', etc.).
    
    Checks the mode variable and guesses otherwise if guess is True.
    
    """
    mode = variables.variables(text).get("mode")
    if mode in ly.tokenize.modes:
        return mode
    if guess:
        return ly.tokenize.guessMode(text)


def mode(filename):
    """Returns the type of the text in the given filename."""
    try:
        return _mode_cache[filename]
    except KeyError:
        with open(filename) as f:
            text = util.decode(f.read())
        mode = _mode_cache[filename] = textmode(text)
        return mode


def tokens(filename):
    """Returns a token stream from the given filename."""
    with open(filename) as f:
        text = util.decode(f.read())
    return ly.tokenize.state(textmode(text)).tokens(text)


def includeargs(filename):
    """Returns the list of arguments of \\include commands in the given file.
    
    The return value is cached until the mtime of the file changes.
    
    """
    try:
        return _include_args_cache[filename]
    except KeyError:
        result = _include_args_cache[filename] = list(ly.parse.includeargs(tokens(filename)))
        return result
        

def outputargs(filename):
    """Returns the list of arguments of \\bookOutputName, \\bookOutputSuffix etc. commands.
    
    See outputargs(). The return value is cached until the mtime of the file changes.
    
    """
    try:
        return _output_args_cache[filename]
    except KeyError:
        result = _output_args_cache[filename] = list(ly.parse.outputargs(tokens(filename)))
        return result


