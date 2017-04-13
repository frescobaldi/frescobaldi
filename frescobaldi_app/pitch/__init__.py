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
Tools to edit pitch of selected music.
"""


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QAction, QActionGroup, QMenu

import app
import actioncollection
import actioncollectionmanager
import plugin
import qutil
import icons
import ly.pitch


class Pitch(plugin.MainWindowPlugin):
    def __init__(self, mainwindow):
        self.actionCollection = ac = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        m = self.language_menu = QMenu()
        g = self.language_group = QActionGroup(None)
        for name in sorted(ly.pitch.pitchInfo.keys()):
            a = m.addAction(name.title())
            a.setObjectName(name)
            a.setCheckable(True)
            g.addAction(a)
        qutil.addAccelerators(m.actions())
        ac.pitch_language.setMenu(m)
        m.aboutToShow.connect(self.setLanguageMenu)
        g.triggered.connect(self.changeLanguage)
        ac.pitch_rel2abs.triggered.connect(self.rel2abs)
        ac.pitch_abs2rel.triggered.connect(self.abs2rel)
        ac.pitch_transpose.triggered.connect(self.transpose)
        ac.pitch_modal_transpose.triggered.connect(self.modalTranspose)
        ac.pitch_mode_shift.triggered.connect(self.modeShift)
        ac.pitch_simplify.triggered.connect(self.simplifyAccidentals)
        self.readSettings()
        app.aboutToQuit.connect(self.writeSettings)

    def get_absolute(self, document):
        """Return True when the first pitch in a \\relative expression without
        startpitch may be considered absolute.

        """
        import documentinfo
        return (self.actionCollection.pitch_relative_assume_first_pitch_absolute.isChecked()
            or documentinfo.docinfo(document).version() >= (2, 18))

    def rel2abs(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        pitch.rel2abs(cursor, self.get_absolute(cursor.document()))

    def abs2rel(self):
        startpitch = self.actionCollection.pitch_relative_write_startpitch.isChecked()
        from . import pitch
        cursor = self.mainwindow().textCursor()
        pitch.abs2rel(cursor, startpitch, self.get_absolute(cursor.document()))

    def transpose(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        transposer = pitch.getTransposer(cursor.document(), self.mainwindow())
        if transposer:
            pitch.transpose(cursor, transposer, self.mainwindow(), self.get_absolute(cursor.document()))

    def modalTranspose(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        transposer = pitch.getModalTransposer(cursor.document(), self.mainwindow())
        if transposer:
            pitch.transpose(cursor, transposer, self.mainwindow())

    def modeShift(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        transposer = pitch.getModeShifter(cursor.document(), self.mainwindow())
        if transposer:
            pitch.transpose(cursor, transposer, self.mainwindow())

    def simplifyAccidentals(self):
        from . import pitch
        import ly.pitch.transpose
        cursor = self.mainwindow().textCursor()
        transposer = ly.pitch.transpose.Simplifier()
        pitch.transpose(cursor, transposer, self.mainwindow(), self.get_absolute(cursor.document()))

    def setLanguageMenu(self):
        """Called when the menu is shown; selects the correct language."""
        import documentinfo
        doc = self.mainwindow().currentDocument()
        lang = documentinfo.docinfo(doc).language() or 'nederlands'
        for a in self.language_group.actions():
            if a.objectName() == lang:
                a.setChecked(True)
                break

    def changeLanguage(self, action):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        pitch.changeLanguage(cursor, action.objectName())

    def readSettings(self):
        s = QSettings()
        s.beginGroup("pitch-menu")
        self.actionCollection.pitch_relative_assume_first_pitch_absolute.setChecked(
            s.value("relative-first-pitch-absolute", False, bool))
        self.actionCollection.pitch_relative_write_startpitch.setChecked(
            s.value("relative-write-startpitch", True, bool))

    def writeSettings(self):
        s = QSettings()
        s.beginGroup("pitch-menu")
        s.setValue("relative-first-pitch-absolute",
            self.actionCollection.pitch_relative_assume_first_pitch_absolute.isChecked())
        s.setValue("relative-write-startpitch",
            self.actionCollection.pitch_relative_write_startpitch.isChecked())


class Actions(actioncollection.ActionCollection):
    name = "pitch"
    def createActions(self, parent):
        self.pitch_language = QAction(parent)
        self.pitch_rel2abs = QAction(parent)
        self.pitch_abs2rel = QAction(parent)
        self.pitch_transpose = QAction(parent)
        self.pitch_modal_transpose = QAction(parent)
        self.pitch_mode_shift = QAction(parent)
        self.pitch_simplify = QAction(parent)
        self.pitch_relative_assume_first_pitch_absolute = QAction(parent, checkable=True)
        self.pitch_relative_write_startpitch = QAction(parent, checkable=True)

        self.pitch_language.setIcon(icons.get('tools-pitch-language'))
        self.pitch_transpose.setIcon(icons.get('tools-transpose'))
        self.pitch_modal_transpose.setIcon(icons.get('tools-transpose'))
        self.pitch_mode_shift.setIcon(icons.get('tools-transpose'))
        self.pitch_simplify.setIcon(icons.get('tools-transpose'))

    def translateUI(self):
        self.pitch_language.setText(_("Pitch Name &Language"))
        self.pitch_language.setToolTip(_(
            "Change the LilyPond language used for pitch names "
            "in this document or in the selection."))
        self.pitch_rel2abs.setText(_("Convert Relative to &Absolute"))
        self.pitch_rel2abs.setToolTip(_(
            "Converts the notes in the document or selection from relative to "
            "absolute pitch."))
        self.pitch_abs2rel.setText(_("Convert Absolute to &Relative"))
        self.pitch_abs2rel.setToolTip(_(
            "Converts the notes in the document or selection from absolute to "
            "relative pitch."))
        self.pitch_transpose.setText(_("&Transpose..."))
        self.pitch_transpose.setToolTip(_(
            "Transposes all notes in the document or selection."))
        self.pitch_modal_transpose.setText(_("&Modal Transpose..."))
        self.pitch_modal_transpose.setToolTip(_(
            "Transposes all notes in the document or selection within a given mode."))
        self.pitch_mode_shift.setText(_("Mode shift..."))
        self.pitch_mode_shift.setToolTip(_(
            "Transforms all notes in the document or selection to an optional mode."))
        self.pitch_simplify.setText(_("Simplify Accidentals"))
        self.pitch_simplify.setToolTip(_(
            "Replaces notes with accidentals as much as possible with natural neighbors."))
        self.pitch_relative_assume_first_pitch_absolute.setText(_(
            "First pitch in \\relative {...} is absolute"))
        self.pitch_relative_assume_first_pitch_absolute.setToolTip(_(
            "If checked, always assume that the first pitch of a \\relative {...}\n"
            "expression without startpitch is absolute. Otherwise, Frescobaldi\n"
            "only assumes this when the LilyPond version >= 2.18."))
        self.pitch_relative_write_startpitch.setText(_(
            "Write \\relative with startpitch"))
        self.pitch_relative_write_startpitch.setToolTip(_(
            "If checked, when converting absolute music to relative, a startpitch\n"
            "is added. Otherwise, no starting pitch is written."))


