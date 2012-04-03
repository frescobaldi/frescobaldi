# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Some functions making it easy to build HTML strings in Python.
"""

from __future__ import unicode_literals


def block_tag(name):
    """Generates a tag-wrapping function."""
    fmt = '<{0}>{{0}}</{0}>\n'.format(name).format
    def func(*args):
        return ''.join(map(fmt, args))
    func.__name__ = name.encode('latin1')
    func.__doc__ = 'Wraps each argument in a {0} tag'.format(name)
    return func

p = block_tag('p')

ul = block_tag('ul')
ol = block_tag('ol')
li = block_tag('li')

