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
The global things in Frescobaldi.
"""

import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
documentCreated = SignalInstance()      # Document
documentUrlChanged = SignalInstance()   # Document
documentModificationChanged = SignalInstance() # Document
documentClosed = SignalInstance()       # Document
languageChanged = SignalInstance()      # (no arguments)
settingsChanged = SignalInstance()      # (no arguments)

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
    sys.exit(qApp.exec_())
    
def quit():
    for window in windows:
        if not window.close():
            break

def startSession(name):
    """Switches to the given session."""
    
def caption(title):
    """Returns a nice dialog or window title with appname appended."""
    return "{0} \u2013 {1}".format(title, info.appname)

def filetypes(extension=None):
    """Returns a list of supported filetypes.
    
    If a type matches extension, it is placed first.
    
    """
    l = []
    for patterns, name in (
            ("{0} (*.ly *.lyi *.ily)", _("LilyPond Files")),
            ("{0} (*.tex *.lytex)",    _("LaTeX Files")),
            ("{0} (*.docbook)",        _("DocBook Files")),
            ("{0} (*.html)",           _("HTML Files")),
            ("{0} (*.scm)",            _("Scheme Files")),
            ("{0} (*)",                _("All Files")),
            ):
        if extension and extension in patterns:
            l.insert(0, patterns.format(name))
        else:
            l.append(patterns.format(name))
    return ";;".join(l)

def settings(name):
    """Returns a QSettings object referring a file in ~/.config/frescobaldi/"""
    return QSettings(info.name, name)

def iswritable(path):
    """Returns True if the path can be written to or created."""
    return ((os.path.exists(path) and os.access(path, os.W_OK))
            or os.access(os.path.dirname(path), os.W_OK))

