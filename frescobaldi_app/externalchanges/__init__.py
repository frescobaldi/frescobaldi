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
This module monitors open documents for changes on disk (overwrite or move and
delete operations) by external programs.

The documentwatcher module is used to do the actual monitoring work,
this module checks if a touched file really changed and pops up the window
if needed.

"""



from PyQt5.QtCore import QSettings, QTimer


def enabled():
    """Return whether watching documents is enabled by the user."""
    return QSettings().value("externalchanges/enabled", True, bool)


def setEnabled(enable):
    """Enable or disable watching documents, saves the setting."""
    if enabled() != bool(enable):
        QSettings().setValue("externalchanges/enabled", bool(enable))
        setup()


def setup():
    """Start or stop the document watching according to the settings."""
    import documentwatcher
    if enabled():
        documentwatcher.documentChangedOnDisk.connect(slotDocumentChanged)
        documentwatcher.start()
    else:
        documentwatcher.documentChangedOnDisk.disconnect(slotDocumentChanged)
        documentwatcher.stop()


def changedDocuments():
    """Return a list of really changed Documents.

    When a document is not modified and the file on disk is exactly the same,
    the document is not considered having been changed on disk.

    """
    import documentwatcher
    for w in documentwatcher.DocumentWatcher.instances():
        d = w.document()
        if w.changed and not d.isModified():
            filename = d.url().toLocalFile()
            if filename:
                try:
                    with open(filename, 'rb') as diskfile:
                        if diskfile.read() == d.encodedText():
                            w.changed = False
                except (OSError, IOError):
                    pass
    return [w.document() for w in documentwatcher.DocumentWatcher.instances()
              if w.changed]


def display(documents):
    """Diplay the window showing the specified Documents."""
    from . import widget
    window = widget.window()
    window.setDocuments(documents)
    window.show()


def displayChangedDocuments():
    """Display the window, even if there are no changed files."""
    display(changedDocuments())


def checkChangedDocuments():
    """Display the window if there are changed files."""
    docs = changedDocuments()
    if docs:
        display(docs)


# timer to wait before really looking at the changed files, a file could
# probably still be changing.
_timer = QTimer(singleShot=True, timeout=checkChangedDocuments)


def slotDocumentChanged(document):
    """Called when a document is changed."""
    _timer.start(500)


# initial setup
if enabled():
    setup()

