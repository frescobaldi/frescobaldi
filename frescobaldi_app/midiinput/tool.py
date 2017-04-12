"""
MIDI input dock
"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import icons
import panel


class MidiInputTool(panel.Panel):
    """Midi Tool."""
    def __init__(self, mainwindow):
        super(MidiInputTool, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+R"))
        ac = self.actionCollection = Actions()
        ac.capture_start.triggered.connect(self.slotStartCapturing)
        ac.capture_stop.triggered.connect(self.slotStopCapturing)
        ac.accidental_switch.triggered.connect(self.slotAccidentalSwitch)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        mainwindow.addDockWidget(Qt.BottomDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("MIDI Input"))
        self.toggleViewAction().setText(_("MIDI I&nput"))

    def slotStartCapturing(self):
        self.widget().startcapturing()

    def slotStopCapturing(self):
        self.widget().stopcapturing()

    def slotAccidentalSwitch(self):
        self.widget().switchaccidental()

    def createWidget(self):
        from . import widget
        return widget.Widget(self)

class Actions(actioncollection.ActionCollection):
    name = "midiinputtool"
    def createActions(self, parent=None):
        self.capture_start = QAction(parent)
        self.capture_stop = QAction(parent)
        self.accidental_switch = QAction(parent)

        self.capture_start.setIcon(icons.get('media-record'))
        self.capture_stop.setIcon(icons.get('process-stop'))

        self.accidental_switch.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_3))

    def translateUI(self):
        self.capture_start.setText(_("midi input", "Start capturing"))
        self.capture_start.setToolTip(_("midi input", "Start MIDI capturing"))
        self.capture_stop.setText(_("midi input", "Stop capturing"))
        self.capture_stop.setToolTip(_("midi input", "Stop MIDI capturing"))
        self.accidental_switch.setText(_("midi input", "Switch accidental style"))
        self.accidental_switch.setToolTip(_("midi input", "Change accidental style (flats or sharps)"))
