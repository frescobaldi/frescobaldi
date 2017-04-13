# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
A chooser combobox to choose a LilyPond instance.
"""


from PyQt5.QtWidgets import QComboBox

import app
import lilypondinfo
import icons


class LilyChooser(QComboBox):
    def __init__(self, parent=None):
        super(LilyChooser, self).__init__(parent)
        self._infos = []
        app.translateUI(self)
        app.settingsChanged.connect(self.load)
        self.load()

    def translateUI(self):
        self.setToolTip(_("Choose the desired LilyPond version."""))

    def setLilyPondInfo(self, info):
        """Set the current LilyPond info (one of lilypondinfo.infos())."""
        try:
            self.setCurrentIndex(self._infos.index(info))
        except IndexError:
            pass

    def lilyPondInfo(self):
        """Get the current LilyPond info."""
        if self._infos:
            return self._infos[self.currentIndex()]

    def load(self):
        """Load the available LilyPond infos."""
        infos = lilypondinfo.infos() or [lilypondinfo.default()]
        infos.sort(key = lambda i: i.version() or (999,))
        cur = self._infos[self.currentIndex()] if self._infos else lilypondinfo.preferred()
        self._infos = infos
        block = self.blockSignals(True)
        try:
            self.clear()
            index = 0
            for i, info in enumerate(infos):
                icon = 'lilypond-run' if info.version() else 'dialog-error'
                self.addItem(icons.get(icon), info.prettyName())
                if info.abscommand() == cur.abscommand() or info.command == cur.command:
                    index = i
            self.setCurrentIndex(index)
        finally:
            self.blockSignals(block)


