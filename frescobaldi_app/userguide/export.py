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
Export the user guide to other formats and destinations.
"""


import re

import simplemarkdown

from . import page
from . import util


class Exporter(object):
    """Export userguide pages to other formats or destinations."""
    def __init__(self):
        self._pages = []

    def add_page(self, name):
        """Add a help page. Return True if the page was not already added."""
        if name not in self._pages:
            self._pages.append(name)
            return True

    def add_recursive(self, name):
        """Add a help page and its child pages recursively."""
        def add(name):
            if self.add_page(name):
                for c in util.cache.children(name):
                    add(c)
        add(name)

    def replace_links(self, text):
        """Alter links in the text to other help pages.

        Calls replace_link() for every match of a HTML <a href...> construct.

        """
        return re.sub(r'<a href="([^"])">', self.replace_link, re.I)

    def replace_link(self, match):
        url = match.group(1)
        if '/' in url:
            return match.group()
        if url in self._pages:
            return '<a href="#{0}">'.format(match.group(1))
        return '<a href="{0}.html">'.format(match.group(1))





