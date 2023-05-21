# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2011 - 2015 by Wilbert Berendsen
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
Transforming music by pitch manipulation.
"""

from __future__ import unicode_literals

import ly.lex.lilypond


def retrograde(cursor, language="nederlands"):
    """Reverses pitches."""    
    source = ly.document.Source(cursor, True, tokens_with_position=True)

    pitches = ly.pitch.PitchIterator(source, language)
    psource = pitches.pitches()

    plist = [p for p in psource if isinstance(p, ly.pitch.Pitch)]
    rlist = [r.copy() for r in reversed(plist)]
    
    with cursor.document as d:
        for p, r in zip(plist, rlist):
            p.note = r.note   
            p.alter = r.alter            
            p.octave = r.octave          
            pitches.write(p)

def inversion(cursor, language="nederlands"):
    """Inversion of the intervals between pitches."""
    import ly.pitch.transpose
     
    source = ly.document.Source(cursor, True, tokens_with_position=True)

    pitches = ly.pitch.PitchIterator(source, language)
    psource = pitches.pitches()

    prev_note = None

    with cursor.document as d:
        for p in psource:
            if isinstance(p, ly.pitch.Pitch):
                if prev_note is None:
                    prev_note = refp = p
                    continue
                transposer = ly.pitch.transpose.Transposer(p, prev_note)
                prev_note = p.copy()
                p.note = refp.note
                p.alter = refp.alter
                p.octave = refp.octave               
                transposer.transpose(p)
                refp = p
                pitches.write(p)
                
     
