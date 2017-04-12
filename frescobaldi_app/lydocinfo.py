# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Harvest information from a ly.document.DocumentBase instance.

This extends the ly.docinfo.DocInfo class with some behaviour specific to
Frescobaldi, such as variables.

With this module, information extracted from tokenized LilyPond source is
available to both text documents on disk and loaded Frescobaldi documents.

"""

from __future__ import absolute_import

import re

import ly.docinfo


class DocInfo(ly.docinfo.DocInfo):
    """Add Frescobaldi-specific stuff to ly.docinfo.DocInfo."""

    def __init__(self, doc, variables):
        """Initialize with ly.document instance and variables dictionary."""
        super(DocInfo, self).__init__(doc)
        self.variables = variables

    @ly.docinfo._cache
    def version_string(self):
        """Return the version, but also looks in the variables and comments."""
        version = super(DocInfo, self).version_string()
        if version:
            return version
        version = self.variables.get("version")
        if version:
            return version
        # parse whole document for non-lilypond comments
        m = re.search(r'\\version\s*"(\d+\.\d+(\.\d+)*)"', self.document.plaintext())
        if m:
            return m.group(1)


