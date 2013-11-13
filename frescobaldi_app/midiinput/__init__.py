"""
MIDI input package
provides a dock which allows to capture midi events and insert notes

- input is static, not dynamic
- special midi events (e. g. damper pedal) can modify notes (e. g. duration)
  or insert elements (e. g. slurs)
 
current limitations:
- outputs only absolute notes
- special events not implemented yet

TODO:
  chord mode
  dynamic input
"""

import time
import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import midihub
import midifile.event
import midifile.parser
import ly.pitch


class MidiIn:
    def __init__(self, widget):
        self._widget = weakref.ref(widget)
        self._portmidiinput = None
    
    def widget(self):
        return self._widget()
    
    def open(self):
        s = QSettings()
        self._portname = s.value("midi/input_port", midihub.default_input(), type(""))
        self._pollingtime = s.value("midi/polling_time", 10, int)
        self._portmidiinput = midihub.input_by_name(self._portname)
        
        self._listener = Listener(self._portmidiinput, self._pollingtime)
        QObject.connect(self._listener, SIGNAL("caughtevent"), self.analyzeevent)
    
    def close(self):
        # self._portmidiinput.close()
        # this will end in segfault with pyportmidi 0.0.7 in ubuntu
        # see https://groups.google.com/d/msg/pygame-mirror-on-google-groups/UA16GbFsUDE/RkYxb9SzZFwJ
        # so we cleanup ourself and invoke __dealloc__() by garbage collection
        # so discard any reference to a pypm.Input instance
        self._portmidiinput._input = None
        self._portmidiinput = None
        del self._listener
    
    def capture(self):
        if not self._portmidiinput:
            self.open()
        self._listener.start()
    
    def capturestop(self):
        self._listener.stop()
        if not self._listener.isFinished():
            self._listener.wait()
        self.close()
    
    def analyzeevent(self, event):
        if isinstance(event, midifile.event.NoteEvent):
            self.noteevent(event.type, event.channel, event.note, event.value)
    
    def noteevent(self, notetype, channel, notenumber, value):
        targetchannel = self.widget().channel()
        if channel == targetchannel or targetchannel == 0:    # '0' captures all
            if notetype == 9 and value > 0:    # note on with velocity > 0
                if self.widget().accidentals() == 0:
                    # sharps
                    notemapping = notemapping_sharps
                else:
                    # flats
                    notemapping = notemapping_flats
                # get correct note 0...11 = c...b
                # and octave corresponding to octave modifiers ',' & '''
                octave, note = divmod(notenumber, 12)
                octave -= 4
                pitch = ly.pitch.Pitch(notemapping[note][0], notemapping[note][1], octave)
                cursor = self.widget().mainwindow().textCursor()
                # check if there is a space before cursor or beginning of line
                posinblock = cursor.position() - cursor.block().position()
                charbeforecursor = cursor.block().text()[posinblock-1:posinblock]
                if charbeforecursor.isspace() or cursor.atBlockStart():
                    insertion = pitch.output()
                else:
                    insertion = ' ' +  pitch.output()
                cursor.insertText(insertion)
    
class Listener(QThread):
    def __init__(self, portmidiinput, pollingtime):
        QThread.__init__(self)
        self._portmidiinput = portmidiinput
        self._pollingtime = pollingtime
    
    def run(self):
        self._capturing = True
        while self._capturing:
            while not self._portmidiinput.poll():
                time.sleep(self._pollingtime/1000.)
                if not self._capturing:
                    break
            if not self._capturing:
                break
            data = self._portmidiinput.read(1)
            
            # midifile.parser.parse_midi_events is a generator which expects a long "byte string" from a file,
            # so we feed it one. But since it's just one event, we only need the first "generated" element.
            # First bytes are time, which are unnecessary in our case, so we feed a dummy byte "chr(77)"
            # and strip output by just using [1]. 77 is chosen randomly ;)
            s = chr(77) + chr(data[0][0][0]) + chr(data[0][0][1]) + chr(data[0][0][2]) + chr(data[0][0][3])
            event = next(midifile.parser.parse_midi_events(s))[1]
            
            self.emit(SIGNAL("caughtevent"), event)
    
    def stop(self):
        self._capturing = False


notemapping_sharps = [(0, 0),    # c
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

notemapping_flats = [(0, 0),     # c
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
