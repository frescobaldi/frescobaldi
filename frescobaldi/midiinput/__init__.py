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

import re
from PyQt6.QtGui import QTextCursor

import time
import weakref

from PyQt6.QtCore import QObject, QThread, pyqtSignal

import app
import midihub
import midifile.event
import midifile.parser
import documentinfo

from . import elements

# What this does was originally undocumented. It appears intended to match
# chord and pitch names, but not commands or variables (thanks @ksnortum)
LY_REG_EXPR = re.compile(
    r'(?<![a-zA-Z#_^\-\\])[a-ps-zA-PS-Z]{1,3}(?![a-zA-Z])[\'\,]*'
    '|'
    r'(?<![<\\])<[^<>]*>(?!>)'
)

# Event codes from the MIDI specification
NOTE_OFF_EVENT = 8
NOTE_ON_EVENT = 9


class MidiIn:
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
        # needed because close() does not reliably do its job
        midihub.refresh_ports()

        s = app.settings("midi")
        portname = s.value("input_port", midihub.default_input(), str)
        pollingtime = s.value("polling_time", 10, int)
        self._portmidiinput = midihub.input_by_name(portname)

        self._listener = Listener(self._portmidiinput, pollingtime)
        self._listener.receivedNoteEvent.connect(self.analyzeEvent)

    def close(self):
        if self._portmidiinput:
            self._portmidiinput.close()
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

    def analyzeEvent(self, event):
        if isinstance(event, midifile.event.NoteEvent):
            self.processNoteEvent(event.type, event.channel, event.note, event.value)

    def processNoteEvent(self, notetype, channel, notenumber, value):
        targetchannel = self.widget().channel()
        if targetchannel == 0 or channel == targetchannel - 1:  # '0' captures all
            # midi channels start at 1 for humans and 0 for programs
            if notetype == NOTE_ON_EVENT and value > 0: # value gives the velocity
                notemapping = elements.NoteMapping(self.widget().keysignature(), self.widget().accidentals() == 'sharps')
                note = elements.Note(notenumber, notemapping)
                if self.widget().chordmode():
                    if not self._chord:    # no Chord instance?
                        self._chord = elements.Chord()
                    self._chord.add(note)
                    self._activenotes += 1
                else:
                    self.addToDocument(note.output(self.widget().relativemode(), self._language))
            elif ((notetype == NOTE_OFF_EVENT
                   or (notetype == NOTE_ON_EVENT and value == 0))
                  and self.widget().chordmode()):
                self._activenotes -= 1
                if self._activenotes <= 0:    # activenotes could get negative under strange conditions
                    if self._chord:
                        self.addToDocument(self._chord.output(self.widget().relativemode(), self._language))
                    self._activenotes = 0    # reset in case it was negative
                    self._chord = None

    def addToDocument(self, text):
        view = self.widget().mainwindow()
        cursor = view.textCursor()

        if self.widget().repitchmode():
              music = cursor.document().toPlainText()[cursor.position() : ]
              notes = LY_REG_EXPR.search(music)
              if notes is not None:
                    start = cursor.position() + notes.start()
                    end = cursor.position() + notes.end()

                    cursor.beginEditBlock()
                    cursor.setPosition(start)
                    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                    cursor.insertText(text)
                    cursor.endEditBlock()

                    view.setTextCursor(cursor)

        else:
              # check if there is a space before cursor or beginning of line
              posinblock = cursor.position() - cursor.block().position()
              charbeforecursor = cursor.block().text()[posinblock-1:posinblock]

              if charbeforecursor.isspace() or cursor.atBlockStart():
                   cursor.insertText(text)
              else:
                   cursor.insertText(' ' +  text)


class Listener(QThread):
    receivedNoteEvent = pyqtSignal(midifile.event.NoteEvent)

    def __init__(self, portmidiinput, pollingtime):
        super().__init__()
        self._portmidiinput = portmidiinput
        self._pollingtime = pollingtime

    def run(self):
        self._capturing = True
        while self._capturing:
            while not self._portmidiinput.poll():
                time.sleep(self._pollingtime / 1000.)
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

            if isinstance(event, midifile.event.NoteEvent):
                self.receivedNoteEvent.emit(event)

    def stop(self):
        self._capturing = False
