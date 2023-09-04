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
Settings stuff and handling for different LilyPond versions.
"""


import glob
import codecs
import os
import pathlib
import platform
import re
import shutil

from PyQt5.QtCore import QEventLoop, QSettings, QStandardPaths, QTimer
from PyQt5.QtWidgets import QProgressDialog

import app
import cachedproperty
import job
import job.queue
import util
import qutil

if platform.system() == "Darwin":
    import macosx

_infos = None   # this can hold a list of configured LilyPondInfo instances

LILYPOND_AUTOINSTALL_DIR = (
    os.path.join(QStandardPaths.writableLocation(QStandardPaths.DataLocation),
                 "lilypond-binaries")
)
# According to the Qt documentation, the location may need to be created.
pathlib.Path(LILYPOND_AUTOINSTALL_DIR).mkdir(parents=True, exist_ok=True)

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
        if not _infos:
            info = default()
            if info.abscommand():
                _infos.append(info)
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
    lilypond = "lilypond-windows.exe" if platform.system() == "Windows" else "lilypond"
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
    defaultCommand = "lilypond-windows.exe" if platform.system() == "Windows" else "lilypond"
    userDefault = s.value("default", defaultCommand, str)
    if userDefault != defaultCommand:
        for info in infos_:
            if info.command == userDefault:
                return info
    for info in infos_:
        if info.command == defaultCommand:
            return info
    return infos_[0]


def suitable(version):
    """Return a LilyPondInfo with a suitable version if found.

    Otherwise the most recent LilyPond version is returned.

    """
    infos_ = [i for i in infos() if i.autoVersionIncluded]
    if infos_:
        infos_.sort(key=lambda i: i.version())
        for i in infos_:
            if i.version() >= version:
                return i
        return i # return the latest anyway
    return preferred()


class CachedProperty(cachedproperty.CachedProperty):
    def wait(self, msg=None, timeout=0):
        """Returns the value for the property, waiting for it to be computed.

        If this lasts longer than 2 seconds, a progress dialog is displayed.

        """
        if self.get() is None:
            self.start()
            if self.get() is None:
                if msg is None:
                    msg = _("Running LilyPond, this can take some time...")
                qutil.waitForSignal(self.computed, msg, timeout)
        return self.get()

    __call__ = wait


class LilyPondInfo:
    ly_tool_names = (
        'lilypond-book',
        'convert-ly',
        'musicxml2ly',
        'midi2ly',
        'abc2ly',
    )

    def __init__(self, command):
        self._command = command
        self.autoVersionIncluded = True
        self.name = "LilyPond"
        self._lytools = {}

    @property
    def command(self):
        return self._command

    @CachedProperty.cachedproperty
    def abscommand(self):
        """The absolute path of the command."""
        if platform.system() == "Windows":
            # on Windows, newer versions of LilyPond don't add themselves to the
            # PATH, so add a probable path here
            path = glob.glob(os.path.join(
                os.environ.get('ProgramFiles', 'C:\\Program Files'),
                'LilyPond*', 'usr', 'bin'))
        elif platform.system() == "Darwin":
            # also on Mac OS X, LilyPond is not automatically added to the PATH
            path = [
                os.path.join('/Applications', 'LilyPond.app', 'Contents', 'Resources', 'bin'),
                os.path.join('/opt', 'local', 'bin'),
                os.path.join('/opt', 'lilypond', 'bin'),
                # Default path for Homebrew on MacOS arm64.
                '/opt/homebrew/bin',
                # Default path for Homebrew on MacOS x86_64.
                '/usr/local/bin',
            ]
            if macosx.inside_app_bundle():
                # By default, the PATH environment variable for app bundles
                # does not contain the path which is required for lilypond
                # and other helper programs like gs.
                # Add the lilypond path to PATH to find the helper programs
                # for Homebrew, Macports and other local installations.
                exe = util.findexe(self.command, path)
                if exe:
                    bindir = os.path.dirname(exe)
                    os.environ['PATH'] = bindir + ':' + os.environ['PATH']
        else:
            path = None
        return util.findexe(self.command, path) or False

    #NOTE/TODO:
    # This has only been tested for downloaded and self-compiled releases on Linux so far
    @CachedProperty.cachedproperty(depends=abscommand)
    def libdir(self):
        exe = self.abscommand()
        if exe:
            parent = os.path.dirname(os.path.dirname(exe))
            return os.path.join(parent, 'lib')
        else:
            return False

    @CachedProperty.cachedproperty(depends=abscommand)
    def displaycommand(self):
        """The path to the command in a format pretty to display.

        This removes the 'out/bin/lilypond' part of custom build LilyPond
        versions, and on Mac OS X it removes the
        '/Contents/Resources/bin/lilypond' part.

        Finally it replaces the users home directory with '~'.

        The empty string is returned if LilyPond is not installed on the users'
        system.
        """
        command = self.abscommand()
        if command:
            outstrip='out/bin/lilypond'
            if command.endswith(outstrip):
                command=command[:-len(outstrip)]
            macstrip='/Contents/Resources/bin/lilypond'
            if platform.system() == "Darwin" and command.endswith('.app' + macstrip):
                command=command[:-len(macstrip)]
            return util.homify(command)
        else:
            return self.command

    @CachedProperty.cachedproperty(depends=abscommand)
    def versionString(self):
        if not self.abscommand():
            return ""

        j = job.Job([self.abscommand(), '--version'])

        @j.done.connect
        def done():
            success = j.success
            if success:
                output = ' '.join([line[0] for line in j.history()])
                m = re.search(r"\d+\.\d+(.\d+)?", output)
                self.versionString = m.group() if m else ""
            else:
                self.versionString = ""

        app.job_queue().add_job(j, 'generic')

    @CachedProperty.cachedproperty(depends=versionString)
    def version(self):
        if self.versionString():
            return tuple(map(int, self.versionString().split('.')))
        return ()

    @CachedProperty.cachedproperty(depends=abscommand)
    def bindir(self):
        """Returns the directory the LilyPond command is in."""
        if self.abscommand():
            return os.path.dirname(self.abscommand())
        return False

    @CachedProperty.cachedproperty(depends=bindir)
    def prefix(self):
        """Returns the prefix LilyPond was installed to."""
        if self.bindir():
            return os.path.dirname(self.bindir())
        return False

    @CachedProperty.cachedproperty(depends=(prefix, versionString))
    def datadir(self):
        """Returns the datadir of this LilyPond instance.

        Most times this is something like "/usr/share/lilypond/2.13.3/"
        If this method returns False, the datadir could not be determined.

        """
        if not self.abscommand():
            return False

        # First ask LilyPond itself.
        j = job.Job([self.abscommand(), '-e',
            "(display (ly:get-option 'datadir)) (newline) (exit)"])
        @j.done.connect
        def done():
            success = j.success
            if success:
                output = [line[0] for line in j.history()]
                d = output[1].strip('\n')
                if os.path.isabs(d) and os.path.isdir(d):
                    self.datadir = d
                    return

            # Then find out via the prefix.
            if self.prefix():
                dirs = ['current']
                if self.versionString():
                    dirs.append(self.versionString())
                for suffix in dirs:
                    d = os.path.join(self.prefix(), 'share', 'lilypond', suffix)
                    if os.path.isdir(d):
                        self.datadir = d
                        return
            self.datadir = False
        app.job_queue().add_job(j, 'generic')

    def toolcommand(self, original_command, use_ly_tool=True):
        """Return a list containing the commandline to run a tool, e.g. convert-ly.

        On Unix (including macOS), the list has one element: the full path to the tool.

        On Windows, the list has two elements: the LilyPond-provided Python
        interpreter and the tool path.

        If use_ly_tool is True, this takes into account the command the user
        might have configured for the tool, using ly_tool() to get that command
        name first.

        """
        if use_ly_tool:
            command = self.ly_tool(original_command)
        else:
            command = original_command

        bindir = self.bindir()
        if bindir:
            toolpath = os.path.join(self.bindir(), command)
        else:
            toolpath = command

        # on Windows the tool command is not directly executable, but
        # must be started using the LilyPond-provided Python interpreter
        if platform.system() == "Windows":
            if not os.access(toolpath, os.R_OK) and not toolpath.endswith('.py'):
                toolpath += '.py'
            command = [self.python(), toolpath]
        else:
            command = [toolpath]
        return command

    @property
    def isAutoManaged(self):
        """Return true if the LilyPond installation was auto-installed by Frescobaldi."""
        command_path = pathlib.Path(self.command)
        autoinstall_path = pathlib.Path(LILYPOND_AUTOINSTALL_DIR)
        #return command_path.is_relative_to(autoinstall_path) # Python 3.9+
        return autoinstall_path in command_path.parents

    def forget(self):
        """If this is an auto-managed installation, then wipe it from the file system."""
        if self.isAutoManaged:
            shutil.rmtree(self.prefix())

    @CachedProperty.cachedproperty(depends=versionString)
    def prettyName(self):
        """Return a pretty-printable name for this LilyPond instance."""
        # Don't show the internal path for auto-managed installations
        if self.isAutoManaged:
            return "{name} {version}".format(name=self.name,
                                             version=self.versionString())
        else:
            return "{name} {version} ({command})".format(
                name = self.name,
                version = self.versionString(),
                command = self.displaycommand())

    def ly_tool(self, name):
        """Get the configured command for the ly tool (e.g. midi2ly).

        By default this is just the name itself, relative to the directory
        the LilyPond executable is in.

        """
        return self._lytools.get(name, name)

    def set_ly_tool(self, name, value):
        """Set the command for the named ly tool (e.g. midi2ly).

        By default this is just the name itself, relative to the directory
        the LilyPond executable is in.

        """
        self._lytools[name] = value

    @classmethod
    def read(cls, settings):
        """Returns a new LilyPondInfo instance, filled from a QSettings instance.

        May return None, if the command is not existing.

        """
        cmd = settings.value("command", "", str)
        if cmd:
            info = cls(cmd)
            if info.abscommand.wait():
                info.autoVersionIncluded = settings.value("auto", True, bool)
                info.name = settings.value("name", "LilyPond", str)
                for name in cls.ly_tool_names:
                    info.set_ly_tool(name, settings.value(name, name, str))
                if int(os.path.getmtime(info.abscommand())) == int(settings.value("mtime", 0, float)):
                    info.versionString = settings.value("version", "", str)
                    datadir = settings.value("datadir", "", str)
                    if datadir and os.path.isdir(datadir):
                        info.datadir = datadir
                return info

    def write(self, settings):
        """Writes ourselves to a QSettings instance. We should be valid."""
        settings.setValue("command", self.command)
        settings.setValue("version", self.versionString())
        settings.setValue("datadir", self.datadir() or "")
        if self.abscommand():
            settings.setValue("mtime", int(os.path.getmtime(self.abscommand())))
        settings.setValue("auto", self.autoVersionIncluded)
        settings.setValue("name", self.name)
        for name in self.ly_tool_names:
            value = self._lytools.get(name, name)
            if name == value:
                settings.remove(name)
            else:
                settings.setValue(name, value)

    def python(self):
        """Returns the path to the LilyPond-provided Python interpreter.

        This is only used on Windows, where tools like convert-ly can't be
        run directly.

        """
        if self.bindir():
            for python in ('python-windows.exe', 'pythonw.exe', 'python.exe'):
                interpreter = os.path.join(self.bindir(), python)
                if os.access(interpreter, os.X_OK):
                    return interpreter
        return 'pythonw.exe'
