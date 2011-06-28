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

'blankline': T(_("Blank Line"),
r"""
$C
"""),


'quotes_s': T(_("Single Typographical Quotes"),
"""-*- menu: quotes;
\u2018$SELECTION\u2019"""),


'quotes_d': T(_("Double Typographical Quotes"),
"""-*- menu: quotes;
\u201C$SELECTION\u201D"""),


'voice1': T(None,
r"""-*- name: v1;
\voiceOne"""),


'voice2': T(None,
r"""-*- name: v2;
\voiceTwo"""),


'voice3': T(None,
r"""-*- name: v3;
\voiceThree"""),


'voice4': T(None,
r"""-*- name: v4;
\voiceFour"""),


'1voice': T(None,
r"""-*- name: 1v;
\oneVoice"""),


'times23': T(_("Tuplets"),
r"""-*- menu: blocks;
\times 2/3 { $SELECTION_WS }"""),


'onceoverride': T(None,
r"""-*- name: oo;
\once \override """),


'm22': T(_("Modern 2/2 Time Signature"),
r"""-*- name: 22;
\numericTimeSignature
\time 2/2"""),


'm44': T(_("Modern 4/4 Time Signature"),
r"""-*- name: 44;
\numericTimeSignature
\time 4/4"""),


'tactus': T(_("Tactus Time Signature (number with note)"),
r"""-*- name: tac;
\once \override Staff.TimeSignature #'style = #'()
\once \override Staff.TimeSignature #'stencil = #ly:text-interface::print
\once \override Staff.TimeSignature #'text = \markup {
  \override #'(baseline-skip . 0.5)
  \column { \number $C1$A \tiny \note #"2" #-.6 }
}
"""),


'ly_version': T(_("LilyPond Version"),
r"""-*- menu;
\version "$LILYPOND_VERSION"
"""),


'repeat': T(_("Repeat"),
r"""-*- menu: blocks; name: rep;
\repeat volta 2 { $SELECTION_WS }"""),


'relative': T(_("Relative Music"),
r"""-*- name: rel;
\relative c$C'$A {
""" '  ' r"""  
}"""),


}

