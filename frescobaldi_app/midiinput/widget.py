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
        self._midichannel.addItems(['all']+[str(i) for i in range(1,17)])
        
        self._labelkeysignature = QLabel()
        self._keysignature = QComboBox()
        
        self._labelaccidentals = QLabel()
        self._accidentals = QComboBox()
        
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
        grid.addWidget(self._labelkeysignature, 1, 0)
        grid.addWidget(self._keysignature, 1, 1)
        grid.addWidget(self._labelaccidentals, 2, 0)
        grid.addWidget(self._accidentals, 2, 1)
        grid.addWidget(self._labelchordmode, 3, 0)
        grid.addWidget(self._chordmode, 3, 1)
        grid.addWidget(self._labeldamper, 4, 0)
        grid.addWidget(self._damper, 4, 1)
        grid.addWidget(self._labelsostenuto, 5, 0)
        grid.addWidget(self._sostenuto, 5, 1)
        grid.addWidget(self._labelsoft, 6, 0)
        grid.addWidget(self._soft, 6, 1)
        
        layout.addWidget(self._capture)
        
        app.translateUI(self)
    
    def mainwindow(self):
        return self._dockwidget().mainwindow()
    
    def channel(self):
        return self._midichannel.currentIndex()
    
    def keysignature(self):
        return self._keysignature.currentIndex()-7
    
    def accidentals(self):
        return self._accidentals.currentIndex()
    
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
        self._labelkeysignature.setText(_("Key signature"))
        self._keysignature.addItems([
            _("Ces major (7 flats)"),
            _("Ges major (6 flats)"),
            _("Des major (5 flats)"),
            _("Aes major (4 flats)"),
            _("Ees major (3 flats)"),
            _("Bes major (2 flats)"),
            _("F major (1 flat)"),
            _("no key"),
            _("G major (1 sharp)"),
            _("D major (2 sharps)"),
            _("A major (3 sharps)"),
            _("E major (4 sharps)"),
            _("B major (5 sharps)"),
            _("Fis major (6 sharps)"),
            _("Cis major (7 sharps)")
            ])
        self._keysignature.setCurrentIndex(7)
        self._labelaccidentals.setText(_("Accidentals"))
        self._accidentals.addItems([_("sharps"), _("flats")])
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
