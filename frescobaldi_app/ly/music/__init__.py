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
An api to read music from the tokens of a ly.document.Document.

This is meant to quickly read music from a document, to perform 
modifications on the document, and to interpret music and markup and to 
convert or export it to other formats.

This package is not intended to construct documents entirely from scratch. 
(This can be done using the ly.dom module.)

Some item types can have a list of child items, but the tree structure is as 
linear as possible.

"""

import ly.document


def document(doc):
    """Return a music.items.Document instance for the ly.document.Document."""
    from . import items
    return items.Document(doc)


