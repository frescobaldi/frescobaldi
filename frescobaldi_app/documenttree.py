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
Group all Document instances in a tree structure.

Documents that are included by other Documents are considered a child of that
Document instance.

If a Document is included by multiple documents, it shows up as a child of one
of them. If a Document includes other files that exist on disk but are not open
yet, they can also show up.

"""


import os

import ly.node
import app
import documentinfo


class DocumentNode(ly.node.Node):
    document = None
    url = None


def tree(urls=False):
    """Return the open documents as a tree structure.

    Returned is a ly.node.Node instance having the toplevel documents (documents
    that are not included by other open documents) as children. The children of
    the nodes are the documents that are included by the toplevel document.

    Every node has the Document in its document attribute.

    If urls == True, nodes will also be generated for urls that refer to
    documents that are not yet open. They will have the QUrl in their url
    attribute.

    It is not checked whether the referred to urls or files actually exist.

    """
    root = ly.node.Node()
    nodes = {}
    for doc in app.documents:
        try:
            n = nodes[doc]
        except KeyError:
            n = nodes[doc] = DocumentNode(root)
            n.document = doc
        for u in documentinfo.info(doc).child_urls():
            d = app.findDocument(u)
            if d:
                try:
                    n.append(nodes[d])
                except KeyError:
                    n1 = nodes[d] = DocumentNode(n)
                    n1.document = d
            elif urls:
                try:
                    n.append(nodes[u.toString()])
                except KeyError:
                    n1 = nodes[u.toString()] = DocumentNode(n)
                    n1.url = u
    return root


