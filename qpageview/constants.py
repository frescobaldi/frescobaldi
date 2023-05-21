# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
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
Constant values.
"""


# rotation:
Rotate_0   = 0      #: normal
Rotate_90  = 1      #: 90° rotated clockwise
Rotate_180 = 2      #: 180° rotated
Rotate_270 = 3      #: 270° rotated (90° couter clockwise)


# viewModes:
FixedScale = 0      #: the scale is not adjusted to the widget size
FitWidth   = 1      #: scale so that the page's width fits in the widget
FitHeight  = 2      #: scale so that the page's height fits in the widget
FitBoth    = FitHeight | FitWidth   #: fit the whole page


# orientation:
Horizontal = 1      #: arrange the pages in horizontal order
Vertical   = 2      #: arrange the pages in vertical order

