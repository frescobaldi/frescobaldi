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
Finds out which type of LilyPond object the offset will be applied to
using ly.music.
"""

from __future__ import unicode_literals

import documentinfo
import lydocument


class DefineOffset():

    def __init__(self, doc):
        self.docinfo = documentinfo.music(doc)
        self.node = None
        
    def getCurrentLilyObject(self, cursor):
        """ Use cursor from textedit link to get type of object being edited."""        
        lycursor = lydocument.cursor(cursor)        
        node = self.docinfo.node(lycursor.start)
        self.node = node
        child = self.docinfo.iter_music(node)
        for c in child:
            name = c.__class__.__name__ #get instance name
            return self.item2object(name)
        name = node.__class__.__name__
        return self.item2object(name)		
        
    def item2object(self, item):
        """ Translate item type into name of 
		LilyPond object.
        """
        item2objectDict = {"String": "TextScript", 
        "Markup": "TextScript",
        "Tempo": "MetronomeMark"}
        try:
            obj = item2objectDict[item]
        except KeyError:
            obj = "still testing!"
        return obj

