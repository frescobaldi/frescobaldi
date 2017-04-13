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
A slightly customized subclass of qpopplerview.View.

This is used throughout Frescobaldi, to obey color settings etc.

"""


from PyQt5.QtCore import QSettings

import app
import textformats
import qpopplerview


# global setup of background color
def _setbackground():
    colors = textformats.formatData('editor').baseColors
    qpopplerview.cache.options().setPaperColor(colors['paper'])
    qpopplerview.cache.clear()

app.settingsChanged.connect(_setbackground, -1)
_setbackground()


# make small sizes smoother
qpopplerview.cache.options().setOversampleThreshold(96)


class View(qpopplerview.View):
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        try:
            import popplerqt5
        except ImportError:
            # surface with a "could not load popplerqt5" message
            import popplerdummy
            self.setSurface(popplerdummy.Surface(self))
        self.surface().pageLayout().setDPI(self.physicalDpiX(), self.physicalDpiY())
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        kineticScrollingActive = QSettings().value("musicview/kinetic_scrolling", True, bool)
        scrollbarsVisible = QSettings().value("musicview/show_scrollbars", True, bool)
        self.setKineticScrolling(kineticScrollingActive)
        self.setScrollbarsVisible(scrollbarsVisible)
        self.redraw() # because of possibly changed background color
        # magnifier size and scale
        s = MagnifierSettings.load()
        self.surface().magnifier().resize(s.size, s.size)
        self.surface().magnifier().setScale(s.scale / 100.0)


class MagnifierSettings(object):
    """Manages settings for the MusicView Magnifier."""
    sizeRange = (200, 800)
    scaleRange = (150, 800)

    def __init__(self, size=300, scale=300):
        self.size = size
        self.scale = scale

    @classmethod
    def load(cls):
        """Returns a loaded Magnifier settings instance."""
        self = cls()
        s = QSettings()
        s.beginGroup("musicview/magnifier")
        try:
            self.size = int(s.value("size", self.size))
        except ValueError:
            pass
        try:
            self.scale = int(s.value("scale", self.scale))
        except ValueError:
            pass

        self.size = bound(self.size, *cls.sizeRange)
        self.scale = bound(self.scale, *cls.scaleRange)
        return self

    def save(self):
        """Stores the settings."""
        s = QSettings()
        s.beginGroup("musicview/magnifier")
        s.setValue("size", self.size)
        s.setValue("scale", self.scale)


def bound(value, start, end):
    """Clips value so it falls in the int range defined by start and end."""
    return max(start, min(end, value))


