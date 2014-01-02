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
Some utility functions.
"""

from __future__ import unicode_literals

import codecs
import glob
import itertools
import os
import re

from PyQt4.QtCore import QDir

import info
import variables


def findexe(cmd, path=None):
    """Checks the PATH for the executable and returns the absolute path or None.
    
    If path (a list or tuple of directory names) is given, it is searched as
    well when the operating system's PATH did not contain the executable.
    
    """
    if os.path.isabs(cmd):
        return cmd if os.access(cmd, os.X_OK) else None
    else:
        ucmd = os.path.expanduser(cmd)
        if os.path.isabs(ucmd):
            return ucmd if os.access(ucmd, os.X_OK) else None
        elif os.sep in cmd and os.access(cmd, os.X_OK):
            return os.path.abspath(cmd)
        else:
            paths = os.environ.get("PATH", os.defpath).split(os.pathsep)
            if path:
                paths = itertools.chain(paths, path)
            for p in paths:
                if os.access(os.path.join(p, cmd), os.X_OK):
                    return os.path.join(p, cmd)


def iswritable(path):
    """Returns True if the path can be written to or created."""
    return ((os.path.exists(path) and os.access(path, os.W_OK))
            or os.access(os.path.dirname(path), os.W_OK))


if os.name == 'nt':
    def equal_paths(p1, p2):
        """Returns True if the paths are equal (case and separator insensitive)."""
        return p1.lower().replace('\\', '/') == p2.lower().replace('\\', '/')
else:
    def equal_paths(p1, p2):
        """Returns True if the paths are equal."""
        return p1 == p2
        

# Make sure that also on Windows, directory slashes remain forward
if os.name == 'nt':
    def normpath(path):
        """A version of os.path.normpath that keeps slashes forward."""
        return os.path.normpath(path).replace('\\', '/')
else:
    normpath = os.path.normpath


def homify(path):
    """Replaces the homedirectory (if present) in the path with a tilde (~)."""
    homedir = QDir.homePath()
    if equal_paths(path[:len(homedir)+1], homedir + '/'):
        path = "~" + path[len(homedir):]
    return path


def tempdir():
    """Returns a temporary directory that is erased on app quit."""
    import tempfile
    global _tempdir
    try:
        _tempdir
    except NameError:
        _tempdir = tempfile.mkdtemp(prefix = info.name +'-')
        import atexit
        @atexit.register
        def remove():
            import shutil
            shutil.rmtree(_tempdir, ignore_errors=True)
    return tempfile.mkdtemp(dir=_tempdir)


def files(basenames, extension = '.*'):
    """Yields filenames with the given basenames matching the given extension."""
    def source():
        for name in basenames:
            name = name.replace('[', '[[]').replace('?', '[?]').replace('*', '[*]')
            if name.endswith(('/', '\\')):
                yield glob.iglob(name + '*' + extension)
            else:
                yield glob.iglob(name + extension)
                yield glob.iglob(name + '-*[0-9]' + extension)
    return sorted(uniq(itertools.chain.from_iterable(source())), key=filenamesort)


def group_files(names, groups):
    """Groups the given filenames by extension.
    
    names: an iterable (or list or tuple) yielding filenames.
    groups: an iterable (or list or tuple) yielding strings.
    
    Each group is a string containing one or more extensions, without period,
    separated by a space. If a filename has one of the extensions in the group,
    the names is added to the list of file for that group.
    An exclamation sign at the beginning of the string negates the match.
    
    Yields the same number of lists as there were group arguments.
    
    """
    allgroups = []
    for group in groups:
        if group.startswith('!'):
            pred = lambda e, ext=group[1:].split(): e not in ext
        else:
            pred = lambda e, ext=group.split(): e in ext
        allgroups.append(([], pred))
    for name in names:
        ext = os.path.splitext(name)[1][1:].lower()
        for files, pred in allgroups:
            if pred(ext):
                files.append(name)
                break
    return (files for files, pred in allgroups)


def naturalsort(text):
    """Returns a key for the list.sort() method.
    
    Intended to sort strings in a human way, for e.g. version numbers.
    
    """
    return tuple(int(s) if s.isdigit() else s for s in re.split(r'(\d+)', text))


def filenamesort(filename):
    """Return a key for sorting filenames."""
    name, ext = os.path.splitext(filename)
    return naturalsort(name), ext


def next_file(filename):
    """Return a similar filename with e.g. "-1" added before the extension.
    
    If there is already a "-n" before the extension, where n is a number,
    the number is increased by one.
    
    """
    name, ext = os.path.splitext(filename)
    try:
        a, b = name.rsplit('-', 1)
        num = int(b)
    except ValueError:
        name += '-1'
    else:
        name = a + '-' + format(num+1)
    return name + ext


def bytes_environ(encoding='latin1'):
    """Return the environment as a dictionary with bytes keys and values.
    
    This can be used for subprocess, as it chokes on Windows on unicode strings
    in Python 2.x.
    
    """
    return dict((s.encode(encoding) if type(s) is not type(b'') else s
                 for s in v) for v in os.environ.items())

    
def uniq(iterable):
    """Returns an iterable, removing duplicates. The items should be hashable."""
    s, l = set(), 0
    for i in iterable:
        s.add(i)
        if len(s) > l:
            yield i
            l = len(s)


def decode(data, encoding=None):
    """Returns the unicode text from the encoded, data. Prefer encoding if given.
    
    The text is also checked for the 'coding' document variable.
    
    """
    encodings = [encoding] if encoding else []
    for bom, encoding in (
        (codecs.BOM_UTF8, 'utf-8'),
        (codecs.BOM_UTF16_LE, 'utf_16_le'),
        (codecs.BOM_UTF16_BE, 'utf_16_be'),
            ):
        if data.startswith(bom):
            encodings.append(encoding)
            data = data[len(bom):]
            break
    else:
        var_coding = variables.variables(data).get("coding")
        if var_coding:
            encodings.append(var_coding)
    encodings.append('utf-8')
    encodings.append('latin1')
    
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except (UnicodeError, LookupError):
            continue
    return data.decode('utf-8', 'replace')


def encode(text, default_encoding='utf-8'):
    """Returns the bytes representing the text, encoded.
    
    Looks at the 'coding' variable to determine the encoding,
    otherwise falls back to the given default encoding, defaulting to 'utf-8'.
    
    """
    encoding = variables.variables(text).get("coding")
    if encoding:
        try:
            return text.encode(encoding)
        except (LookupError, UnicodeError):
            pass
    return text.encode(default_encoding)


