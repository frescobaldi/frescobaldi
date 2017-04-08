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
Computes and caches various information about files.
"""


import itertools
import re
import os
import atexit

import ly.document
import lydocinfo
import ly.lex
import filecache
import util
import variables


_document_cache = filecache.FileCache()
_suffix_chars_re = re.compile(r'[^-\w]', re.UNICODE)


### XXX otherwise I get a segfault on shutdown when very large music trees
### are made (and every node references the document).
### (The segfault is preceded by a "corrupted double-linked list" message.)
atexit.register(_document_cache.clear)


class _CachedDocument(object):
    """Contains a document and related items."""
    filename = None
    document = None
    variables = None
    docinfo = None
    music = None


def _cached(filename):
    """Return a _CachedDocument instance for the filename, else creates one."""
    filename = os.path.realpath(filename)
    try:
        c = _document_cache[filename]
    except KeyError:
        with open(filename, 'rb') as f:
            text = util.decode(f.read())
        c = _document_cache[filename] = _CachedDocument()
        c.variables = v = variables.variables(text)
        c.document = ly.document.Document(text, v.get("mode"))
        c.filename = c.document.filename = filename
    return c


def document(filename):
    """Return a (cached) ly.document.Document for the filename."""
    return _cached(filename).document


def docinfo(filename):
    """Return a (cached) LyDocInfo instance for the specified file."""
    c = _cached(filename)
    if c.docinfo is None:
        c.docinfo = lydocinfo.DocInfo(c.document, c.variables)
    return c.docinfo


def music(filename):
    """Return a (cached) music.Document instance for the specified file."""
    c = _cached(filename)
    if c.music is None:
        import music
        c.music = music.Document(c.document)
    return c.music


def textmode(text, guess=True):
    """Returns the type of the given text ('lilypond, 'html', etc.).

    Checks the mode variable and guesses otherwise if guess is True.

    """
    mode = variables.variables(text).get("mode")
    if mode in ly.lex.modes:
        return mode
    if guess:
        return ly.lex.guessMode(text)


def includefiles(dinfo, include_path=()):
    """Returns a set of filenames that are included by the DocInfo's document.

    The specified include path is used to find files. The own filename
    is NOT added to the set. Included files are checked recursively,
    relative to our file, relative to the including file, and if that
    still yields no file, relative to the directories in the include_path.

    If the document has no local filename, only the include_path is
    searched for files.

    """
    filename = dinfo.document.filename
    basedir = os.path.dirname(filename) if filename else None
    files = set()

    def tryarg(directory, arg):
        path = os.path.realpath(os.path.join(directory, arg))
        if path not in files and os.path.isfile(path):
            files.add(path)
            args = docinfo(path).include_args()
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

    find(dinfo.include_args(), basedir)
    return files


def basenames(dinfo, includefiles=(), filename=None, replace_suffix=True):
    """Returns the list of basenames a document is expected to create.

    The list is created based on includefiles and the define output-suffix and
    \bookOutputName and \bookOutputSuffix commands.
    You should add '.ext' and/or '-[0-9]+.ext' to find created files.

    If filename is given, it is regarded as the filename LilyPond is run on.
    Otherwise, the filename of the info's document is read.

    If replace_suffix is True (the default), special characters and spaces
    in the suffix are replaced with underscores (in the same way as LilyPond
    does it), using the replace_suffix_chars() function.

    """
    basenames = []
    basepath = os.path.splitext(filename or dinfo.document.filename)[0]
    dirname, basename = os.path.split(basepath)

    if basepath:
        basenames.append(basepath)

    def args():
        yield dinfo.output_args()
        for filename in includefiles:
            yield docinfo(filename).output_args()

    for type, arg in itertools.chain.from_iterable(args()):
        if type == "suffix":
            if replace_suffix:
                # LilyPond (lily-library.scm:223) does this, too
                arg = replace_suffix_chars(arg)
            arg = basename + '-' + arg
        path = os.path.normpath(os.path.join(dirname, arg))
        if path not in basenames:
            basenames.append(path)
    return basenames


def replace_suffix_chars(s):
    """Replace spaces and most non-alphanumeric characters with underscores.

    This is used to mimic the behaviour of LilyPond, which also does this,
    for the output-suffix. (See scm/lily-library.scm:223.)

    """
    return _suffix_chars_re.sub('_', s)


