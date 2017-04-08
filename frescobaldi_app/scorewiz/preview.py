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
Fill in a ly.dom Document with example music for previewing.
"""


import itertools
import math

import ly.dom


def examplify(doc):
    """Fills in some example music in the given ly.dom.Document."""
    stubs = []
    globals = {}
    for a in doc.find_children(ly.dom.Assignment, 2):
        if isinstance(a.name, ly.dom.Reference):
            g = None
            for i in a.find_children(ly.dom.Identifier):
                if not isinstance(i.name, ly.dom.Reference):
                    g = i.name
                    break
            stubs.append((g, a[-1]))
        else:
            keysig = a.find_child(ly.dom.KeySignature)
            timesig = a.find_child(ly.dom.TimeSignature)
            partial = a.find_child(ly.dom.Partial)

            # create a list of durations for the example notes.
            durations = []
            if partial:
                durations.append((partial.dur, partial.dots))
            if timesig:
                dur = int(math.log(int(timesig.beat), 2))
                num = min(int(timesig.num)*2, 10)
            else:
                dur, num = 2, 4
            durations += [(dur, 0)] * num

            globals[a.name] = (keysig, durations)

    # other lyrics on each request
    lyrics = itertools.cycle('ha hi he ho hu'.split())

    # fill assignment stubs with suitable example music input
    num = 10
    for g, stub in stubs:
        try:
            keysig, durations = globals[g]
            num = len(durations)
        except KeyError:
            pass

        def addItems(stub, generator):
            for dur, dots in durations:
                node = next(generator)
                node.append(ly.dom.Duration(dur, dots))
                stub.append(node)

        if isinstance(stub, ly.dom.LyricMode):
            stub.append(ly.dom.Text(' '.join(itertools.repeat(next(lyrics), num))))
        elif isinstance(stub, ly.dom.Relative):
            addItems(stub[-1], pitchGen(keysig))
        elif isinstance(stub, ly.dom.ChordMode):
            addItems(stub, chordGen(keysig))
        elif isinstance(stub, ly.dom.FigureMode):
            addItems(stub, figureGen())
        elif isinstance(stub, ly.dom.DrumMode):
            addItems(stub, drumGen())


# Generators for different kinds of example input
def pitchGen(startPitch):
    note = startPitch.note
    while True:
        for n in (note, note, (note + 9 ) % 7, (note + 8) % 7,
                  note, (note + 11) % 7, note):
            chord = ly.dom.Chord()
            ly.dom.Pitch(-1, n, startPitch.alter, parent=chord)
            yield chord


def chordGen(startPitch):
    for n in pitchGen(startPitch):
        yield n
        for i in 1, 2, 3:
            yield ly.dom.TextDur("\\skip")


def figureGen():
    while True:
        for i in 5, 6, 3, 8, 7:
            for s in "<{0}>".format(i), "\\skip", "\\skip":
                yield ly.dom.TextDur(s)


def drumGen():
    while True:
        for s in "bd", "hh", "sn", "hh":
            yield ly.dom.TextDur(s)


