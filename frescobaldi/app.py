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



import os
import sys
import platform
import importlib.util
import weakref

from PyQt6.QtCore import QObject, QSettings, Qt, QThread, QStandardPaths
from PyQt6.QtWidgets import QApplication, QMenuBar

### needed for QWebEngine
### it wants those two things be done before constructing QApplication()
if importlib.util.find_spec('PyQt6.QtWebEngineWidgets'):
    import PyQt6.QtWebEngineWidgets
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
### end needed for QWebEngine

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
            d = document.EditorDocument.new_from_url(url, encoding)
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
    args = list(map(os.fsencode, [os.path.abspath(sys.argv[0])] + sys.argv[1:]))
    if platform.system() == "Windows":
        args.append("-platform")
        args.append("windows:fontengine=freetype")
    qApp = QApplication(args)
    QApplication.setApplicationName(appinfo.name)
    QApplication.setApplicationVersion(appinfo.version)
    QApplication.setDesktopFileName(appinfo.desktop_file_name)
    QApplication.setOrganizationName(appinfo.name)
    QApplication.setOrganizationDomain(appinfo.domain)
    if platform.system() == "Darwin":
        qApp._menubar = QMenuBar()
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
    """Enter the Qt event loop."""
    result = qApp.exec()
    aboutToQuit()
    return result

def restart():
    """Restarts Frescobaldi."""
    args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
    python_executable = sys.executable
    if python_executable:
        args = [python_executable] + args
    #NOTE: This deliberately uses subprocess and not job.Job
    # It has turned out that using Job the code files are not
    # reloaded at all.
    import subprocess
    subprocess.Popen(args)

def _make_retranslate_callback(obj):
    ref = weakref.ref(obj)
    def retranslate():
        found_obj = ref()
        if found_obj is None:
            # obj was already collected. Now remove this retranslator itself,
            # we don't need it anymore.
            languageChanged.disconnect(retranslate)
            return
        found_obj.translateUI()
    return retranslate

def translateUI(obj, priority=0):
    """Translates texts in the object.

    Texts are translated again if the language is changed.
    The object must have a translateUI() method.  It is
    also called by this function.

    This function only causes weak references to the object to be ingested, so
    it does not prevent garbage-collecting the object, and will just not
    retranslate it after the object is garbage-collected.  Furthermore, if the
    object is a QObject, the function will refrain from retranslating it as soon
    as the underlying C++ object is deleted, even if the Python object itself is
    only garbage-collected later.  This means that a widget can safely
    retranslate its subwidgets in its translateUI() method, since they are still
    alive on the C++ level, as the widget itself is alive.  On the other hand,
    for non-QObjects, keep in mind the contract: the object must be able to
    retranslate itself without errors at any time until it is garbage-collected.

    """
    obj.translateUI()
    retranslator = _make_retranslate_callback(obj)
    languageChanged.connect(retranslator, priority)
    if isinstance(obj, QObject):
        obj.destroyed.connect(lambda: languageChanged.disconnect(retranslator))

def caption(title):
    """Returns a nice dialog or window title with appname appended."""
    return f"{title} \u2013 {appinfo.appname}"

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
    If no directory was set, this returns the user's Documents directory.

    """
    import sessions
    conf = sessions.currentSessionGroup()
    if not conf:
        conf = QSettings()
    basedir = conf.value("basedir", "", str)
    return basedir if basedir else QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation)

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
    if exctype is not KeyboardInterrupt:
        # show dialog, but not when in non-GUI thread
        if QThread.currentThread() == qApp.thread():
            import exception
            exception.ExceptionDialog(exctype, excvalue, exctb)

def displayhook(obj):
    """Prevent normal displayhook from overwriting __builtin__._"""
    if obj is not None:
        print(repr(obj))


_extensions = None

def load_extensions(mainwindow):
    """Called from MainWindow.__init__()"""
    import extensions
    global _extensions
    _extensions = extensions.Extensions(mainwindow)

def extensions():
    """Return the global Extensions object."""
    global _extensions
    return _extensions


_job_queue = None

def job_queue():
    """Return the global JobQueue object."""
    global _job_queue
    if _job_queue is None:
        import job.queue
        #TODO: save the number of runners in the Preferences
        #NOTE: Provide code for *changing* the number of runners
        _job_queue = job.queue.GlobalJobQueue()
    return _job_queue

_is_git_controlled = None

def is_git_controlled():
    global _is_git_controlled
    if _is_git_controlled is None:
        import vcs
        _is_git_controlled = vcs.app_is_git_controlled()
    return _is_git_controlled

_editor_font = None

def editor_font(requested_family=None):
    """Returns a font suitable for editing text as a QFont object.

    If a specific font family is requested and available, it will be used.
    Otherwise, this attempts to pick a readable monospace font (the exact
    choice of which is platform-dependent).

    """
    global _editor_font
    if requested_family or _editor_font is None:
        from PyQt6.QtGui import QFontDatabase
        available_families = QFontDatabase.families()
    if _editor_font is None:
        # This is always a safe choice but not necessarily the best available
        _editor_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        # Our preferred font is generally the default of the platform's native
        # text editor (Notepad, TextEdit, etc.). If this has changed over time
        # then we try the most recent first.
        if platform.system() == "Darwin":   # macOS
            preferred_families = ["SF Mono", "Menlo", "Monaco"]
        elif platform.system() == "Windows":
            # Avoid Lucida Console since it lacks a bold weight
            preferred_families = ["Consolas"]
        else:
            preferred_families = ["monospace"]
        for family in preferred_families:
            if family in available_families:
                _editor_font.setFamily(family)
                break
    # Caller requests should not override the global default
    font = _editor_font
    if requested_family and requested_family in available_families:
        font.setFamily(requested_family)
    return font
