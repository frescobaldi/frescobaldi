# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2014 - 2014 by Wilbert Berendsen
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
Frescobaldi's extensions of ly.music.
"""

from __future__ import unicode_literals


import ly.music.items
import documentinfo
import fileinfo


def document(doc):
    """Return a Document music tree for the specified document.
    
    This is equivalent to documentinfo.docinfo(doc).music(),
    and thus uses caching (you should not alter the music tree).
    
    """
    return documentinfo.docinfo(doc).music()


class Document(ly.music.items.Document):
    """music.Document type that caches music trees using fileinfo."""
    def get_music(self, filename):
        return fileinfo.docinfo(filename).music()


