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
The global things in Frescobaldi.
"""

from __future__ import print_function

import os
import sys

from PyQt5.QtCore import QSettings, QThread
from PyQt5.QtWidgets import QApplication

import appinfo

qApp = None                     # instantiate() puts the QApplication obj. here
windows = []
documents = []

from signals import Signal, SignalContext

# signals
appInstantiated  = Signal()     # Called when the QApplication is instantiated
appStarted = Signal()           # Called when the main event loop is entered
aboutToQuit = Signal()          # Use this and not qApp.aboutToQuit
mainwindowCreated = Signal()    # MainWindow
mainwindowClosed = Signal()     # MainWindow
documentCreated = Signal()      # Document
documentUrlChanged = Signal()   # Document
documentLoaded = Signal()       # Document
documentModificationChanged = Signal() # Document
documentClosed = Signal()       # Document
documentSaved = Signal()        # Document
documentSaving = SignalContext() # Document
viewCreated = Signal()          # View
viewSpaceCreated = Signal()     # ViewSpace (see viewmanager.py)
languageChanged = Signal()      # (no arguments)
settingsChanged = Signal()      # (no arguments)
sessionChanged = Signal()       # (name)
saveSessionData = Signal()      # (name)
jobStarted = Signal()           # (Document, Job)
jobFinished = Signal()          # (Document, Job, bool success)


def activeWindow():
    """Return the currently active MainWindow.

    Only returns None if there are no windows at all.

    """
    if windows:
        w = QApplication.activeWindow()
        if w in windows:
            return w
        return windows[0]

def openUrl(url, encoding=None):
    """Returns a Document instance for the given QUrl.

    If there is already a document with that url, it is returned.

    """
    d = findDocument(url)
    if not d:
        # special case if there is only one document:
        # if that is empty and unedited, use it.
        if (len(documents) == 1
            and documents[0].url().isEmpty()
            and documents[0].isEmpty()
            and not documents[0].isUndoAvailable()
            and not documents[0].isRedoAvailable()):
            d = documents[0]
            d.setEncoding(encoding)
            if not url.isEmpty():
                d.load(url)
        else:
            import document
            d = document.Document.new_from_url(url, encoding)
    return d

def findDocument(url):
    """Returns a Document instance for the given QUrl if already loaded.

    Returns None if no document with given url exists or if the url is empty.

    """
    if not url.isEmpty():
        for d in documents:
            if url == d.url():
                return d

def instantiate():
    """Instantiate the global QApplication object."""
    global qApp
    args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
    ### on Python3, QApplication args must be byte strings
    if sys.version_info >= (3, 0):
        args = list(map(os.fsencode, args))
    qApp = QApplication(args)
    QApplication.setApplicationName(appinfo.name)
    QApplication.setApplicationVersion(appinfo.version)
    QApplication.setOrganizationName(appinfo.name)
    QApplication.setOrganizationDomain(appinfo.domain)
    appInstantiated()

def oninit(func):
    """Call specified function on QApplication instantiation.

    If the QApplication already has been instantiated, the function is called
    directly.

    As this function returns the specified function, you can use this as a
    decorator.

    """
    if qApp:
        func()
    else:
        appInstantiated.connect(func)
    return func

def run():
    """Emit the appStarted signal and enter the Qt event loop."""
    appStarted()
    result = qApp.exec_()
    aboutToQuit()
    return result

def restart():
    """Restarts Frescobaldi."""
    args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
    python_executable = sys.executable
    if python_executable:
        args = [python_executable] + args
    import subprocess
    subprocess.Popen(args)

def translateUI(obj, priority=0):
    """Translates texts in the object.

    Texts are translated again if the language is changed.
    The object must have a translateUI() method.  It is
    also called by this function.

    """
    languageChanged.connect(obj.translateUI, priority)
    obj.translateUI()

def caption(title):
    """Returns a nice dialog or window title with appname appended."""
    return "{0} \u2013 {1}".format(title, appinfo.appname)

def filetypes(extension=None):
    """Returns a list of supported filetypes.

    If a type matches extension, it is placed first.

    """
    have, havenot = [], []
    for patterns, name in (
            ("{0} (*.ly *.lyi *.ily)",          _("LilyPond Files")),
            ("{0} (*.tex *.lytex *.latex)",     _("LaTeX Files")),
            ("{0} (*.docbook *.lyxml)",         _("DocBook Files")),
            ("{0} (*.html *.xml)",              _("HTML Files")),
            ("{0} (*.itely *.tely *.texi *.texinfo)", _("Texinfo Files")),
            ("{0} (*.scm)",                     _("Scheme Files")),
            ("{0} (*)",                         _("All Files")),
            ):
        if extension and extension in patterns:
            have.append(patterns.format(name))
        else:
            havenot.append(patterns.format(name))
    return ";;".join(have + havenot)

def basedir():
    """Returns a base directory for documents.

    First looks in the session settings, then the default settings.
    Returns "" if no directory was set. It is recommended to use the
    home directory in that case.

    """
    import sessions
    conf = sessions.currentSessionGroup()
    if conf:
        basedir = conf.value("basedir", "", str)
        if basedir:
            return basedir
    return QSettings().value("basedir", "", str)

def settings(name):
    """Returns a QSettings object referring a file in ~/.config/frescobaldi/"""
    s = QSettings()
    s.beginGroup(name)
    s.setFallbacksEnabled(False)
    return s

def excepthook(exctype, excvalue, exctb):
    """Called when a Python exception goes unhandled."""
    from traceback import format_exception
    sys.stderr.write(''.join(format_exception(exctype, excvalue, exctb)))
    if exctype != KeyboardInterrupt:
        # show dialog, but not when in non-GUI thread
        if QThread.currentThread() == qApp.thread():
            import exception
            exception.ExceptionDialog(exctype, excvalue, exctb)

def displayhook(obj):
    """Prevent normal displayhook from overwriting __builtin__._"""
    if obj is not None:
        print(repr(obj))

_is_git_controlled = None

def is_git_controlled():
    global _is_git_controlled
    if _is_git_controlled is None:
        import vcs
        _is_git_controlled = vcs.app_is_git_controlled()
    return _is_git_controlled