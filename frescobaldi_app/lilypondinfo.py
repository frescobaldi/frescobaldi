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
Settings stuff and handling for different LilyPond versions.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import QSettings

import ly.info
import app


_infos = None   # this can hold a list of configured LilyPondInfo instances


def infos():
    """Returns all configured LilyPondInfo for the different used LilyPond versions."""
    global _infos
    if _infos is None:
        s = QSettings()
        _infos = []
        for i in range(s.beginReadArray("lilypondinfo")):
            s.setArrayIndex(i)
            info = LilyPondInfo.read(s)
            if info:
                _infos.append(info)
        s.endArray()
        app.aboutToQuit.connect(saveinfos)
    return _infos


def setinfos(infos):
    """Sets the info's to the given list of LilyPondInfo instances."""
    global _infos
    _infos = infos
    

def saveinfos():
    """Saves the info's."""
    s = QSettings()
    s.beginWriteArray("lilypondinfo")
    for i, info in enumerate(infos()):
        s.setArrayIndex(i)
        info.write(s)
    s.endArray()


def default():
    """Returns a default LilyPondInfo instance with the default LilyPond command.
    
    On Windows, the default command is "lilypond-windows.exe",
    on other platforms simply "lilypond".
    
    """
    lilypond = "lilypond-windows.exe" if os.name == "nt" else "lilypond"
    return LilyPondInfo(lilypond)


def preferred():
    """Returns the preferred (user set default) LilyPondInfo instance."""
    infos_ = infos()
    if not infos_:
        return default()
    elif len(infos_) == 1:
        return infos_[0]
    s = QSettings()
    s.beginGroup("lilypond_settings")
    # find default version
    defaultCommand = "lilypond-windows.exe" if os.name == "nt" else "lilypond"
    userDefault = s.value("default", defaultCommand)
    if userDefault != defaultCommand:
        for info in infos_:
            if info.command == userDefault:
                return info
    for info in infos_:
        if info.command == defaultCommand:
            return info
    return infos_[0]


def suitable(version):
    """Returns a LilyPondInfo with a suitable version if found, else returns preferred()."""
    for i in sorted(infos(), key=lambda i: i.version):
        if i.version >= version:
            return i
    return preferred()
 

class LilyPondInfo(ly.info.LilyPondInfo):
    """Manages information about a LilyPond instance, partially cached to speed up Frescobaldi."""
    def __init__(self, command):
        super(LilyPondInfo, self).__init__(command)
        self.auto = True
        self.lilypond_book = 'lilypond-book'
        self.convert_ly = 'convert-ly'
    
    @classmethod
    def read(cls, settings):
        """Returns a new LilyPondInfo instance, filled from a QSettings instance.
        
        May return None, if the command is not existing.
        
        """
        cmd = settings.value("command", "")
        if cmd:
            info = cls(cmd)
            if info.abscommand:
                info.auto = settings.value("auto", True) in (True, "true")
                info.lilypond_book = settings.value("lilypond-book", "lilypond-book")
                info.convert_ly = settings.value("convert-ly", "convert-ly")
                if int(os.path.getmtime(info.abscommand)) == int(float(settings.value("mtime", 0))):
                    info.versionString = settings.value("version")
                    datadir = settings.value("datadir")
                    if datadir and os.path.isdir(datadir):
                        info.datadir = settings.value("datadir")
                return info
    
    def write(self, settings):
        """Writes ourselves to a QSettings instance. We should be valid."""
        settings.setValue("command", self.command)
        settings.setValue("version", self.versionString)
        settings.setValue("datadir", self.datadir)
        if self.abscommand:
            settings.setValue("mtime", int(os.path.getmtime(self.abscommand)))
        settings.setValue("auto", self.auto)
        settings.setValue("lilypond-book", self.lilypond_book)
        settings.setValue("convert-ly", self.convert_ly)


