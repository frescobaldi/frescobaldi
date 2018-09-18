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
Handle everything around (available) text fonts.
NOTE: "available" refers to the fonts that are available to LilyPond,
which may be different than for arbitrary programs and can canonically
be determined by running `lilypond -dshow-available-fonts`.
"""


from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import plugin

from . import musicfonts, textfonts

def fonts(mainwindow):
    return Fonts.instance(mainwindow)


class Fonts(plugin.MainWindowPlugin):

    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.fonts_show_available_fonts.triggered.connect(
            self.showAvailableFonts)
        ac.fonts_set_document_fonts.triggered.connect(
            self.setDocumentFonts)

    def setDocumentFonts(self):
        """Menu Action Set Document Fonts."""
        from . import documentfontsdialog
        dlg = documentfontsdialog.DocumentFontsDialog(self.mainwindow())
        if dlg.exec_():
            text = dlg.document_font_code()
            # NOTE: How to translate this to the dialog context?
            # if state[-1] != "paper":
            text = "\\paper {{\n{0}}}\n".format(text)
            cursor = self.mainwindow().currentView().textCursor()
            cursor.insertText(text)

    def showAvailableFonts(self):
        """Menu action Show Available Fonts."""
        import documentinfo
        info = documentinfo.lilyinfo(self.mainwindow().currentDocument())
        from . import availablefontsdialog
        availablefontsdialog.show_available_fonts(self.mainwindow(), info)


class Actions(actioncollection.ActionCollection):
    name = "fonts"

    def createActions(self, parent=None):
        self.fonts_show_available_fonts = QAction(parent)
        self.fonts_set_document_fonts = QAction(parent)

    def translateUI(self):
        self.fonts_show_available_fonts.setText(
            _("Show Available &Fonts..."))
        self.fonts_set_document_fonts.setText(
            _("Set &Document Fonts..."))


class AvailableFonts(QObject):
    """Store available text and music fonts for a given
    LilyPond installation. Sets for multiple registered
    installations are maintained in a global dictionary
    cached for the whole application lifetime.
    Note that the music fonts are loaded immediately while
    text fonts have to be loaded explicitly (in an
    asynchronous invocation of LilyPond)."""

    def __init__(self, lilypond_info):
        self.lilypond_info = lilypond_info
        self._music_fonts = musicfonts.InstalledMusicFonts(
            lilypond_info)
        self._text_fonts = textfonts.TextFonts(lilypond_info)

    def music_fonts(self):
        return self._music_fonts

    def text_fonts(self):
        return self._text_fonts


_available_fonts = {}
def available(lilypond_info):
    key = lilypond_info.abscommand() or lilypond_info.command()
    if not key in _available_fonts.keys():
        _available_fonts[key] = AvailableFonts(lilypond_info)
    return _available_fonts[key]
