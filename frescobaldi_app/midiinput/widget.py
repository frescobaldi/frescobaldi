"""
MIDI input controls
"""

from __future__ import unicode_literals

import weakref

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app

import midiinput


class Widget(QWidget):
    def __init__(self, dockwidget):
        super(Widget, self).__init__(dockwidget)
        self._document = None
        self._midiin = midiinput.MidiIn(self)
        self._dockwidget = weakref.ref(dockwidget)
        
        self._labelmidichannel = QLabel()
        self._midichannel = QComboBox()
        
        self._labelaccidentals = QLabel()
        self._accidentalssharps = QRadioButton()
        self._accidentalsflats = QRadioButton()
        self._groupaccidentals = QGroupBox()
        self._groupaccidentals.setFlat(True)
        hbox = QHBoxLayout()
        self._groupaccidentals.setLayout(hbox)
        hbox.addWidget(self._accidentalssharps)
        hbox.addWidget(self._accidentalsflats)
        self._accidentalssharps.setChecked(True)
        
        self._labelchordmode = QLabel()
        self._chordmode = QCheckBox()
        
        self._labeldamper = QLabel()
        self._damper = QComboBox()
        
        self._labelsostenuto = QLabel()
        self._sostenuto = QComboBox()
        
        self._labelsoft = QLabel()
        self._soft = QComboBox()
        
        ac = self.parentWidget().actionCollection
        self._capture = QToolButton()
        self._capture.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._capture.setDefaultAction(ac.capture_start)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        grid = QGridLayout(spacing=0)
        layout.addLayout(grid)
        
        grid.addWidget(self._labelmidichannel, 0, 0)
        grid.addWidget(self._midichannel, 0, 1)
        grid.addWidget(self._labelaccidentals, 1, 0)
        grid.addWidget(self._groupaccidentals, 1, 1)
        grid.addWidget(self._labelchordmode, 2, 0)
        grid.addWidget(self._chordmode, 2, 1)
        grid.addWidget(self._labeldamper, 3, 0)
        grid.addWidget(self._damper, 3, 1)
        grid.addWidget(self._labelsostenuto, 4, 0)
        grid.addWidget(self._sostenuto, 4, 1)
        grid.addWidget(self._labelsoft, 5, 0)
        grid.addWidget(self._soft, 5, 1)
        
        layout.addWidget(self._capture)
        
        app.translateUI(self)
    
    def mainwindow(self):
        return self._dockwidget().mainwindow()
    
    def channel(self):
        return self._midichannel.currentIndex()
    
    def accidentals(self):
        if self._accidentalsflats.isChecked():
            return 'flats'
        else:
            return 'sharps'
    
    def chordmode(self):
        return self._chordmode.isChecked()
    
    def startcapturing(self):
        self._midiin.capture()
        ac = self.parentWidget().actionCollection
        while self._capture.actions():    # remove all old actions
            self._capture.removeAction(self._capture.actions()[0])
        self._capture.setDefaultAction(ac.capture_stop)
    
    def stopcapturing(self):
        self._midiin.capturestop()
        ac = self.parentWidget().actionCollection
        while self._capture.actions():    # remove all old actions
            self._capture.removeAction(self._capture.actions()[0])
        self._capture.setDefaultAction(ac.capture_start)

    def translateUI(self):
        self._labelmidichannel.setText(_("MIDI channel"))
        self._midichannel.addItems([_("all")]+[str(i) for i in range(1,17)])
        self._labelaccidentals.setText(_("Accidentals"))
        self._accidentalssharps.setText(_("sharps"))
        self._accidentalsflats.setText(_("flats"))
        self._labelchordmode.setText(_("Chord mode"))
        self._chordmode.setToolTip(_(
            "Enter simultaneously played notes as chords. "
            "See \"What's This\" for more information."))
        self._chordmode.setWhatsThis(_(
            "Notes which are played simultaneously are written "
            "as chords. As a consequence they are not written "
            "before the last key is lifted. Of course single "
            "can also be entered."))
        self._labeldamper.setText(_("Damper pedal"))
        self._labelsostenuto.setText(_("Sostenuto pedal"))
        self._labelsoft.setText(_("Soft pedal"))
