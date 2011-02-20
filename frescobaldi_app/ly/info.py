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


class LilyPondInfo(object):
    """Encapsulates information about a runnable LilyPond instance.
    
    You should instantiate a LilyPondInfo object with the command
    you would give when running LilyPond, either 'lilypond' or a full path.
    
    If no full path is given, the executable is searched for in the system's PATH.
    
    """
    def __init__(self, command):
        """The path should point to an existing, executable LilyPond instance."""
        self._command = command
    
    @property
    def command(self):
        """Returns the command given at instantiation."""
        return self._command
        
    @util.cachedproperty
    def abscommand(self):
        """Returns the full absolute path of our LilyPond command.
        
        May return None if LilyPond is not found.
        
        """
        return util.findexe(self._command)

    @util.cachedproperty
    def versionString(self):
        """Returns the version of this LilyPond instance as a string."""
        if self.abscommand:
            try:
                output = subprocess.Popen(
                    (self.abscommand, '-v'),
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
        if self.abscommand:
            return os.path.dirname(self.abscommand)
    
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
        if self.abscommand:
            # First ask LilyPond itself.
            try:
                d = subprocess.Popen((self.abscommand, '-e',
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

