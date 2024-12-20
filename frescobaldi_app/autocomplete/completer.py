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
The completer for Frescobaldi.
"""


import re

from PyQt6.QtGui import QTextCursor

import app
import textformats
import widgets.completer
import worker
import locking


class Completer(widgets.completer.Completer):
    def __init__(self):
        super().__init__()
        self.setMaxVisibleItems(16)
        self.popup().setMinimumWidth(100)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        self.popup().setFont(textformats.formatData('editor').font)
        self.popup().setPalette(textformats.formatData('editor').palette())

    def completionCursor(self):
        # Our worker does the actual cursor positioning
        return self.textCursor()

    class Worker(worker.Worker):
        """Worker to build a completion model in a background thread."""
        def work(self, data):
            with locking.lock(data.cursor.document()):
                cursor = data.cursor
                # trick: if we are still visible we don't have to analyze the
                # text again
                if not (data.popupVisible and data._pos < cursor.position()):
                    analyzer = self.analyzer()
                    pos, model = analyzer.completions(cursor)
                    if not model:
                        return
                    data._pos = cursor.block().position() + pos
                    if data.model != model:
                        data.model = model
                cursor.setPosition(data._pos, QTextCursor.MoveMode.KeepAnchor)
                self.resultReady.emit(data)

        def analyzer(self):
            from . import analyzer
            return analyzer.Analyzer()
