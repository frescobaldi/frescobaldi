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
Information about LilyPond instances.
"""

import re
import os
import subprocess

from . import util


_cache = {} # this can be changed to another dict-like object using setcache()


__all__ = ['info', 'cache', 'setcache', 'LilyPondInfo']


def info(cmd):
    """Returns a LilyPondInfo object if the path points to a lilypond executable."""
    try:
        info = _cache[cmd]
    except KeyError:
        info = _cache[cmd] = LilyPondInfo(cmd)
    return info


def setcache(obj):
    """Uses obj as the cache.
    
    The object should only have a __getitem__ and __setitem__ method (like a dict)
    It should cache (partially) filled LilyPondInfo instances.
    
    You can use it to cache e.g. the verionString and datadir based on mtime
    of the executable so it's not necessary to really start the LilyPond executable
    to get this information.
    
    """
    global _cache
    _cache = obj
    

def cache():
    """Returns the object used as the cache. By default a dictionary is used."""
    return _cache


class LilyPondInfo(object):
    """Encapsulates information about a runnable LilyPond instance.
    
    You should instantiate a LilyPondInfo object with the command
    you would give when running LilyPond, either 'lilypond' or a full path.
    
    If no full path is given, the executable is searched for in the system's PATH.
    
    """
    def __init__(self, command):
        """The path should point to an existing, executable LilyPond instance."""
        self._command = command
    
    @util.cachedproperty
    def command(self):
        """Returns the full path of our LilyPond command.
        
        May return None if LilyPond is not found.
        
        """
        return util.findexe(self._command)

    @util.cachedproperty
    def versionString(self):
        """Returns the version of this LilyPond instance as a string."""
        if self.command:
            try:
                output = subprocess.Popen(
                    (self.command, '-v'),
                    stdout = subprocess.PIPE, stderr = subprocess.STDOUT).communicate()[0]
            except OSError:
                pass
            else:
                m = re.search(r"\d+\.\d+(.\d+)?", output)
                if m:
                    return m.group()
        return ""
    
    @property
    def version(self):
        """Returns the version as a tuple of ints."""
        return tuple(map(int, self.versionString.split('.')))
    
    @property
    def bindir(self):
        """Returns the directory the LilyPond command is in."""
        if self.command:
            return os.path.dirname(self.command)
    
    @property
    def prefix(self):
        """Returns the prefix LilyPond was installed to."""
        if self.bindir:
            return os.path.dirname(self.bindir)
        
    @util.cachedproperty
    def datadir(self):
        """Returns the datadir of this LilyPond instance.
        
        Most times this is something like "/usr/share/lilypond/2.13.3/"
        If this method returns None, the datadir could not be determined.
        
        """
        if self.command:
            # First ask LilyPond itself.
            try:
                d = subprocess.Popen((self.command, '-e',
                    "(display (ly:get-option 'datadir)) (newline) (exit)"),
                    stdout = subprocess.PIPE).communicate()[0].strip()
                if os.path.isabs(d) and os.path.isdir(d):
                    return d
            except OSError:
                pass
            # Then find out via the prefix.
            version, prefix = self.versionString, self.prefix
            if prefix:
                dirs = ['current']
                if version:
                    dirs.append(version)
                for suffix in dirs:
                    d = os.path.join(prefix, 'share', 'lilypond', suffix)
                    if os.path.isdir(d):
                        return d

