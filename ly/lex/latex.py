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

"""
Parses and tokenizes LaTeX input, recognizing LilyPond in LaTeX.
"""

from __future__ import unicode_literals

from . import _token
from . import Parser


class ParseLaTeX(Parser):
    mode = "latex"
    items = (
        _token.Space,
    )


