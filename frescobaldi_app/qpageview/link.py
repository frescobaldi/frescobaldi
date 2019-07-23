# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
Generic Link class and handling of links (clickable areas on a Page).

The link area is in coordinates between 0.0 and 1.0, like Poppler does it.
This way we can easily compute where the link area is on a page in different
sizes or rotations.

"""

import collections

from . import rectangles


linkarea = collections.namedtuple("linkarea", "left top right bottom")


class Link:
    url = ""
    tooltip = ""
    area = linkarea(0, 0, 0, 0)

    def __init__(self, left, top, right, bottom, url=None, tooltip=None):
        self.area = linkarea(left, top, right, bottom)
        if url:
            self.url = url
        if tooltip:
            self.tooltip = tooltip


class Links(rectangles.Rectangles):
    """Manages a list of Link objects.
    
    See the rectangles documentation for how to access the links.
    
    """
    def get_coords(self, link):
        return link.area


