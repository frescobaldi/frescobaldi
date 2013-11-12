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
        
        self._labelaccidentals = QLabel()
        self._accidentals = QComboBox()
        self._accidentals.addItems(['sharps', 'flats'])
        
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
        grid.addWidget(self._accidentals, 1, 1)
        grid.addWidget(self._labeldamper, 2, 0)
        grid.addWidget(self._damper, 2, 1)
        grid.addWidget(self._labelsostenuto, 3, 0)
        grid.addWidget(self._sostenuto, 3, 1)
        grid.addWidget(self._labelsoft, 4, 0)
        grid.addWidget(self._soft, 4, 1)
        
        layout.addWidget(self._capture)
        
        app.translateUI(self)
    
    def mainwindow(self):
        return self._dockwidget().mainwindow()
    
    def channel(self):
        return self._midichannel.currentIndex()
    
    def accidentals(self):
        return self._accidentals.currentIndex()
    
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
        self._labelaccidentals.setText(_("Accidentals"))
        self._labeldamper.setText(_("Damper pedal"))
        self._labelsostenuto.setText(_("Sostenuto pedal"))
        self._labelsoft.setText(_("Soft pedal"))
