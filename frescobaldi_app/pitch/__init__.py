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

from __future__ import unicode_literals

from PyQt4.QtGui import QAction, QActionGroup, QMenu

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
    
    def rel2abs(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        pitch.rel2abs(cursor)
    
    def abs2rel(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        pitch.abs2rel(cursor)
    
    def transpose(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        transposer = pitch.getTransposer(cursor.document(), self.mainwindow())
        if transposer:
            pitch.transpose(cursor, transposer, self.mainwindow())
    
    def modalTranspose(self):
        from . import pitch
        cursor = self.mainwindow().textCursor()
        transposer = pitch.getModalTransposer(cursor.document(), self.mainwindow())
        if transposer:
            pitch.transpose(cursor, transposer, self.mainwindow())
    
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


class Actions(actioncollection.ActionCollection):
    name = "pitch"
    def createActions(self, parent):
        self.pitch_language = QAction(parent)
        self.pitch_rel2abs = QAction(parent)
        self.pitch_abs2rel = QAction(parent)
        self.pitch_transpose = QAction(parent)
        self.pitch_modal_transpose = QAction(parent)

        self.pitch_language.setIcon(icons.get('tools-pitch-language'))
        self.pitch_transpose.setIcon(icons.get('tools-transpose'))
        self.pitch_modal_transpose.setIcon(icons.get('tools-transpose'))
        
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
        
