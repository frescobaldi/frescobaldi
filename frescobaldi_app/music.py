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



import ly.music.items
import fileinfo


class Document(ly.music.items.Document):
    """music.Document type that caches music trees using fileinfo."""
    def get_included_document_node(self, node):
        """Return a Document for the Include node."""
        filename = node.filename()
        if filename:
            resolved = self.resolve_filename(filename)
            if resolved:
                try:
                    d = fileinfo.music(resolved)
                except IOError:
                    pass
                else:
                    d.include_node = node
                    d.include_path = self.include_path
                    return d


