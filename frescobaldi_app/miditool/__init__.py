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
The MIDI tool.
"""


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import app
import icons
import panel


class MidiTool(panel.Panel):
    """Midi Tool."""
    def __init__(self, mainwindow):
        super(MidiTool, self).__init__(mainwindow)
        self.hide()
        self.toggleViewAction().setShortcut(QKeySequence("Meta+Alt+P"))
        ac = self.actionCollection = Actions()
        ac.midi_play.triggered.connect(self.slotPlay)
        ac.midi_pause.triggered.connect(self.slotPause)
        ac.midi_stop.triggered.connect(self.slotStop)
        ac.midi_restart.triggered.connect(self.slotRestart)
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        mainwindow.addDockWidget(Qt.TopDockWidgetArea, self)

    def translateUI(self):
        self.setWindowTitle(_("MIDI"))
        self.toggleViewAction().setText(_("MIDI &Player"))

    def createWidget(self):
        from . import widget
        return widget.Widget(self)

    def slotPause(self):
        """Called on action Pause."""
        self.widget().stop()

    def slotPlay(self):
        """Called on action Play."""
        self.widget().play()

    def slotStop(self):
        """Called on action Stop."""
        self.widget().stop()

    def slotRestart(self):
        """Called on action Restart."""
        self.widget().restart()


class Actions(actioncollection.ActionCollection):
    name = "miditool"
    def createActions(self, parent=None):
        self.midi_pause = QAction(parent)
        self.midi_play = QAction(parent)
        self.midi_stop = QAction(parent)
        self.midi_restart = QAction(parent)

        try:
            self.midi_pause.setShortcut(QKeySequence(Qt.Key_MediaPause))
        except AttributeError:
            pass # No Qt.Key_MediaPause in some PyQt5 versions
        self.midi_play.setShortcut(QKeySequence(Qt.Key_MediaPlay))
        self.midi_stop.setShortcut(QKeySequence(Qt.Key_MediaStop))
        self.midi_restart.setShortcut(QKeySequence(Qt.Key_MediaPrevious))

        self.midi_pause.setIcon(icons.get('media-playback-pause'))
        self.midi_play.setIcon(icons.get('media-playback-start'))
        self.midi_stop.setIcon(icons.get('media-playback-stop'))
        self.midi_restart.setIcon(icons.get('media-skip-backward'))

    def translateUI(self):
        self.midi_pause.setText(_("midi player", "Pause"))
        self.midi_play.setText(_("midi player", "Play"))
        self.midi_stop.setText(_("midi player", "Stop"))
        self.midi_restart.setText(_("midi player", "Restart"))



