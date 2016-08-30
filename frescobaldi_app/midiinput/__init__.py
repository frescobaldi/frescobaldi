"""
MIDI input package
provides a dock which allows to capture midi events and insert notes

- input is static, not dynamic
- special midi events (e. g. damper pedal) can modify notes (e. g. duration)
  or insert elements (e. g. slurs)
 
current limitations:
- special events not implemented yet

TODO:
  dynamic input
"""

import time
import weakref

from PyQt5.QtCore import QObject, QSettings, QThread, pyqtSignal

import midihub
import midifile.event
import midifile.parser
import documentinfo

from . import elements


class MidiIn(object):
    def __init__(self, widget):
        self._widget = weakref.ref(widget)
        self._portmidiinput = None
        self._listener = None
        self._chord = None
    
    def __del__(self):
        if isinstance(self._listener, Listener):
            self.capturestop()
    
    def widget(self):
        return self._widget()
    
    def open(self):
        s = QSettings()
        self._portname = s.value("midi/midi/input_port", midihub.default_input(), str)
        self._pollingtime = s.value("midi/polling_time", 10, int)
        self._portmidiinput = midihub.input_by_name(self._portname)
        
        self._listener = Listener(self._portmidiinput, self._pollingtime)
        self._listener.NoteEventSignal.connect(self.analyzeevent)
    
    def close(self):
        # self._portmidiinput.close()
        # this will end in segfault with pyportmidi 0.0.7 in ubuntu
        # see https://groups.google.com/d/msg/pygame-mirror-on-google-groups/UA16GbFsUDE/RkYxb9SzZFwJ
        # so we cleanup ourself and invoke __dealloc__() by garbage collection
        # so discard any reference to a pypm.Input instance
        if self._portmidiinput:
            self._portmidiinput._input = None
        self._portmidiinput = None
        self._listener = None
    
    def capture(self):
        if not self._portmidiinput:
            self.open()
            if not self._portmidiinput:
                return
        doc = self.widget().mainwindow().currentDocument()
        self._language = documentinfo.docinfo(doc).language() or 'nederlands'
        self._activenotes = 0
        self._listener.start()
    
    def capturestop(self):
        self._listener.stop()
        if not self._listener.isFinished():
            self._listener.wait()
        self._activenotes = 0
        self.close()
    
    def analyzeevent(self, event):
        if isinstance(event, midifile.event.NoteEvent):
            self.noteevent(event.type, event.channel, event.note, event.value)
    
    def noteevent(self, notetype, channel, notenumber, value):
        targetchannel = self.widget().channel()
        if channel == targetchannel or targetchannel == 0:    # '0' captures all
            if notetype == 9 and value > 0:    # note on with velocity > 0
                notemapping = elements.NoteMapping(self.widget().keysignature(), self.widget().accidentals()=='sharps')
                note = elements.Note(notenumber, notemapping)
                if self.widget().chordmode():
                    if not self._chord:    # no Chord instance?
                        self._chord = elements.Chord()
                    self._chord.add(note)
                    self._activenotes += 1
                else:
                    self.printwithspace(note.output(self.widget().relativemode(), self._language))
            elif (notetype == 8 or (notetype == 9 and value == 0)) and self.widget().chordmode():
                self._activenotes -= 1
                if self._activenotes <= 0:    # activenotes could get negative under strange conditions
                    if self._chord:
                        self.printwithspace(self._chord.output(self.widget().relativemode(), self._language))
                    self._activenotes = 0    # reset in case it was negative
                    self._chord = None
    
    def printwithspace(self, text):
        cursor = self.widget().mainwindow().textCursor()
        # check if there is a space before cursor or beginning of line
        posinblock = cursor.position() - cursor.block().position()
        charbeforecursor = cursor.block().text()[posinblock-1:posinblock]
        if charbeforecursor.isspace() or cursor.atBlockStart():
            cursor.insertText(text)
        else:
            cursor.insertText(' ' +  text)
    
class Listener(QThread):
    NoteEventSignal = pyqtSignal(midifile.event.NoteEvent)
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
            # First byte is time, which is unnecessary in our case, so we feed a dummy byte 77
            # and strip output by just using [1]. 77 is chosen randomly ;)
            s = bytearray([77, data[0][0][0], data[0][0][1], data[0][0][2], data[0][0][3]])
            event = next(midifile.parser.parse_midi_events(s))[1]
            
            self.NoteEventSignal.emit(event)
    
    def stop(self):
        self._capturing = False
