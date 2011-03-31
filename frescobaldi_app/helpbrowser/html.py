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
Generates HTML on the fly for help browser.
"""

import info


def welcome():
    return (
    "<html>"
    "<head>"
    "<title>" + enc(_("Frescobaldi Help Pages")) + "</title>"
    "</head>"
    "<body>"
    "<h1>" + enc(_("Documentation")) + "</h1>" +
    "<p>{0} {1}</p>".format(info.appname, info.version) +
    
    "</body>"
    "</html>\n")
    

def enc(html):
    return html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

