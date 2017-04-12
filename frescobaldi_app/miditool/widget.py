# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The MIDI tool widget.
"""


from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtWidgets import (
    QWidget, QComboBox, QToolButton, QSlider, QGridLayout, QSizePolicy, QLabel)

import app
import css
import qutil
import listmodel
import midihub
import gadgets.drag

from . import midifiles
from . import output
from . import player


class Widget(QWidget):
    def __init__(self, dockwidget):
        super(Widget, self).__init__(dockwidget)
        self._document = None
        self._fileSelector = QComboBox(editable=True, insertPolicy=QComboBox.NoInsert)
        gadgets.drag.ComboDrag(self._fileSelector).role = Qt.UserRole
        self._fileSelector.lineEdit().setReadOnly(True)
        self._fileSelector.lineEdit().setFocusPolicy(Qt.NoFocus)
        self._stopButton = QToolButton()
        self._playButton = QToolButton()
        self._timeSlider = QSlider(Qt.Horizontal, tracking=False,
            singleStep=500, pageStep=5000, invertedControls=True)
        self._display = Display()
        self._tempoFactor = QSlider(Qt.Vertical, minimum=-50, maximum=50,
            singleStep=1, pageStep=5)

        grid = QGridLayout(spacing=0)
        self.setLayout(grid)

        grid.addWidget(self._fileSelector, 0, 0, 1, 3)
        grid.addWidget(self._stopButton, 1, 0)
        grid.addWidget(self._playButton, 1, 1)
        grid.addWidget(self._timeSlider, 1, 2)
        grid.addWidget(self._display, 2, 0, 1, 3)
        grid.addWidget(self._tempoFactor, 0, 3, 3, 1)

        # size policy of combo
        p = self._fileSelector.sizePolicy()
        p.setHorizontalPolicy(QSizePolicy.Ignored)
        self._fileSelector.setSizePolicy(p)

        # size policy of combo popup
        p = self._fileSelector.view().sizePolicy()
        p.setHorizontalPolicy(QSizePolicy.MinimumExpanding)
        self._fileSelector.view().setSizePolicy(p)

        self._player = player.Player()
        self._outputCloseTimer = QTimer(interval=60000, singleShot=True,
            timeout=self.closeOutput)
        self._timeSliderTicker = QTimer(interval=200, timeout=self.updateTimeSlider)
        self._fileSelector.activated[int].connect(self.slotFileSelected)
        self._tempoFactor.valueChanged.connect(self.slotTempoChanged)
        self._timeSlider.valueChanged.connect(self.slotTimeSliderChanged)
        self._timeSlider.sliderMoved.connect(self.slotTimeSliderMoved)
        self._player.beat.connect(self.updateDisplayBeat)
        self._player.time.connect(self.updateDisplayTime)
        self._player.stateChanged.connect(self.slotPlayerStateChanged)
        self.slotPlayerStateChanged(False)
        dockwidget.mainwindow().currentDocumentChanged.connect(self.loadResults)
        app.documentLoaded.connect(self.slotDocumentLoaded)
        app.jobFinished.connect(self.slotUpdatedFiles)
        app.aboutToQuit.connect(self.stop)
        midihub.aboutToRestart.connect(self.slotAboutToRestart)
        midihub.settingsChanged.connect(self.clearMidiSettings, -100)
        midihub.settingsChanged.connect(self.readMidiSettings)
        app.documentClosed.connect(self.slotDocumentClosed)
        app.translateUI(self)
        self.readMidiSettings()
        d = dockwidget.mainwindow().currentDocument()
        if d:
            self.loadResults(d)

    def translateUI(self):
        self._tempoFactor.setToolTip(_("Tempo"))

    def slotAboutToRestart(self):
        self.stop()
        self._player.set_output(None)

    def clearMidiSettings(self):
        """Called first when settings are changed."""
        self.stop()
        self._outputCloseTimer.stop()
        self._player.set_output(None)

    def readMidiSettings(self):
        """Called after clearMidiSettings(), and on first init."""
        pass

    def openOutput(self):
        """Called when playing starts. Ensures an output port is opened."""
        self._outputCloseTimer.stop()
        if not self._player.output():
            p = QSettings().value("midi/player/output_port", midihub.default_output(), str)
            o = midihub.output_by_name(p)
            if o:
                self._player.set_output(output.Output(o))

    def closeOutput(self):
        """Called when the output close timer fires. Closes the output."""
        self._player.set_output(None)

    def slotPlayerStateChanged(self, playing):
        ac = self.parentWidget().actionCollection
        # setDefaultAction also adds the action
        for b in self._stopButton, self._playButton:
            while b.actions():
                b.removeAction(b.actions()[0])
        if playing:
            self._timeSliderTicker.start()
            self._stopButton.setDefaultAction(ac.midi_stop)
            self._playButton.setDefaultAction(ac.midi_pause)
        else:
            self._timeSliderTicker.stop()
            self.updateTimeSlider()
            self._stopButton.setDefaultAction(ac.midi_restart)
            self._playButton.setDefaultAction(ac.midi_play)
            # close the output if the preference is set
            if QSettings().value("midi/close_outputs", False, bool):
                self._outputCloseTimer.start()

    def play(self):
        """Starts the MIDI player, opening an output if necessary."""
        if not self._player.is_playing() and not self._player.has_events():
            self.restart()
        self.openOutput()
        if not self._player.output():
            self._display.statusMessage(_("No output found!"))
        self._player.start()

    def stop(self):
        """Stops the MIDI player."""
        self._player.stop()

    def restart(self):
        """Restarts the MIDI player.

        If another file is in the file selector, or the file was updated,
        the new file is loaded.

        """
        self._player.seek(0)
        self.updateTimeSlider()
        self._display.reset()
        if self._document:
            files = midifiles.MidiFiles.instance(self._document)
            index = self._fileSelector.currentIndex()
            if files and (files.song(index) is not self._player.song()):
                self.loadSong(index)

    def slotTempoChanged(self, value):
        """Called when the user drags the tempo."""
        # convert -50 to 50 to 0.5 to 2.0
        factor = 2 ** (value / 50.0)
        self._player.set_tempo_factor(factor)
        self._display.setTempo("{0}%".format(int(factor * 100)))

    def slotTimeSliderChanged(self, value):
        self._player.seek(value)
        self._display.setTime(value)
        if self._player.song():
            self._display.setBeat(*self._player.song().beat(value)[1:])

    def slotTimeSliderMoved(self, value):
        self._display.setTime(value)
        if self._player.song():
            self._display.setBeat(*self._player.song().beat(value)[1:])

    def updateTimeSlider(self):
        if not self._timeSlider.isSliderDown():
            with qutil.signalsBlocked(self._timeSlider):
                self._timeSlider.setMaximum(self._player.total_time())
                self._timeSlider.setValue(self._player.current_time())

    def updateDisplayBeat(self, measnum, beat, num, den):
        if not self._timeSlider.isSliderDown():
            self._display.setBeat(measnum, beat, num, den)

    def updateDisplayTime(self, time):
        if not self._timeSlider.isSliderDown():
            self._display.setTime(time)

    def slotDocumentLoaded(self, document):
        """Called when a new document is loaded.

        Only calls slotUpdatedFiles when this is the first document, as that
        slot will be called anyway when the current document is switched. When
        the first document is loaded, it is loaded into the existing empty
        document, so mainwindow.currentDocumentChanged() will never be emitted.

        """
        if len(app.documents) == 1:
            self.slotUpdatedFiles(document)

    def slotUpdatedFiles(self, document, job=None):
        """Called when there are new MIDI files."""
        mainwindow = self.parentWidget().mainwindow()
        import engrave
        if document not in (mainwindow.currentDocument(), engrave.engraver(mainwindow).document()):
            return
        import jobattributes
        if job and jobattributes.get(job).mainwindow != mainwindow:
            return
        self.loadResults(document)

    def loadResults(self, document):
        files = midifiles.MidiFiles.instance(document)
        if files.update():
            self._document = document
            self._fileSelector.setModel(files.model())
            self._fileSelector.setCurrentIndex(files.current)
            if not self._player.is_playing():
                self.loadSong(files.current)

    def loadSong(self, index):
        files = midifiles.MidiFiles.instance(self._document)
        self._player.set_song(files.song(index))
        m, s = divmod(self._player.total_time() // 1000, 60)
        name = self._fileSelector.currentText()
        self.updateTimeSlider()
        self._display.reset()
        self._display.statusMessage(
            _("midi lcd screen", "LOADED"), name,
            _("midi lcd screen", "TOTAL"), "{0}:{1:02}".format(m, s))

    def slotFileSelected(self, index):
        if self._document:
            self._player.stop()
            files = midifiles.MidiFiles.instance(self._document)
            if files:
                files.current = index
                self.restart()

    def slotDocumentClosed(self, document):
        if document == self._document:
            self._document = None
            self._fileSelector.setModel(listmodel.ListModel([]))
            self._player.stop()
            self._player.clear()
            self.updateTimeSlider()
            self._display.reset()


class Display(QLabel):
    """Maintains values in the LCD display."""
    def __init__(self):
        QLabel.__init__(self, wordWrap=True)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred))
        self.setStyleSheet(css.lcd_screen)
        self._tempoTimer = QTimer(interval=1500, singleShot=True,
            timeout=self.setTempo)
        self._statusTimer = QTimer(interval=2000, singleShot=True,
            timeout=self.statusMessage)
        self._tempo = None
        self._status = None
        self.reset()
        app.translateUI(self)

    def reset(self):
        """Sets everything to 0."""
        self._time = 0
        self._beat = 0, 0, 0, 0
        self.updateDisplay()

    def translateUI(self):
        self.updateDisplay()

    def setTime(self, time):
        self._time = time
        self.updateDisplay()

    def setBeat(self, measnum, beat, num, den):
        self._beat = measnum, beat, num, den
        self.updateDisplay()

    def setTempo(self, text=None):
        self._tempo = text
        if text:
            self._tempoTimer.start()
        self.updateDisplay()

    def statusMessage(self, *msg):
        """Status message can be multiple arguments (1 to 4)."""
        self._status = msg
        if msg:
            self._statusTimer.start()
        self.updateDisplay()

    def updateDisplay(self):
        minutes, seconds = divmod(self._time // 1000, 60)

        time_spec = "{0}:{1:02}".format(minutes, seconds)
        if self._status:
            items = self._status
            if len(items) == 1:
                self.setText(_lcd_status_one.format("&nbsp;", items[0]))
            elif len(items) == 2:
                self.setText(_lcd_status_one.format(*items))
            elif len(items) == 3:
                self.setText(_lcd_status_two.format(
                    items[0], items[1], "&nbsp;", items[2]))
            elif len(items) == 4:
                self.setText(_lcd_status_two.format(*items))
        elif self._tempo:
            self.setText(_lcd_text.format(
                _("midi lcd screen", "TIME"),
                _("midi lcd screen", "TEMPO"),
                time_spec,
                self._tempo,
            ))
        else:
            measnum, beat, num, den = self._beat
            beat_spec = "{0}.{1:2}".format(measnum, beat)
            time_sig = "&nbsp;{0}/{1}".format(num, 2 ** den) if num else ""
            self.setText(_lcd_text.format(
                _("midi lcd screen", "TIME"),
                _("midi lcd screen", "BEAT") + time_sig,
                time_spec,
                beat_spec,
            ))



_lcd_text = """\
<table width=100% border=0 cellspacing=0>
<tr>
<td width=50% align=right style="font-size:8px;">{0}</td>
<td width=50% align=right style="font-size:8px;">{1}</td>
</tr>
<tr>
<td width=50% align=right><h2>{2}</h2></td>
<td width=50% align=right><h2>{3}</h2></td>
</tr>
</table>"""

_lcd_status_one = """\
<table width=100% border=0 cellspacing=0>
<tr>
<td align=left style="font-size:8px;">{0}</td>
</tr>
<tr>
<td align=left><h2>{1}</h2></td>
</tr>
</table>"""

_lcd_status_two = """\
<table width=100% border=0 cellspacing=0>
<tr>
<td align=left style="font-size:8px;">{0}</td>
<td align=right style="font-size:8px;">{2}</td>
</tr>
<tr>
<td align=left><h2>{1}</h2></td>
<td align=right><h2>{3}</h2></td>
</tr>
</table>"""

