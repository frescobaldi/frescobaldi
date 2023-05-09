# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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

r"""
Routines that manipulate an XML mapping very similar to the Scheme music
structure used by LilyPond itself.

The mapping can also be generated from within LilyPond and then parsed
by other programs.

While designing the mapping, I decided to use xml elements for almost
everything, only values that are very simple in all cases, are attributes.

Code could be written to convert such an XML music tree to other formats.

Also code is added to build such trees from scratch and from tokenized
documents.

Code will be added to print LilyPond source. When all is finished, `ly.dom`
is deprecated and `ly.music` will probably use these xml tree for storage.

A single LilyPond file `xml-export.ily` is also included with this module;
it can be \included in a LilyPond document and exports the
``\displayLilyXML`` music function.

"""

from __future__ import unicode_literals
from __future__ import absolute_import
