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
Generates HTML on the fly for help browser, served via a custom fhelp: url scheme
"""

import info
import network


def fhelp(url):
    """Returns HTML for custom fhelp: urls."""
    path = url.path()
    if path == "titlepage":
        return titlepage()


# install the custom url scheme
network.accessmanager().registerHtmlHandler("fhelp", fhelp)



def titlepage():
    
    title = _("Documentation")
    versioninfo = _("{appname} version {version}").format(appname = info.appname, version = info.version)
    
    return titlepage_template.format(**locals())



titlepage_template = """\
<html><body>
<h1>{title}</h1>
<p>{versioninfo}</p>
</body></html>
"""




