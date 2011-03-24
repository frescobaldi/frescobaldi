# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Icons.
"""

from PyQt4.QtCore import QDir, QFile, QSize
from PyQt4.QtGui import QIcon

QDir.setSearchPaths("icons", __path__)

_cache = {}

def get(name):
    if QIcon.hasThemeIcon(name):
        return QIcon.fromTheme(name)
    try:
        return _cache[name]
    except KeyError:
        icon = _cache[name] = QIcon()
        # first try SVG
        fname = 'icons:{0}.svg'.format(name)
        if QFile(fname).exists():
            icon.addFile(fname)
        else:
            # then try different sizes
            for size in (0, 16, 22, 32, 48):
                fname = 'icons:{0}{1}.png'.format(name, size or '')
                if QFile(fname).exists():
                    qsize = QSize(size, size) if size else QSize()
                    icon.addFile(fname, qsize)
        return icon

