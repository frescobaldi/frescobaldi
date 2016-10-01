"""
Elements that can be inserted by MIDI events
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

import ly.pitch


class Note:
    LastPitch = ly.pitch.Pitch()
    
    def __init__(self, midinote, notemapping):
        # get correct note 0...11 = c...b
        # and octave corresponding to octave modifiers ',' & '''
        self._midinote = midinote
        octave, note = divmod(midinote, 12)
        octave -= 4
        self._pitch = ly.pitch.Pitch(notemapping[note][0] % 7, notemapping[note][1], octave + notemapping[note][0] // 7)
    
    def output(self, relativemode=False, language='nederlands'):
        if relativemode:
            pitch = self._pitch.copy()
            pitch.makeRelative(Note.LastPitch)
            Note.LastPitch.note = self._pitch.note
            Note.LastPitch.octave = self._pitch.octave
        else:
            pitch = self._pitch
        # also octavecheck if Shift is held
        return pitch.output(language) + (('='+ly.pitch.octaveToString(self._pitch.octave)) if QApplication.keyboardModifiers() & Qt.SHIFT else '')
    
    def midinote(self):
        return self._midinote


class Chord(object):
    def __init__(self):
        self._notes = list()
        
    def add(self, note):
        self._notes.append(note)
    
    def output(self, relativemode=False, language='nederlands'):
        if len(self._notes) == 1:    # only one note, no chord
            return self._notes[0].output(relativemode, language)
        else:    # so we have a chord, print <chord>
            sortednotes = sorted(self._notes, key=lambda note: note.midinote())
            chord = ''
            # temporary variables, to reset LastPitch after this chord
            lastnote = sortednotes[0]._pitch.note
            lastoctave = sortednotes[0]._pitch.octave
            for n in sortednotes:
                chord += n.output(relativemode, language) + ' '
            Note.LastPitch.note = lastnote
            Note.LastPitch.octave = lastoctave
            return '<' + chord[:-1] + '>'    # strip last space


class NoteMappings:
    def to_sharp(self, note, alteration):
        if alteration==0.5:
            return (note, alteration)
        return (note-1, 0.5)

    def to_flat(self, note, alteration):
        if alteration==-0.5:
            return (note, alteration)
        return (note+1, -0.5)

    def __init__(self):
        self.key_order_sharp = [6, 1, 8, 3, 10, 5, 0]
        self.key_order_flat = [10, 3, 8, 1, 6, 11, 4]

        # Transform: midinote (0-11) -> (note, accidental)
        self.sharps = [(0, 0),    # c
                       (0, 0.5),  # cis
                       (1, 0),    # d
                       (1, 0.5),  # dis
                       (2, 0),    # e
                       (3, 0),    # f
                       (3, 0.5),  # fis
                       (4, 0),    # g
                       (4, 0.5),  # gis
                       (5, 0),    # a
                       (5, 0.5),  # ais
                       (6, 0)]    # b

        self.flats = [(0, 0),     # c
                      (1, -0.5),  # des
                      (1, 0),     # d
                      (2, -0.5),  # es
                      (2, 0),     # e
                      (3, 0),     # f
                      (4, -0.5),  # ges
                      (4, 0),     # g
                      (5, -0.5),  # aes
                      (5, 0),     # a
                      (6, -0.5),  # bes
                      (6, 0)]     # b
        # Construct all possible mappings using some replacement logic
        # 7 flats, ... 1 flats, 0, 1 sharp, ..., 7 sharps

        self.sharp_mappings = []
        self.flat_mappings = []
        for i in range(len(self.key_order_flat)-1, -1, -1):
            flatmap = list(self.flats) # copy existing list
            sharpmap = list(self.sharps) # copy existing list
            for k in self.key_order_flat[:i+1]:
                flatmap[k] = self.to_flat(*flatmap[k])
                sharpmap[k] = self.to_flat(*sharpmap[k])
            self.flat_mappings.append(flatmap)
            self.sharp_mappings.append(sharpmap)
    
        self.sharp_mappings.append(self.sharps) # Append C major signature -> no key alteration
        self.flat_mappings.append(self.flats) # Append C major signature -> no key alteration

        for i in range(len(self.key_order_sharp)):
            flatmap = list(self.flats) # copy existing list
            sharpmap = list(self.sharps) # copy existing list
            for k in self.key_order_sharp[:i+1]:
                flatmap[k] = self.to_sharp(*flatmap[k])
                sharpmap[k] = self.to_sharp(*sharpmap[k])
            self.flat_mappings.append(flatmap)
            self.sharp_mappings.append(sharpmap)

class NoteMapping:
    mappings = NoteMappings()

    def __init__(self, keysignature, sharps=True):
        if sharps:
            self.mapping = NoteMapping.mappings.sharp_mappings[keysignature]
        else:
            self.mapping = NoteMapping.mappings.flat_mappings[keysignature]

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, index):
        return self.mapping[index]
