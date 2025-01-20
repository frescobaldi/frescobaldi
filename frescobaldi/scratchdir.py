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
Manages a local temporary directory for a Document (e.g. unnamed or remote).
"""


import os

import app
import util
import ly.lex
import documentinfo
import plugin


def scratchdir(document):
    return ScratchDir.instance(document)


def findDocument(filename):
    """Like app.findDocument(), but also takes a possible scratchdir into account.

    If the filename happens to be the scratch-filename of a document, that
    document is returned. Otherwise, the document that really has the filename
    is returned.

    Note that, unlike app.findDocument(), a filename is specified and not a url.

    """
    for d in app.documents:
        if d.url().toLocalFile() == filename:
            return d
        s = ScratchDir.instance(d)
        if s.directory() and util.equal_paths(filename, s.path()):
            return d


class ScratchDir(plugin.DocumentPlugin):

    def __init__(self, document):
        self._directory = None

    def create(self):
        """Creates the local temporary directory."""
        if not self._directory:
            self._directory = util.tempdir()

    def directory(self):
        """Returns the directory if a temporary area was created, else None."""
        return self._directory

    def path(self):
        """Returns the path the saved document text would have if a temporary area was created, else None."""
        if self._directory:
            basename = None
            if not self.document().url().isEmpty():
                basename = os.path.basename(self.document().url().path())
            if not basename:
                basename = 'document' + ly.lex.extensions[documentinfo.mode(self.document())]
            return os.path.join(self._directory, basename)

    def saveDocument(self):
        """Writes the text of the document to our path()."""
        if not self._directory:
            self.create()
        with open(self.path(), 'wb') as f:
            f.write(self.document().encodedText())



