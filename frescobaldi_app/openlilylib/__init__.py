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
openLilyLib support

openLilylib (https://github.com/openlilylib) is a LilyPond extension package framework
intended to make additional functionality available for LilyPond users in
coherent "packages" without having to add the functionality to LilyPond's code base.

Support for openLilyLib in Frescobaldi serves two purposes:
- giving openLilyLib users convenient interfaces to manage and configure packages
  and ease their use in LilyPond projects
- adding "compilation features" similar to the Layout Control Mode
  by injecting openLilyLib code into the compilation.
  It is important to keep in mind that such functions must *not* persistently change
  the documents and make them work within Frescobaldi only.
"""

from . import oll_lib


# cached object to access by openlilylib.lib
lib = oll_lib.OllLib()
