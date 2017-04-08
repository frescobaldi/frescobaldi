"""
MIDI input controls
"""


import weakref

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QRadioButton, QToolButton,
                             QVBoxLayout, QWidget)

import app

import midiinput


class Widget(QWidget):
    def __init__(self, dockwidget):
        super(Widget, self).__init__(dockwidget)
        self._document = None
        self._midiin = midiinput.MidiIn(self)
        self._dockwidget = weakref.ref(dockwidget)

        signals = list()

        self._labelmidichannel = QLabel()
        self._midichannel = QComboBox()
        signals.append(self._midichannel.currentIndexChanged)

        self._labelkeysignature = QLabel()
        self._keysignature = QComboBox()
        signals.append(self._keysignature.currentIndexChanged)

        self._labelaccidentals = QLabel()
        self._accidentalssharps = QRadioButton()
        signals.append(self._accidentalssharps.clicked)
        self._accidentalsflats = QRadioButton()
        signals.append(self._accidentalsflats.clicked)
        self._groupaccidentals = QGroupBox()
        self._groupaccidentals.setFlat(True)
        hbox = QHBoxLayout()
        self._groupaccidentals.setLayout(hbox)
        hbox.addWidget(self._accidentalssharps)
        hbox.addWidget(self._accidentalsflats)
        self._accidentalssharps.setChecked(True)

        self._chordmode = QCheckBox()
        signals.append(self._chordmode.clicked)

        self._relativemode = QCheckBox()
        signals.append(self._relativemode.clicked)

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
        self.addAction(ac.accidental_switch)

        self._notemode = QLabel()

        layout = QVBoxLayout()
        self.setLayout(layout)
        grid = QGridLayout(spacing=0)
        layout.addLayout(grid)
        layout.addStretch()

        grid.addWidget(self._labelmidichannel, 0, 0)
        grid.addWidget(self._midichannel, 0, 1)
        grid.addWidget(self._labelkeysignature, 1, 0)
        grid.addWidget(self._keysignature, 1, 1)
        grid.addWidget(self._labelaccidentals, 2, 0)
        grid.addWidget(self._groupaccidentals, 2, 1)
        grid.addWidget(self._chordmode, 3, 0)
        grid.addWidget(self._relativemode, 3, 1)
        grid.addWidget(self._labeldamper, 4, 0)
        grid.addWidget(self._damper, 4, 1)
        grid.addWidget(self._labelsostenuto, 5, 0)
        grid.addWidget(self._sostenuto, 5, 1)
        grid.addWidget(self._labelsoft, 6, 0)
        grid.addWidget(self._soft, 6, 1)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        hbox.addWidget(self._capture)
        hbox.addStretch()

        app.translateUI(self)

        self.loadsettings()
        for s in signals:
            s.connect(self.savesettings)

    def mainwindow(self):
        return self._dockwidget().mainwindow()

    def channel(self):
        return self._midichannel.currentIndex()

    def keysignature(self):
        return self._keysignature.currentIndex()

    def accidentals(self):
        if self._accidentalsflats.isChecked():
            return 'flats'
        else:
            return 'sharps'

    def chordmode(self):
        return self._chordmode.isChecked()

    def relativemode(self):
        return self._relativemode.isChecked()

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

    def switchaccidental(self):
        if self.accidentals() == 'flats':
            self._accidentalssharps.setChecked(True)
        else:
            self._accidentalsflats.setChecked(True)

    def savesettings(self):
        s = QSettings()
        s.beginGroup("midiinputdock")
        s.setValue("midichannel", self._midichannel.currentIndex())
        s.setValue("keysignature", self._keysignature.currentIndex())
        if self._accidentalsflats.isChecked():
            s.setValue("accidentals", 'flats')
        else:
            s.setValue("accidentals", 'sharps')
        s.setValue("chordmode", self._chordmode.isChecked())
        s.setValue("relativemode", self._relativemode.isChecked())

    def loadsettings(self):
        s = QSettings()
        s.beginGroup("midiinputdock")
        self._midichannel.setCurrentIndex(s.value("midichannel", 0, int))
        self._keysignature.setCurrentIndex(s.value("keysignature", 7, int))
        if s.value("accidentals", 'sharps', str) == 'flats':
            self._accidentalsflats.setChecked(True)
        else:
            self._accidentalssharps.setChecked(True)
        self._chordmode.setChecked(s.value("chordmode", False, bool))
        self._relativemode.setChecked(s.value("relativemode", False, bool))

    def translateUI(self):
        self._labelmidichannel.setText(_("MIDI channel"))
        self._midichannel.addItems([_("all")]+[str(i) for i in range(1,17)])
        self._labelkeysignature.setText(_("Key signature"))
        self._keysignature.addItems([
            _("C flat major (7 flats)"),
            _("G flat major (6 flats)"),
            _("D flat major (5 flats)"),
            _("A flat major (4 flats)"),
            _("E flat major (3 flats)"),
            _("B flat major (2 flats)"),
            _("F major (1 flat)"),
            _("C major"),
            _("G major (1 sharp)"),
            _("D major (2 sharps)"),
            _("A major (3 sharps)"),
            _("E major (4 sharps)"),
            _("B major (5 sharps)"),
            _("F sharp major (6 sharps)"),
            _("C sharp major (7 sharps)")
            ])
        self._keysignature.setCurrentIndex(7)
        self._labelaccidentals.setText(_("Accidentals"))
        self._accidentalssharps.setText(_("sharps"))
        self._accidentalsflats.setText(_("flats"))
        self._chordmode.setText(_("Chord mode"))
        self._chordmode.setToolTip(_(
            "Enter simultaneously played notes as chords. "
            "See \"What's This\" for more information."))
        self._chordmode.setWhatsThis(_(
            "Notes which are played simultaneously are written "
            "as chords. As a consequence they are not written "
            "before the last key is lifted. Of course single "
            "can also be entered."))
        self._relativemode.setText(_("Relative mode"))
        self._relativemode.setToolTip(_(
            "Enter octaves of notes relative to the last note. "
            "See \"What's This\" for more information."))
        self._relativemode.setWhatsThis(_(
            "Enter octaves of notes relative to the last note. "
            "This refers to the last key pressed on the MIDI keyboard, not the last note in the document."
            "Hold Shift with a note to enter an octave check."))
        self._labeldamper.setText(_("Damper pedal"))
        self._labelsostenuto.setText(_("Sostenuto pedal"))
        self._labelsoft.setText(_("Soft pedal"))
