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
Manages cursor positions of file-references in error messages.
"""


import app
import plugin




def errors(document):
    return Errors.instance(document)
    


class Errors(plugin.DocumentPlugin):
    def __init__(self, document):
        self._cursors = {}
        
    def cursor(self, url, load=False):
        """Returns a QTextCursor belonging to the url (string).
        
        If load (defaulting to False) is True, the document is loaded
        if it wasn't already loaded.
        Returns None if the url was not valid or the document could not be loaded.
        
        """
        print url
        pass # TODO: implement


