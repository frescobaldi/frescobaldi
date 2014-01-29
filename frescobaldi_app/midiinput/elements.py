"""
Elements that can bei inserted by MIDI events
"""

import ly.pitch


class Note:
    def __init__(self, midinote, notemapping):
        # get correct note 0...11 = c...b
        # and octave corresponding to octave modifiers ',' & '''
        self._midinote = midinote
        self._octave, self._note = divmod(midinote, 12)
        self._octave -= 4
        self._pitch = ly.pitch.Pitch(notemapping[self._note][0], notemapping[self._note][1], self._octave)
    
    def output(self, language='nederlands'):
        return self._pitch.output(language)
    
    def midinote(self):
        return self._midinote


class Chord:
    def __init__(self):
        self._notes = list()
        
    def add(self, note):
        self._notes.append(note)
    
    def output(self, language='nederlands'):
        if len(self._notes) == 1:    # only one note, no chord
            return self._notes[0].output(language)
        else:    # so we have a chord, print <chord>
            sortednotes = sorted(self._notes, key=lambda note: note.midinote())
            chord = ''
            for n in sortednotes:
                chord += n.output(language) + ' '
            return '<' + chord[:-1] + '>'    # strip last space


class NoteMappings:
    def __init__(self):
        self.key_order_sharp = [6, 1, 8, 3, 10, 5, 0]
        self.key_order_flat = [10, 3, 8, 1, 6, 11, 4]

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

        # keysignature with sharps and flat accidentals
        self.flat_mappings = [self.flats]
        for i in range(len(self.key_order_sharp)):
            mapping = list(self.flats) # copy existing list
            for k in self.key_order_sharp[:i+1]:
                n = mapping[k][0]
                mapping[k] = (n-1 if k > 0 else 11, 0.5)
            self.flat_mappings.append(mapping)

        # keysignature with flatss and sharp accidentals
        self.sharp_mappings = []
        for i in range(len(self.key_order_flat)):
            mapping = list(self.sharps) # copy existing list
            for k in self.key_order_flat[:i+1]:
                n = mapping[k][0]
                mapping[k] = (n+1 if k < 11 else 0, -0.5)
            self.sharp_mappings.append(mapping)

class NoteMapping:
    mappings = NoteMappings()

    def __init__(self, keysignature, sharps=True):
        if keysignature >= 0:
            if sharps:
                self.mapping = NoteMapping.mappings.sharps
            else:
                self.mapping = NoteMapping.mappings.flat_mappings[keysignature]
        else:
            if sharps:
                self.mapping = NoteMapping.mappings.sharp_mappings[-keysignature-1]
            else:
                self.mapping = NoteMapping.mappings.flats

    def __len__(self):
        return len(self.mapping)

    def __getitem__(self, index):
        return self.mapping[index]
