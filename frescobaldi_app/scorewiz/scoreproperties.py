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
Properties of a score:
- key signature
- time signature
- pickup beat
- metronome value [note]=[time][tap]
- tempo indication
"""


import fractions
import re

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel)

import ly.dom
import completionmodel
import listmodel
import symbols
import widgets.lineedit
import widgets.tempobutton


class ScoreProperties(object):
    """This is only the base class, it should be mixed in with a widget or a different way."""

    def createWidgets(self):
        """Creates all widgets."""
        self.createKeySignatureWidget()
        self.createTimeSignatureWidget()
        self.createPickupWidget()
        self.createMetronomeWidget()
        self.createTempoWidget()

    def layoutWidgets(self, layout):
        """Adds all widgets to a vertical layout."""
        self.layoutKeySignatureWidget(layout)
        self.layoutTimeSignatureWidget(layout)
        self.layoutPickupWidget(layout)
        self.layoutMetronomeWidget(layout)
        self.layoutTempoWidget(layout)

    def translateWidgets(self):
        self.translateKeySignatureWidget()
        self.translateTimeSignatureWidget()
        self.translatePickupWidget()
        self.tranlateMetronomeWidget()
        self.translateTempoWidget()

    def ly(self, node, builder):
        """Adds appropriate LilyPond command nodes to the parent node.

        Settings from the builder are used where that makes sense.
        All widgets must be present.

        """
        self.lyKeySignature(node, builder)
        self.lyTimeSignature(node, builder)
        self.lyPickup(node, builder)
        self.lyTempo(node, builder)

    def globalSection(self, builder):
        """Returns a sequential expression between { } containing the output of ly()."""
        seq = ly.dom.Seq()
        self.ly(seq, builder)
        return seq

    # Key signature
    def createKeySignatureWidget(self):
        self.keySignatureLabel = QLabel()
        self.keyNote = QComboBox()
        self.keyNote.setModel(listmodel.ListModel(keyNames['nederlands'], self.keyNote))
        self.keyMode = QComboBox()
        self.keyMode.setModel(listmodel.ListModel(modes, self.keyMode, display=listmodel.translate_index(1)))
        self.keySignatureLabel.setBuddy(self.keyNote)

    def translateKeySignatureWidget(self):
        self.keySignatureLabel.setText(_("Key signature:"))
        self.keyMode.model().update()

    def layoutKeySignatureWidget(self, layout):
        """Adds our widgets to a layout, assuming it is a QVBoxLayout."""
        box = QHBoxLayout()
        box.addWidget(self.keySignatureLabel)
        box.addWidget(self.keyNote)
        box.addWidget(self.keyMode)
        layout.addLayout(box)

    def setPitchLanguage(self, language='nederlands'):
        self.keyNote.model()._data = keyNames[language or 'nederlands']
        self.keyNote.model().update()

    def lyKeySignature(self, node, builder):
        """Adds the key signature to the ly.dom node parent."""
        note, alter = keys[self.keyNote.currentIndex()]
        alter = fractions.Fraction(alter, 2)
        mode = modes[self.keyMode.currentIndex()][0]
        ly.dom.KeySignature(note, alter, mode, node).after = 1

    # Time signature
    def createTimeSignatureWidget(self):
        self.timeSignatureLabel = QLabel()
        self.timeSignature = QComboBox(editable=True)
        icons = {
            '(4/4)': symbols.icon('time_c44'),
            '(2/2)': symbols.icon('time_c22'),
        }
        self.timeSignature.setModel(listmodel.ListModel(timeSignaturePresets, self.timeSignature,
            icon=icons.get))
        self.timeSignature.setCompleter(None)
        self.timeSignatureLabel.setBuddy(self.timeSignature)

    def translateTimeSignatureWidget(self):
        self.timeSignatureLabel.setText(_("Time signature:"))

    def layoutTimeSignatureWidget(self, layout):
        """Adds our widgets to a layout, assuming it is a QVBoxLayout."""
        box = QHBoxLayout()
        box.addWidget(self.timeSignatureLabel)
        box.addWidget(self.timeSignature)
        layout.addLayout(box)

    def lyTimeSignature(self, node, builder):
        """Adds the time signature to the ly.dom node parent."""
        sig = self.timeSignature.currentText().strip()
        if '+' in sig:
            pass # TODO: implement support for \compoundMeter
        else:
            if sig == '(2/2)':
                ly.dom.TimeSignature(2, 2, node).after = 1
            elif sig == '(4/4)':
                ly.dom.TimeSignature(4, 4, node).after = 1
            else:
                match = re.search(r'(\d+).*?(\d+)', sig)
                if match:
                    if builder.lyVersion >= (2, 11, 44):
                        ly.dom.Line(r"\numericTimeSignature", node)
                    else:
                        ly.dom.Line(r"\override Staff.TimeSignature #'style = #'()", node)
                    num, beat = map(int, match.group(1, 2))
                    ly.dom.TimeSignature(num, beat, node).after = 1

    # Pickup bar
    def createPickupWidget(self):
        self.pickupLabel = QLabel()
        self.pickup = QComboBox()
        pickups = ['']
        pickups.extend(durations)
        self.pickup.setModel(listmodel.ListModel(pickups, self.pickup,
            display = lambda item: item or _("None"),
            icon = lambda item: symbols.icon('note_{0}'.format(item.replace('.', 'd'))) if item else None))
        self.pickup.view().setIconSize(QSize(22, 22))
        self.pickupLabel.setBuddy(self.pickup)

    def translatePickupWidget(self):
        self.pickupLabel.setText(_("Pickup measure:"))
        self.pickup.model().update()

    def layoutPickupWidget(self, layout):
        box = QHBoxLayout()
        box.addWidget(self.pickupLabel)
        box.addWidget(self.pickup)
        layout.addLayout(box)

    def lyPickup(self, node, builder):
        if self.pickup.currentIndex() > 0:
            dur, dots = partialDurations[self.pickup.currentIndex() - 1]
            ly.dom.Partial(dur, dots, parent=node)

    # Metronome value
    def createMetronomeWidget(self):
        self.metronomeLabel = QLabel()
        self.metronomeNote = QComboBox()
        self.metronomeNote.setModel(listmodel.ListModel(durations, display=None,
            icon = lambda item: symbols.icon('note_{0}'.format(item.replace('.', 'd')))))
        self.metronomeNote.setCurrentIndex(durations.index('4'))
        self.metronomeNote.view().setIconSize(QSize(22, 22))
        self.metronomeEqualSign = QLabel('=')
        self.metronomeEqualSign.setFixedWidth(self.metronomeEqualSign.minimumSizeHint().width())
        self.metronomeValue = QComboBox(editable=True)
        self.metronomeValue.setModel(listmodel.ListModel(metronomeValues, self.metronomeValue,
            display=format))
        self.metronomeValue.setCompleter(None)
        self.metronomeValue.setValidator(QIntValidator(0, 999, self.metronomeValue))
        self.metronomeValue.setCurrentIndex(metronomeValues.index(100))
        self.metronomeTempo = widgets.tempobutton.TempoButton()
        self.metronomeTempo.tempo.connect(self.setMetronomeValue)
        self.metronomeLabel.setBuddy(self.metronomeNote)
        self.metronomeRound = QCheckBox()


    def layoutMetronomeWidget(self, layout):
        grid = QGridLayout()
        grid.addWidget(self.metronomeLabel, 0, 0)

        box = QHBoxLayout(spacing=0)
        box.addWidget(self.metronomeNote)
        box.addWidget(self.metronomeEqualSign)
        box.addWidget(self.metronomeValue)
        box.addWidget(self.metronomeTempo)
        grid.addLayout(box, 0, 1)

        grid.addWidget(self.metronomeRound, 1, 1)
        layout.addLayout(grid)

    def tranlateMetronomeWidget(self):
        self.metronomeLabel.setText(_("Metronome mark:"))
        self.metronomeRound.setText(_("Round tap tempo value"))
        self.metronomeRound.setToolTip(_(
            "Round the entered tap tempo to a common value."
            ))

    def setMetronomeValue(self, bpm):
        """ Tap the tempo tap button """
        if  self.metronomeRound.isChecked():
            l = [abs(t - bpm) for t in metronomeValues]
            m = min(l)
            if m < 6:
                self.metronomeValue.setCurrentIndex(l.index(m))

        else:
            self.metronomeValue.setEditText(str(bpm))

    # Tempo indication
    def createTempoWidget(self):
        self.tempoLabel = QLabel()
        self.tempo = widgets.lineedit.LineEdit()
        completionmodel.complete(self.tempo, "scorewiz/completion/scoreproperties/tempo")
        self.tempo.completer().setCaseSensitivity(Qt.CaseInsensitive)
        self.tempoLabel.setBuddy(self.tempo)

    def layoutTempoWidget(self, layout):
        box = QHBoxLayout()
        box.addWidget(self.tempoLabel)
        box.addWidget(self.tempo)
        layout.addLayout(box)

    def translateTempoWidget(self):
        self.tempoLabel.setText(_("Tempo indication:"))

    def lyTempo(self, node, builder):
        """Returns an appropriate tempo indication."""
        text = self.tempo.text().strip()
        if builder.showMetronomeMark:
            dur = durations[self.metronomeNote.currentIndex()]
            val = self.metronomeValue.currentText() or '60'
        elif text:
            dur = None
            val = None
        else:
            return
        tempo = ly.dom.Tempo(dur, val, node)
        if text:
            ly.dom.QuotedString(text, tempo)

    def lyMidiTempo(self, node):
        """Sets the configured tempo in the tempoWholesPerMinute variable."""
        node['tempoWholesPerMinute'] = ly.dom.Scheme(self.schemeMidiTempo())

    def schemeMidiTempo(self):
        """Returns a string with the tempo like '(ly:make-moment 100 4)' from the settings."""
        base, mul = midiDurations[self.metronomeNote.currentIndex()]
        val = int(self.metronomeValue.currentText() or '60') * mul
        return "(ly:make-moment {0} {1})".format(val, base)

    def lySimpleMidiTempo(self, node):
        r"""Return a simple \tempo x=y node for the currently set tempo."""
        dur = durations[self.metronomeNote.currentIndex()]
        val = self.metronomeValue.currentText() or '60'
        return ly.dom.Tempo(dur, val, node)


def metronomeValues():
    v, start = [], 40
    for end, step in (60, 2), (72, 3), (120, 4), (144, 6), (210, 8):
        v.extend(range(start, end, step))
        start = end
    return v
metronomeValues = metronomeValues()


timeSignaturePresets = (
    '(4/4)', '(2/2)', # with symbols
    '2/4', '3/4', '4/4', '5/4', '6/4', '7/4',
    '2/2', '3/2', '4/2',
    '3/8', '5/8', '6/8', '7/8', '8/8', '9/8', '12/8',
    '3/16', '6/16', '12/16',
    '3+2/8', '3/4+3/8',
)

# durations for pickup and metronome
durations = ('16', '16.', '8', '8.', '4', '4.', '2', '2.', '1', '1.')
midiDurations = ((16,1),(32,3),(8,1),(16,3),(4,1),(8,3),(2,1),(4,3),(1,1),(2,3))
partialDurations = ((4,0),(4,1),(3,0),(3,1),(2,0),(2,1),(1,0),(1,1),(0,0),(0,1))


keyNames = {
    'nederlands': (
        'C', 'Cis',
        'Des', 'D', 'Dis',
        'Es', 'E',
        'F', 'Fis',
        'Ges', 'G', 'Gis',
        'As', 'A', 'Ais',
        'Bes', 'B',
    ),
    'english': (
        'C', 'C#',
        'Db', 'D', 'D#',
        'Eb', 'E',
        'F', 'F#',
        'Gb', 'G', 'G#',
        'Ab', 'A', 'A#',
        'Bb', 'B',
    ),
    'deutsch': (
        'C', 'Cis',
        'Des', 'D', 'Dis',
        'Es', 'E',
        'F', 'Fis',
        'Ges', 'G', 'Gis',
        'As', 'A', 'Ais',
        'B', 'H',
    ),
    'norsk': (
        'C', 'Ciss',
        'Dess', 'D', 'Diss',
        'Ess', 'E',
        'F', 'Fiss',
        'Gess', 'G', 'Giss',
        'Ass', 'A', 'Aiss',
        'B', 'H',
    ),
    'italiano': (
        'Do', 'Do diesis',
        'Re bemolle', 'Re', 'Re diesis',
        'Mi bemolle', 'Mi',
        'Fa', 'Fa diesis',
        'Sol bemolle', 'Sol', 'Sol diesis',
        'La bemolle', 'La', 'La diesis',
        'Si bemolle', 'Si',
    ),
    'espanol': (
        'Do', 'Do sostenido',
        'Re bemol', 'Re', 'Re sostenido',
        'Mi bemol', 'Mi',
        'Fa', 'Fa sostenido',
        'Sol bemol', 'Sol', 'Sol sostenido',
        'La bemol', 'La', 'La sostenido',
        'Si bemol', 'Si',
    ),
    'vlaams': (
        'Do', 'Do kruis',
        'Re mol', 'Re', 'Re kruis',
        'Mi mol', 'Mi',
        'Fa', 'Fa kruis',
        'Sol mol', 'Sol', 'Sol kruis',
        'La mol', 'La', 'La kruis',
        'Si mol', 'Si',
    ),
}
keyNames['svenska'] = keyNames['norsk']
keyNames['suomi'] = keyNames['deutsch']
keyNames['catalan'] = keyNames['italiano']
keyNames['portugues'] = keyNames['espanol']

keys = (
    (0, 0), (0, 1),
    (1, -1), (1, 0), (1, 1),
    (2, -1), (2, 0),
    (3, 0), (3, 1),
    (4, -1), (4, 0), (4, 1),
    (5, -1), (5, 0), (5, 1),
    (6, -1), (6, 0),
)

modes = (
    ('major',       lambda: _("Major")),
    ('minor',       lambda: _("Minor")),
    ('ionian',      lambda: _("Ionian")),
    ('dorian',      lambda: _("Dorian")),
    ('phrygian',    lambda: _("Phrygian")),
    ('lydian',      lambda: _("Lydian")),
    ('mixolydian',  lambda: _("Mixolydian")),
    ('aeolian',     lambda: _("Aeolian")),
    ('locrian',     lambda: _("Locrian")),
)

