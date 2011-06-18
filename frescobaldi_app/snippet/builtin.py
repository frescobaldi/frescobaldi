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
Builtin snippets.
"""

from __future__ import unicode_literals

import __builtin__
import collections

# postpone translation
_ = lambda *args: lambda: __builtin__._(*args)


T = collections.namedtuple("Template", "title text")


builtin_snippets = {

'voice1':       T(None, '-*- name: v1;\n\\voiceOne'),
'voice2':       T(None, '-*- name: v2;\n\\voiceTwo'),
'voice3':       T(None, '-*- name: v3;\n\\voiceThree'),
'voice4':       T(None, '-*- name: v4;\n\\voiceFour'),
'1voice':       T(None, '\\oneVoice'),
'times23':      T(_("Tuplets"), '\\times 2/3 { {CURSEL} }'),


}

