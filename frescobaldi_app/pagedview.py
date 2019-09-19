# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2019 by Wilbert Berendsen
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
Customization classes for the qpageview.View.

This is used throughout Frescobaldi, to obey color settings etc.

"""


from PyQt5.QtCore import QSettings, Qt

import app
import textformats
import qpageview
import qpageview.magnifier


class Magnifier(qpageview.magnifier.Magnifier):
    """A magnifier that reads and stores its settings."""
    def __init__(self):
        super().__init__()
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        s = QSettings()
        s.beginGroup("musicview/magnifier")
        size = s.value("size", 350, int)
        if self.MIN_SIZE <= size <= self.MAX_SIZE:
            self.resize(size, size)
        scale = s.value("scalef", 3.0, float)
        super().setScale(scale)

    def setScale(self, scale):
        """Reimplemented to save the scale."""
        super().setScale(scale)
        QSettings().setValue("musicview/magnifier/scalef", scale)

    def resizeEvent(self, ev):
        """Reimplemented to save the size."""
        super().resizeEvent(ev)
        QSettings().setValue("musicview/magnifier/size", ev.size().width())


class View(qpageview.View):
    def __init__(self, parent=None):
        super().__init__(parent)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()

    def readSettings(self):
        # kinetic scrolling
        kinetic = QSettings().value("musicview/kinetic_scrolling", True, bool)
        self.kineticPagingEnabled = kinetic
        self.kineticScrollingEnabled = kinetic

        # scrollbar visibility
        scrollbars = QSettings().value("musicview/show_scrollbars", True, bool)
        policy = Qt.ScrollBarAsNeeded if scrollbars else Qt.ScrollBarAlwaysOff
        self.setHorizontalScrollBarPolicy(policy)
        self.setVerticalScrollBarPolicy(policy)

        # paper color; change the existing renderer
        paperColor = textformats.formatData('editor').baseColors['paper']
        # if a page has no renderer, adjust the page itself :-)
        rendererOrPages = set(page.renderer or page for page in self.pageLayout())
        changed = False
        for rp in rendererOrPages:
            if rp.paperColor != paperColor:
                changed = True
                rp.paperColor = paperColor
        if changed:
            self.rerender()

    def loadPopplerDocument(self, document, renderer=None):
        """Reimplemented to use a customized renderer by default."""
        super().loadPopplerDocument(document, renderer or self.renderer("pdf"))

    def loadPdf(self, filename, renderer=None):
        """Reimplemented to use a customized renderer by default."""
        super().loadPdf(filename, renderer or self.renderer("pdf"))

    def loadSvgs(self, filenames, renderer=None):
        """Reimplemented to use a customized renderer by default."""
        super().loadSvgs(filenames, renderer or self.renderer("svg"))

    def renderer(self, rendertype):
        """Factory to create a renderer with the paper color adjusted to the prefs.

        Currently, the rendertype can be "pdf", "svg", "image" or "diff".

        For image types, the paper color is not used. For diff types, it is
        recommended to use the default white background color.

        """
        if rendertype == "pdf":
            import qpageview.poppler
            r = qpageview.poppler.PopplerRenderer()
        elif rendertype == "svg":
            import qpageview.svg
            r = qpageview.svg.SvgRenderer()
        elif rendertype == "image":
            import qpageview.image
            r = qpageview.image.ImageRenderer()
        elif rendertype == "diff":
            import qpageview.diff
            r = qpageview.diff.DiffRenderer()
        else:
            raise ValueError("unknown render type")
        r.paperColor = textformats.formatData('editor').baseColors['paper']
        return r


