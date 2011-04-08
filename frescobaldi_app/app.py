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
The global things in Frescobaldi.
"""

from __future__ import unicode_literals

import os
import sys

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication

import info

qApp = QApplication([os.path.abspath(sys.argv[0])] + sys.argv[1:])
QApplication.setApplicationName(info.name)
QApplication.setApplicationVersion(info.version)
QApplication.setOrganizationName(info.name)
QApplication.setOrganizationDomain(info.url)

windows = []
documents = []

from signals import SignalInstance

# signals
mainwindowCreated = SignalInstance()    # MainWindow
mainwindowClosed = SignalInstance()     # MainWindow
documentCreated = SignalInstance()      # Document
documentUrlChanged = SignalInstance()   # Document
documentLoaded = SignalInstance()       # Document
documentModificationChanged = SignalInstance() # Document
documentClosed = SignalInstance()       # Document
viewSpaceCreated = SignalInstance()     # ViewSpace (see viewmanager.py)
languageChanged = SignalInstance()      # (no arguments)
settingsChanged = SignalInstance()      # (no arguments)
sessionChanged = SignalInstance()       # (no arguments)
jobStarted = SignalInstance()           # (Document, Job)
jobFinished = SignalInstance()          # (Document, Job, bool success)

import mainwindow
import document


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
            d.setUrl(url)
            d.setEncoding(encoding)
            d.load()
        else:
            d = document.Document(url, encoding)
    return d

def findDocument(url):
    """Returns a Document instance for the given QUrl if already loaded.
    
    Returns None if no document with given url exists.
    
    """
    for d in documents:
        if url == d.url():
            return d

def run():
    """Enter the Qt event loop."""
    if not documents:
        document.Document()
    if not windows:
        mainwindow.MainWindow().show()
    sys.excepthook = excepthook
    sys.exit(qApp.exec_())
    
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
    return "{0} \u2013 {1}".format(title, info.appname)

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

def settings(name):
    """Returns a QSettings object referring a file in ~/.config/frescobaldi/"""
    return QSettings(info.name, name)

def excepthook(exctype, excvalue, exctb):
    """Called when a Python exception goes unhandled."""
    from traceback import format_exception
    sys.stderr.write(''.join(format_exception(exctype, excvalue, exctb)))
    if exctype != KeyboardInterrupt:
        import exception
        exception.ExceptionDialog(exctype, excvalue, exctb)

