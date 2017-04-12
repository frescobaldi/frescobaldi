# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 by Wilbert Berendsen
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
The completer for the snippet editing dialog.
"""



import keyword
import re

import app
import listmodel
import textformats
import widgets.completer

from . import snippets


class Completer(widgets.completer.Completer):
    def __init__(self, textedit):
        super(Completer, self).__init__()
        self.setWidget(textedit)
        self.setParent(textedit) # otherwise PyQt5 loses us
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        self.popup().setFont(textformats.formatData('editor').font)
        self.popup().setPalette(textformats.formatData('editor').palette())

    def completionCursor(self):
        cursor = self.textCursor()

        if self.popup().isVisible() and self._pos < cursor.position():
            cursor.setPosition(self._pos, cursor.KeepAnchor)
            return cursor

        # alter the model
        pos = cursor.position()
        text = cursor.document().toPlainText()

        # skip '-*- ' lines declaring variables, and check if it is python
        python = False
        block = cursor.document().firstBlock()
        start = 0
        while block.text().startswith('-*- '):
            if not python:
                python = any(True
                    for m in snippets._variables_re.finditer(block.text())
                    if m.group(1) == 'python')
            block = block.next()
            if not block.isValid():
                break
            start = block.position()

        # determine the word set to complete on
        if python:
            pattern = r'\w+'
        else:
            pattern = r'\\?[\w-]+'
        rx = re.compile(pattern)
        words = set(m.group() for m in rx.finditer(text, start)
                    if len(m.group()) > 4 and m.end() != pos)
        if python:
            words.update(keyword.kwlist)
            words.update(('cursor', 'state', 'text'))
        if words:
            self.setModel(listmodel.ListModel(sorted(words)))
            cursor.movePosition(cursor.StartOfWord, cursor.KeepAnchor)
            self._pos = cursor.position()
            return cursor


