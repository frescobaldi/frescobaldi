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
Vocal part types.
"""


import collections
import itertools
import re

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout)

import listmodel
import ly.dom

from . import _base
from . import register


class VocalPart(_base.Part):
    """Base class for vocal parts."""
    midiInstrument = 'choir aahs'

    def createWidgets(self, layout):
        self.createStanzaWidget(layout)
        self.createAmbitusWidget(layout)

    def translateWidgets(self):
        self.translateStanzaWidget()
        self.translateAmbitusWidget()

    def createStanzaWidget(self, layout):
        self.stanzas = QSpinBox(minimum=1, maximum=99, value=1)
        self.stanzasLabel = QLabel()
        self.stanzasLabel.setBuddy(self.stanzas)
        box = QHBoxLayout(spacing=0)
        box.addWidget(self.stanzasLabel)
        box.addWidget(self.stanzas)
        layout.addLayout(box)

    def translateStanzaWidget(self):
        self.stanzasLabel.setText(_("Stanzas:"))
        self.stanzas.setToolTip(_("The number of stanzas."))

    def createAmbitusWidget(self, layout):
        self.ambitus = QCheckBox()
        layout.addWidget(self.ambitus)

    def translateAmbitusWidget(self):
        self.ambitus.setText(_("Ambitus"))
        self.ambitus.setToolTip(_(
            "Show the pitch range of the voice at the beginning of the staff."))

    def assignLyrics(self, data, name, verse=0):
        """Creates an empty assignment for lyrics.

        Returns the assignment.

        """
        l = ly.dom.LyricMode()
        if verse:
            name = name + ly.util.int2text(verse)
            ly.dom.Line('\\set stanza = "{0}."'.format(verse), l)
        a = data.assign(name)
        a.append(l)
        ly.dom.LineComment(_("Lyrics follow here."), l)
        ly.dom.BlankLine(l)
        return a

    def addStanzas(self, data, node):
        """Add stanzas to the given (Voice) node.

        The stanzas (as configured in self.stanzas.value()) are added
        using \\addlyrics.

        """
        if self.stanzas.value() == 1:
            ly.dom.Identifier(self.assignLyrics(data, 'verse').name, ly.dom.AddLyrics(node))
        else:
            for i in range(self.stanzas.value()):
                ly.dom.Identifier(self.assignLyrics(data, 'verse', i + 1).name, ly.dom.AddLyrics(node))


class VocalSoloPart(VocalPart, _base.SingleVoicePart):
    """Base class for vocal solo parts."""
    octave = 1
    clef = None

    def build(self, data, builder):
        super(VocalSoloPart, self).build(data, builder)
        stub = data.assignments[-1][0][-1]
        stub.insert(1, ly.dom.Line('\\dynamicUp')) # just after the \global
        staff = data.nodes[-1]
        staff[-1].may_remove_brackets = False
        self.addStanzas(data, staff)
        if self.ambitus.isChecked():
            ly.dom.Line('\\consists "Ambitus_engraver"', staff.getWith())


class SopranoVoice(VocalSoloPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Soprano")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Soprano", "S.")


class MezzoSopranoVoice(VocalSoloPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Mezzo-soprano")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Mezzo-soprano", "Ms.")


class AltoVoice(VocalSoloPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Alto")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Alto", "A.")

    octave = 0


class TenorVoice(VocalSoloPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Tenor")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Tenor", "T.")

    octave = 0
    clef = 'treble_8'


class BassVoice(VocalSoloPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Bass")

    @staticmethod
    def short(_=_base.translate):
        return _("abbreviation for Bass", "B.")

    octave = -1
    clef = 'bass'


class LeadSheet(VocalPart, _base.ChordNames):
    @staticmethod
    def title(_=_base.translate):
        return _("Lead sheet")

    def createWidgets(self, layout):
        self.label = QLabel(wordWrap=True)
        self.chords = QGroupBox(checkable=True, checked=True)
        layout.addWidget(self.label)
        layout.addWidget(self.chords)
        box = QVBoxLayout()
        self.chords.setLayout(box)
        _base.ChordNames.createWidgets(self, box)
        self.accomp = QCheckBox()
        layout.addWidget(self.accomp)
        VocalPart.createWidgets(self, layout)

    def translateWidgets(self):
        VocalPart.translateWidgets(self)
        _base.ChordNames.translateWidgets(self)
        self.label.setText('<i>{0}</i>'.format(_(
            "The Lead Sheet provides a staff with chord names above "
            "and lyrics below it. A second staff is optional.")))
        self.chords.setTitle(_("Chord names"))
        self.accomp.setText(_("Add accompaniment staff"))
        self.accomp.setToolTip(_(
            "Adds an accompaniment staff and also puts an accompaniment "
            "voice in the upper staff."))

    def build(self, data, builder):
        """Create chord names, song and lyrics.

        Optionally a second staff with a piano accompaniment.

        """
        if self.chords.isChecked():
            _base.ChordNames.build(self, data, builder)
        if self.accomp.isChecked():
            p = ly.dom.ChoirStaff()
            #TODO: instrument names ?
            #TODO: different midi instrument for voice and accompaniment ?
            s = ly.dom.Sim(p)
            mel = ly.dom.Sim(ly.dom.Staff(parent=s))
            v1 = ly.dom.Voice(parent=mel)
            s1 = ly.dom.Seq(v1)
            ly.dom.Text('\\voiceOne', s1)
            a = data.assignMusic('melody', 1)
            ly.dom.Identifier(a.name, s1)
            s2 = ly.dom.Seq(ly.dom.Voice(parent=mel))
            ly.dom.Text('\\voiceTwo', s2)
            a = data.assignMusic('accRight', 0)
            ly.dom.Identifier(a.name, s2)
            acc = ly.dom.Seq(ly.dom.Staff(parent=s))
            ly.dom.Clef('bass', acc)
            a = data.assignMusic('accLeft', -1)
            ly.dom.Identifier(a.name, acc)
            if self.ambitus.isChecked():
                # We can't use \addlyrics when the voice has a \with {}
                # section, because it creates a nested Voice context.
                # So if the ambitus engraver should be added to the Voice,
                # we don't use \addlyrics but create a new Lyrics context.
                # So in that case we don't use addStanzas, but insert the
                # Lyrics contexts manually inside our ChoirStaff.
                v1.cid = ly.dom.Reference('melody')
                ly.dom.Line('\\consists "Ambitus_engraver"', v1.getWith())
                count = self.stanzas.value() # number of stanzas
                if count == 1:
                    l = ly.dom.Lyrics()
                    s.insert_before(acc.parent(), l)
                    a = self.assignLyrics(data, 'verse')
                    ly.dom.Identifier(a.name, ly.dom.LyricsTo(v1.cid, l))
                else:
                    for i in range(count):
                        l = ly.dom.Lyrics()
                        s.insert_before(acc.parent(), l)
                        a = self.assignLyrics(data, 'verse', i + 1)
                        ly.dom.Identifier(a.name, ly.dom.LyricsTo(v1.cid, l))
            else:
                self.addStanzas(data, v1)
        else:
            a = data.assignMusic('melody', 1)
            p = ly.dom.Staff()
            ly.dom.Identifier(a.name, ly.dom.Seq(p))
            self.addStanzas(data, p)
            if self.ambitus.isChecked():
                ly.dom.Line('\\consists "Ambitus_engraver"', p.getWith())
        data.nodes.append(p)


class Choir(VocalPart):
    @staticmethod
    def title(_=_base.translate):
        return _("Choir")

    def createWidgets(self, layout):
        self.label = QLabel(wordWrap=True)
        self.voicingLabel = QLabel()
        self.voicing = QComboBox(editable=True)
        self.voicingLabel.setBuddy(self.voicing)
        self.voicing.setCompleter(None)
        self.voicing.setValidator(QRegExpValidator(
            QRegExp("[SATB]+(-[SATB]+)*", Qt.CaseInsensitive), self.voicing))
        self.voicing.addItems((
            'SA-TB', 'S-A-T-B',
            'SA', 'S-A', 'SS-A', 'S-S-A',
            'TB', 'T-B', 'TT-B', 'T-T-B',
            'SS-A-T-B', 'S-A-TT-B', 'SS-A-TT-B',
            'S-S-A-T-T-B', 'S-S-A-A-T-T-B-B',
            ))
        self.lyricsLabel = QLabel()
        self.lyrics = QComboBox()
        self.lyricsLabel.setBuddy(self.lyrics)
        self.lyrics.setModel(listmodel.ListModel(lyricStyles, self.lyrics,
            display=listmodel.translate_index(0),
            tooltip=listmodel.translate_index(1)))
        self.lyrics.setCurrentIndex(0)
        self.pianoReduction = QCheckBox()
        self.rehearsalMidi = QCheckBox()

        layout.addWidget(self.label)
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.voicingLabel)
        box.addWidget(self.voicing)
        self.createStanzaWidget(layout)
        box = QHBoxLayout()
        layout.addLayout(box)
        box.addWidget(self.lyricsLabel)
        box.addWidget(self.lyrics)
        self.createAmbitusWidget(layout)
        layout.addWidget(self.pianoReduction)
        layout.addWidget(self.rehearsalMidi)

    def translateWidgets(self):
        self.translateStanzaWidget()
        self.translateAmbitusWidget()
        self.lyrics.model().update()
        self.label.setText('<p>{0} <i>({1})</i></p>'.format(
            _("Please select the voices for the choir. "
              "Use the letters S, A, T, or B. A hyphen denotes a new staff."),
            _("Hint: For a double choir you can use two choir parts.")))
        self.voicingLabel.setText(_("Voicing:"))
        self.lyricsLabel.setText(_("Lyrics:"))
        self.pianoReduction.setText(_("Piano reduction"))
        self.pianoReduction.setToolTip(_(
            "Adds an automatically generated piano reduction."))
        self.rehearsalMidi.setText(_("Rehearsal MIDI files"))
        self.rehearsalMidi.setToolTip(_(
            "Creates a rehearsal MIDI file for every voice, "
            "even if no MIDI output is generated for the main score."))

    def build(self, data, builder):
        # normalize voicing
        staves = self.voicing.currentText().upper()
        # remove unwanted characters
        staves = re.sub(r'[^SATB-]+', '', staves)
        # remove double hyphens, and from begin and end
        staves = re.sub('-+', '-', staves).strip('-')
        if not staves:
            return

        splitStaves = staves.split('-')
        numStaves = len(splitStaves)
        staffCIDs = collections.defaultdict(int)    # number same-name staff Context-IDs
        voiceCounter = collections.defaultdict(int) # dict to number same voice types
        maxNumVoices = max(map(len, splitStaves))   # largest number of voices
        numStanzas = self.stanzas.value()
        lyrics = collections.defaultdict(list)      # lyrics grouped by stanza number
        pianoReduction = collections.defaultdict(list)
        rehearsalMidis = []

        p = ly.dom.ChoirStaff()
        choir = ly.dom.Sim(p)
        data.nodes.append(p)

        # print main instrumentName if there are more choirs, and we
        # have more than one staff.
        if numStaves > 1 and data.num:
            builder.setInstrumentNames(p,
                builder.instrumentName(lambda _: _("Choir"), data.num),
                builder.instrumentName(lambda _: _("abbreviation for Choir", "Ch."), data.num))

        # get the preferred way of adding lyrics
        lyrAllSame, lyrEachSame, lyrEachDiff, lyrSpread = (
            self.lyrics.currentIndex() == i for i in range(4))
        lyrEach = lyrEachSame or lyrEachDiff

        # stanzas to print (0 = don't print stanza number):
        if numStanzas == 1:
            allStanzas = [0]
        else:
            allStanzas = list(range(1, numStanzas + 1))

        # Which stanzas to print where:
        if lyrSpread and numStanzas > 1 and numStaves > 2:
            spaces = numStaves - 1
            count, rest = divmod(max(numStanzas, spaces), spaces)
            stanzaSource = itertools.cycle(allStanzas)
            stanzaGroups = (itertools.islice(stanzaSource, num)
                            for num in itertools.chain(
                                itertools.repeat(count + 1, rest),
                                itertools.repeat(count, numStaves - rest)))
        else:
            stanzaGroups = itertools.repeat(allStanzas, numStaves)

        # a function to set staff affinity (in LilyPond 2.13.4 and above):
        if builder.lyVersion >= (2, 13, 4):
            def setStaffAffinity(context, affinity):
                ly.dom.Line("\\override VerticalAxisGroup "
                     "#'staff-affinity = #" + affinity, context.getWith())
        else:
            def setStaffAffinity(lyricsContext, affinity):
                pass

        # a function to make a column markup:
        if builder.lyVersion >= (2, 11, 57):
            columnCommand = 'center-column'
        else:
            columnCommand = 'center-align'
        def makeColumnMarkup(names):
            node = ly.dom.Markup()
            column = ly.dom.MarkupEnclosed(columnCommand, node)
            for name in names:
                ly.dom.QuotedString(name, column)
            return node

        stavesLeft = numStaves
        for staff, stanzas in zip(splitStaves, stanzaGroups):
            # are we in the last staff?
            stavesLeft -= 1
            # the number of voices in this staff
            numVoices = len(staff)
            # sort the letters in order SATB
            staff = ''.join(i * staff.count(i) for i in 'SATB')
            # Create the staff for the voices
            s = ly.dom.Staff(parent=choir)
            builder.setMidiInstrument(s, self.midiInstrument)

            # Build a list of the voices in this staff.
            # Each entry is a tuple(name, num).
            # name is one of 'S', 'A', 'T', or 'B'
            # num is an integer: 0 when a voice occurs only once, or >= 1 when
            # there are more voices of the same type (e.g. Soprano I and II)
            voices = []
            for voice in staff:
                if staves.count(voice) > 1:
                    voiceCounter[voice] += 1
                voices.append((voice, voiceCounter[voice]))

            # Add the instrument names to the staff:
            if numVoices == 1:
                voice, num = voices[0]
                longName = builder.instrumentName(voice2Voice[voice].title, num)
                shortName = builder.instrumentName(voice2Voice[voice].short, num)
                builder.setInstrumentNames(s, longName, shortName)
            else:
                # stack instrument names (long and short) in a markup column.
                # long names
                longNames = makeColumnMarkup(
                    builder.instrumentName(voice2Voice[voice].title, num) for voice, num in voices)
                shortNames = makeColumnMarkup(
                    builder.instrumentName(voice2Voice[voice].short, num) for voice, num in voices)
                builder.setInstrumentNames(s, longNames, shortNames)

            # Make the { } or << >> holder for this staff's children.
            # If *all* staves have only one voice, addlyrics is used.
            # In that case, don't remove the braces.
            staffMusic = (ly.dom.Seq if lyrEach and maxNumVoices == 1 else
                          ly.dom.Seqr if numVoices == 1 else ly.dom.Simr)(s)

            # Set the clef for this staff:
            if 'B' in staff:
                ly.dom.Clef('bass', staffMusic)
            elif 'T' in staff:
                ly.dom.Clef('treble_8', staffMusic)

            # Determine voice order (\voiceOne, \voiceTwo etc.)
            if numVoices == 1:
                order = (0,)
            elif numVoices == 2:
                order = 1, 2
            elif staff in ('SSA', 'TTB'):
                order = 1, 3, 2
            elif staff in ('SAA', 'TBB'):
                order = 1, 2, 4
            elif staff in ('SSAA', 'TTBB'):
                order = 1, 3, 2, 4
            else:
                order = range(1, numVoices + 1)

            # What name would the staff get if we need to refer to it?
            # If a name (like 's' or 'sa') is already in use in this part,
            # just add a number ('ss2' or 'sa2', etc.)
            staffCIDs[staff] += 1
            cid = ly.dom.Reference(staff.lower() +
                str(staffCIDs[staff] if staffCIDs[staff] > 1 else ""))

            # Create voices and their lyrics:
            for (voice, num), voiceNum in zip(voices, order):
                name = voice2id[voice]
                if num:
                    name += ly.util.int2text(num)
                a = data.assignMusic(name, voice2Voice[voice].octave)
                lyrName = name + 'Verse' if lyrEachDiff else 'verse'

                # Use \addlyrics if all staves have exactly one voice.
                if lyrEach and maxNumVoices == 1:
                    for verse in stanzas:
                        lyrics[verse].append((ly.dom.AddLyrics(s), lyrName))
                    ly.dom.Identifier(a.name, staffMusic)
                else:
                    voiceName = voice2id[voice] + str(num or '')
                    v = ly.dom.Voice(voiceName, parent=staffMusic)
                    voiceMusic = ly.dom.Seqr(v)
                    if voiceNum:
                        ly.dom.Text('\\voice' + ly.util.int2text(voiceNum), voiceMusic)
                    ly.dom.Identifier(a.name, voiceMusic)

                    if stanzas and (lyrEach or (voiceNum <= 1 and
                                    (stavesLeft or numStaves == 1))):
                        # Create the lyrics. If they should be above the staff,
                        # give the staff a suitable name, and use alignAbove-
                        # Context to align the Lyrics above the staff.
                        above = voiceNum & 1 if lyrEach else False
                        if above and s.cid is None:
                            s.cid = cid

                        for verse in stanzas:
                            l = ly.dom.Lyrics(parent=choir)
                            if above:
                                l.getWith()['alignAboveContext'] = cid
                                setStaffAffinity(l, "DOWN")
                            elif not lyrEach and stavesLeft:
                                setStaffAffinity(l, "CENTER")
                            lyrics[verse].append((ly.dom.LyricsTo(voiceName, l), lyrName))

                # Add ambitus:
                if self.ambitus.isChecked():
                    ambitusContext = (s if numVoices == 1 else v).getWith()
                    ly.dom.Line('\\consists "Ambitus_engraver"', ambitusContext)
                    if voiceNum > 1:
                        ly.dom.Line("\\override Ambitus #'X-offset = #{0}".format(
                                 (voiceNum - 1) * 2.0), ambitusContext)

                pianoReduction[voice].append(a.name)
                rehearsalMidis.append((voice, num, a.name, lyrName))

        # Assign the lyrics, so their definitions come after the note defs.
        # (These refs are used again below in the midi rehearsal routine.)
        refs = {}
        for verse in allStanzas:
            for node, name in lyrics[verse]:
                if (name, verse) not in refs:
                    refs[(name, verse)] = self.assignLyrics(data, name, verse).name
                ly.dom.Identifier(refs[(name, verse)], node)

        # Create the piano reduction if desired
        if self.pianoReduction.isChecked():
            a = data.assign('pianoReduction')
            data.nodes.append(ly.dom.Identifier(a.name))
            piano = ly.dom.PianoStaff(parent=a)

            sim = ly.dom.Sim(piano)
            rightStaff = ly.dom.Staff(parent=sim)
            leftStaff = ly.dom.Staff(parent=sim)
            right = ly.dom.Seq(rightStaff)
            left = ly.dom.Seq(leftStaff)

            # Determine the ordering of voices in the staves
            upper = pianoReduction['S'] + pianoReduction['A']
            lower = pianoReduction['T'] + pianoReduction['B']

            preferUpper = 1
            if not upper:
                # Male choir
                upper = pianoReduction['T']
                lower = pianoReduction['B']
                ly.dom.Clef("treble_8", right)
                ly.dom.Clef("bass", left)
                preferUpper = 0
            elif not lower:
                # Female choir
                upper = pianoReduction['S']
                lower = pianoReduction['A']
            else:
                ly.dom.Clef("bass", left)

            # Otherwise accidentals can be confusing
            ly.dom.Line("#(set-accidental-style 'piano)", right)
            ly.dom.Line("#(set-accidental-style 'piano)", left)

            # Move voices if unevenly spread
            if abs(len(upper) - len(lower)) > 1:
                voices = upper + lower
                half = (len(voices) + preferUpper) // 2
                upper = voices[:half]
                lower = voices[half:]

            for staff, voices in (ly.dom.Simr(right), upper), (ly.dom.Simr(left), lower):
                if voices:
                    for v in voices[:-1]:
                        ly.dom.Identifier(v, staff)
                        ly.dom.VoiceSeparator(staff).after = 1
                    ly.dom.Identifier(voices[-1], staff)

            # Make the piano part somewhat smaller
            ly.dom.Line("fontSize = #-1", piano.getWith())
            ly.dom.Line("\\override StaffSymbol #'staff-space = #(magstep -1)",
                piano.getWith())

            # Nice to add Mark engravers
            ly.dom.Line('\\consists "Mark_engraver"', rightStaff.getWith())
            ly.dom.Line('\\consists "Metronome_mark_engraver"', rightStaff.getWith())

            # Keep piano reduction out of the MIDI output
            if builder.midi:
                ly.dom.Line('\\remove "Staff_performer"', rightStaff.getWith())
                ly.dom.Line('\\remove "Staff_performer"', leftStaff.getWith())

        # Create MIDI files if desired
        if self.rehearsalMidi.isChecked():
            a = data.assign('rehearsalMidi')
            rehearsalMidi = a.name

            func = ly.dom.SchemeList(a)
            func.pre = '#\n(' # hack
            ly.dom.Text('define-music-function', func)
            ly.dom.Line('(parser location name midiInstrument lyrics) '
                 '(string? string? ly:music?)', func)
            choir = ly.dom.Sim(ly.dom.Command('unfoldRepeats', ly.dom.SchemeLily(func)))

            data.afterblocks.append(ly.dom.Comment(_("Rehearsal MIDI files:")))

            for voice, num, ref, lyrName in rehearsalMidis:
                # Append voice to the rehearsalMidi function
                name = voice2id[voice] + str(num or '')
                seq = ly.dom.Seq(ly.dom.Voice(name, parent=ly.dom.Staff(name, parent=choir)))
                if builder.lyVersion < (2, 18, 0):
                    ly.dom.Text('<>\\f', seq) # add one dynamic
                ly.dom.Identifier(ref, seq) # add the reference to the voice

                book = ly.dom.Book()

                # Append score to the aftermath (stuff put below the main score)
                suffix = "choir{0}-{1}".format(data.num, name) if data.num else name
                if builder.lyVersion < (2, 12, 0):
                    data.afterblocks.append(
                        ly.dom.Line('#(define output-suffix "{0}")'.format(suffix)))
                else:
                    ly.dom.Line('\\bookOutputSuffix "{0}"'.format(suffix), book)
                data.afterblocks.append(book)
                data.afterblocks.append(ly.dom.BlankLine())
                score = ly.dom.Score(book)

                # TODO: make configurable
                midiInstrument = voice2Midi[voice]

                cmd = ly.dom.Command(rehearsalMidi, score)
                ly.dom.QuotedString(name, cmd)
                ly.dom.QuotedString(midiInstrument, cmd)
                ly.dom.Identifier(refs[(lyrName, allStanzas[0])], cmd)
                ly.dom.Midi(score)

            ly.dom.Text("\\context Staff = $name", choir)
            seq = ly.dom.Seq(choir)
            ly.dom.Line("\\set Score.midiMinimumVolume = #0.5", seq)
            ly.dom.Line("\\set Score.midiMaximumVolume = #0.5", seq)
            ly.dom.Line("\\set Score.tempoWholesPerMinute = #" + data.scoreProperties.schemeMidiTempo(), seq)
            ly.dom.Line("\\set Staff.midiMinimumVolume = #0.8", seq)
            ly.dom.Line("\\set Staff.midiMaximumVolume = #1.0", seq)
            ly.dom.Line("\\set Staff.midiInstrument = $midiInstrument", seq)
            lyr = ly.dom.Lyrics(parent=choir)
            lyr.getWith()['alignBelowContext'] = ly.dom.Text('$name')
            ly.dom.Text("\\lyricsto $name $lyrics", lyr)



lyricStyles = (
    (lambda: _("All voices same lyrics"),
        lambda: _("A set of the same lyrics is placed between all staves.")),
    (lambda: _("Every voice same lyrics"),
        lambda: _("Every voice gets its own lyrics, using the same text as the"
                  " other voices.")),
    (lambda: _("Every voice different lyrics"),
        lambda: _("Every voice gets a different set of lyrics.")),
    (lambda: _("Distribute stanzas"),
        lambda: _("One set of stanzas is distributed across the staves.")),
)

voice2Voice = {
    'S': SopranoVoice,
    'A': AltoVoice,
    'T': TenorVoice,
    'B': BassVoice,
}

voice2id = {
    'S': 'soprano',
    'A': 'alto',
    'T': 'tenor',
    'B': 'bass',
}

voice2Midi = {
    'S': 'soprano sax',
    'A': 'soprano sax',
    'T': 'tenor sax',
    'B': 'tenor sax',
}

register(
    lambda: _("Vocal"),
    [
        LeadSheet,
        SopranoVoice,
        MezzoSopranoVoice,
        AltoVoice,
        TenorVoice,
        BassVoice,
        Choir,
    ])

