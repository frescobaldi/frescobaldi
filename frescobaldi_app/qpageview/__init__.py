# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2016 by Wilbert Berendsen
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
This is a generic paged view widget.

Its main design goal is to display the pages of a PDF document, but it can
display any set of images or pages, originating from different documents.

Every page is represented by a Page instance, which encompasses all logic
for the document type, i.e. drawing etc.

Pages are managed by a PageLayout.

A PageLayout can be set to a View so the pages are displayed.

Because the qpageview is built on Qt, we use the Qt convention
to have camelCase method names and CamelCase class names.

"""

from .constants import (
    # rotation:
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,


    # viewModes:
    FixedScale,
    FitWidth,
    FitHeight,
    FitBoth,


    # orientation:
    Horizontal,
    Vertical,

)

from .view import View
from .layout import PageLayout, RowPageLayout
