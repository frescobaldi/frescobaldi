# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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
Entry point of Frescobaldi.
"""

import sys
import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

from PyQt4.QtGui import QApplication
app = QApplication(sys.argv)

import info
app.setApplicationName(info.name)
app.setApplicationVersion(info.version)
app.setOrganizationName(info.description)
app.setOrganizationDomain(info.url)
print app.arguments()

