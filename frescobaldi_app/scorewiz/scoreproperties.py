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
Properties of a score:
- key signature
- time signature
- pickup beat
- metronome value [note]=[time][tap]
- tempo indication
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class ScoreProperties(object):
    """This is only the base class, it should be mixed in with a widget or a different way."""
    
    # Key signature
    def createKeySignatureWidget(self):
        self.keySignatureLabel = QLabel()
        self.keyNote = QComboBox()
        self.keyNote.setModel(KeyNoteModel(self.keyNote))
        self.keyMode = QComboBox()
        self.keyMode.setModel(KeyModeModel(self.keyMode))

    def translateKeySignatureWidget(self):
        self.keySignatureLabel.setText(_("Key signature:"))
        self.keyMode.update()
    
    def layoutKeySignature(self, layout):
        """Adds our widgets to a layout, assuming it is a QVBoxLayout."""
        box = QHBoxLayout()
        box.addWidget(self.keySignatureLabel)
        box.addWidget(self.keyNote)
        box.addWidget(self.keyMode)
        layout.addLayout(box)

    def setPitchNameLanguage(self, language='nederlands'):
        self.keyNote.model().language = language
        self.keyNote.update()
        
    # Time signature
    def createTimeSignatureWidget(self):
        self.timeSignatureLabel = QLabel()
        self.timeSignature = QComboBox()
        self.timeSignature.setModel(TimeSignatureModel(self.timeSignature))
    
    def translateTimeSignatureWidget(self):
        self.timeSignatureLabel.setText(_("Time signature:"))
    
    def layoutTimeSignature(self, layout):
        """Adds our widgets to a layout, assuming it is a QVBoxLayout."""
        box = QHBoxLayout()
        box.addWidget(self.timeSignatureLabel)
        box.addWidget(self.timeSignature)
        layout.addLayout(box)


    # Pickup bar
    def createPickupWidget(self):
        self.pickupLabel = QLabel()
        self.pickup = QComboBox()
        self.pickup.setModel(PickupModel(self.pickup))
        
    def translatePickupWidget(self):
        self.pickup.update()
        
    def layoutPickup(self, layout):
        box = QHBoxLayout()
        box.addWidget(self.pickupLabel)
        box.addWidget(self.pickup)
        layout.addLayout(box)
        
    # Metronome value
    
    
    
    
class KeyNoteModel(QAbstractListModel):
    language = 'nederlands'
    def rowCount(self, parent):
        return 17
        
    def data(self, index, role):
        if role == Qt.DisplayRole:
            return keyNames[self.language][index.row()]


class KeyModeModel(QAbstractListModel):
    def rowCount(self, parent):
        return len(modes)
    
    def data(self, index, role):
        if role == Qt.DisplayRole:
            return modes[index.row()][1]()


class TimeSignatureModel(QAbstractListModel):
    _data = (
        '(4/4)', '(2/2)', # with symbols
        '2/4', '3/4', '4/4', '5/4', '6/4', '7/4',
        '2/2', '3/2', '4/2',
        '3/8', '5/8', '6/8', '7/8', '8/8', '9/8', '12/8',
        '3/16', '6/16', '12/16',
        '3+2/8', '3/4+3/8',
    )
    def rowCount(self, parent):
        return len(self._data)
    
    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()]
        elif role == Qt.DecorationRole:
            if index.row() == 0:
                return symbols.icon('time_c44')
            elif index.row() == 1:
                return symbols.icon('time_c22')
            



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
