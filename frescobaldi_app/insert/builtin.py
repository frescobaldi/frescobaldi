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

"""
Builtin template actions.
"""

import __builtin__
import collections


class _(object):
    """Postpones translation of strings until display."""
    def __init__(self, *args):
        self.args = args
    def __call__(self):
        return __builtin__._(*self.args)


class Action(object):
    """Encapsulates a template to insert."""
    __slots__=(
        'text',
        'title',
        'scope',
    )
    def __init__(self,
            text = "",
            title = "",
            scope = "",
        ):
        self.text = text
        self.title = title or text
        self.scope = scope
    
    

templates = {

'voice1': Action('\\voiceOne'),
'voice2': Action('\\voiceTwo'),
'voice3': Action('\\voiceThree'),
'voice4': Action('\\voiceFour'),
'1voice': Action('\\oneVoice'),


}
