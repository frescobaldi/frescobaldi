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
Store meta information about documents.
"""

import contextlib
import json
import time
import weakref

from PyQt4.QtCore import QSettings, QUrl

import app


__all__ = ["info"]


_docinfo = weakref.WeakKeyDictionary() # for (unsaved) documents that have no URL
_urlinfo = {}  # for documents that have a URL


class MetaInfo(object):
    """Stores meta-information about a Document."""
    def __init__(self):
        self.position = 0
        self.bookmarks = json.dumps(None)

    def load(self, url, settings=None):
        """Loads our settings from the group of url."""
        with settingsGroup(url, settings) as s:
            self.position = int(s.value("position", 0))
            self.bookmarks = bytes(s.value("bookmarks", json.dumps(None)))
            
    def save(self, url, settings=None):
        """Saves our settings to the group of url."""
        with settingsGroup(url, settings) as s:
            s.setValue("time", time.time())
            s.setValue("position", self.position)
            s.setValue("bookmarks", self.bookmarks)
            

@contextlib.contextmanager
def settingsGroup(url, s=None):
    """Returns a contextmanager which is the group metainfo can be saved to."""
    if s is None:
        s = app.settings('metainfo')
    name = url.toString().replace('\\', '_').replace('/', '_')
    s.beginGroup(name)
    try:
        yield s
    finally:
        s.endGroup()

def info(document):
    """Returns a MetaInfo object for the Document."""
    url = document.url()
    if url.isEmpty():
        try:
            res = _docinfo[document]
        except KeyError:
            res = _docinfo[document] = MetaInfo()
        return res
    else:
        try:
            res = _urlinfo[url]
        except KeyError:
            res = _urlinfo[url] = MetaInfo()
            res.load(url)
        return res

@app.qApp.aboutToQuit.connect
def saveMetaInfo():
    """Saves all not yet saved meta information."""
    s = app.settings('metainfo')
    for url, info in _urlinfo.items():
        info.save(url, s)
    # prune old stuff
    month_ago = time.time() - 31 * 24 * 3600
    for key in s.childGroups():
        if float(s.value(key + "/time", 0.0)) < month_ago:
            s.remove(key)

@app.documentUrlChanged.connect
def slotUrlChanged(document):
    """Called when a document changes URL."""
    try:
        del _docinfo[document]
    except KeyError:
        pass

@app.documentClosed.connect
def slotDocumentClosed(document):
    """Called when a document closes."""
    url = document.url()
    if not url.isEmpty() and url in _urlinfo:
        _urlinfo[url].save(url)
        del _urlinfo[url]

