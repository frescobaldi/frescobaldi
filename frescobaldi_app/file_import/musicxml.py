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
Import Music XML dialog.
Uses musicxml2ly to create ly fil from xml
In the dialog the options of musicxml2ly can be set 
"""

from __future__ import unicode_literals

import os
import subprocess
import collections

from PyQt4.QtCore import QSettings, QSize
from PyQt4.QtGui import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QTabWidget, QTextEdit, QWidget)

import app
import documentinfo
import userguide
import icons
import job
import jobmanager
import lilypondinfo
import listmodel
import widgets
import qutil
import util

# language names musicxml2ly allows
_langlist = [
    'nederlands',
    'catalan',
    'deutsch',
    'english',
    'espanol',
    'italiano',
    'norsk',
    'portugues',
    'suomi',
    'svenska',
    'vlaams',
]


class Dialog(QDialog):
	
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self._document = None
        self._path = None
        
        mainLayout = QGridLayout()
        self.setLayout(mainLayout)
        
        tabs = QTabWidget()
        
        import_tab = QWidget()
        post_tab = QWidget()
        
        itabLayout = QGridLayout(import_tab)
        ptabLayout = QGridLayout(post_tab)
        
        tabs.addTab(import_tab, "musicxml2ly")
        tabs.addTab(post_tab, "after import")
        
        self.noartCheck = QCheckBox()
        self.norestCheck = QCheckBox()
        self.nolayoutCheck = QCheckBox()
        self.nobeamCheck = QCheckBox()
        self.useAbsCheck = QCheckBox()
        
        self.langCombo = QComboBox()
        self.langLabel = QLabel()
        
        self.impChecks = [self.noartCheck,
						  self.norestCheck,
						  self.nolayoutCheck,
						  self.nobeamCheck,
						  self.useAbsCheck]
		
        self.formatCheck = QCheckBox()
        self.trimDurCheck = QCheckBox()
        self.removeScalesCheck = QCheckBox()
        self.runEngraverCheck = QCheckBox()
						   
        self.postChecks = [self.formatCheck,
						   self.trimDurCheck,
						   self.removeScalesCheck,
						   self.runEngraverCheck]								  
        
        self.commandLineLabel = QLabel()
        self.commandLine = QTextEdit(acceptRichText=False)
        
        self.setChecksObjectNames()
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        userguide.addButton(self.buttons, "musicxml_import")
        
        self.langCombo.addItem('')
        self.langCombo.addItems(_langlist)

        itabLayout.addWidget(self.noartCheck, 0, 0, 1, 2)
        itabLayout.addWidget(self.norestCheck, 1, 0, 1, 2)
        itabLayout.addWidget(self.nolayoutCheck, 2, 0, 1, 2)
        itabLayout.addWidget(self.nobeamCheck, 3, 0, 1, 2)
        itabLayout.addWidget(self.useAbsCheck, 4, 0, 1, 2)
        itabLayout.addWidget(self.langLabel, 5, 0, 1, 2)
        itabLayout.addWidget(self.langCombo, 6, 0, 1, 2)
        itabLayout.addWidget(widgets.Separator(), 7, 0, 1, 2)
        itabLayout.addWidget(self.commandLineLabel, 8, 0, 1, 2)
        itabLayout.addWidget(self.commandLine, 9, 0, 1, 2)
        
        ptabLayout.addWidget(self.formatCheck, 0, 0, 1, 2)
        ptabLayout.addWidget(self.trimDurCheck, 1, 0, 1, 2)       
        ptabLayout.addWidget(self.removeScalesCheck, 2, 0, 1, 2)
        ptabLayout.addWidget(self.runEngraverCheck, 3, 0, 1, 2)
        ptabLayout.setRowStretch(4, 10)
        
        mainLayout.addWidget(tabs, 0, 0, 9, 2)
        mainLayout.addWidget(self.buttons, 10, 0, 1, 2)
        
        app.translateUI(self)
        qutil.saveDialogSize(self, "xml_import/dialog/size", QSize(480, 260))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.noartCheck.toggled.connect(self.makeCommandLine)
        self.norestCheck.toggled.connect(self.makeCommandLine)
        self.nolayoutCheck.toggled.connect(self.makeCommandLine)
        self.nobeamCheck.toggled.connect(self.makeCommandLine)
        self.useAbsCheck.toggled.connect(self.makeCommandLine)
        self.langCombo.currentIndexChanged.connect(self.makeCommandLine)
        self.makeCommandLine()
        
        self.loadSettings()
        
    def setChecksObjectNames(self):
        self.noartCheck.setObjectName("articulation-directions")
        self.norestCheck.setObjectName("rest-positions")
        self.nolayoutCheck.setObjectName("page-layout")
        self.nobeamCheck.setObjectName("import-beaming")
        self.useAbsCheck.setObjectName("absolute-mode")
        
        self.formatCheck.setObjectName("reformat")
        self.trimDurCheck.setObjectName("trim-durations")
        self.removeScalesCheck.setObjectName("remove-scaling")
        self.runEngraverCheck.setObjectName("engrave-directly")
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Import Music XML")))
        self.noartCheck.setText(_("Import articulation directions"))
        self.norestCheck.setText(_("Import rest positions"))
        self.nolayoutCheck.setText(_("Import page layout"))
        self.nobeamCheck.setText(_("Import beaming"))
        self.useAbsCheck.setText(_("Pitches in absolute mode"))
        self.commandLineLabel.setText(_("Command line:"))
        
        self.langLabel.setText(_("Language for pitch names"))
        self.langCombo.setItemText(0, _("Default"))
        self.formatCheck.setText(_("Reformat source"))
        self.trimDurCheck.setText(_("Trim durations (Make implicit per line)"))
        self.removeScalesCheck.setText(_("Remove fraction duration scaling"))
        self.runEngraverCheck.setText(_("Engrave directly"))
        
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run musicxml2ly"))

    
    def setDocument(self, path):
        """Set the full path to the MusicXML document."""
        self._document = path
    
    def makeCommandLine(self):
        """Reads the widgets and builds a command line."""
        cmd = ["$musicxml2ly"]
        if self.useAbsCheck.isChecked():
            cmd.append('-a')
        if not self.noartCheck.isChecked():
            cmd.append('--nd')
        if not self.norestCheck.isChecked():
            cmd.append('--nrp')
        if not self.nolayoutCheck.isChecked():
            cmd.append('--npl')
        if not self.nobeamCheck.isChecked():
            cmd.append('--no-beaming')
        index = self.langCombo.currentIndex()
        if index > 0:
			cmd.append('--language=' + _langlist[index-1])

        cmd.append("$filename")
        self.commandLine.setText(' '.join(cmd))
    
    def getCmd(self):
        """Returns the command line."""
        cmd = []
        for t in self.commandLine.toPlainText().split():
            if t == '$musicxml2ly':
                cmd.extend(lilypondinfo.preferred().toolcommand('musicxml2ly'))
            elif t == '$filename':
                cmd.append(self._document)
            else:
                cmd.append(t)
        cmd.extend(['--output', '-'])
        return cmd
        
    def run_command(self):
        """ Run command line """
        cmd = self.getCmd()
        directory = os.path.dirname(self._document)
        proc = subprocess.Popen(cmd, cwd=directory,
            universal_newlines = True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
        stdouterr = proc.communicate()
        return stdouterr
		
    def getPostSettings(self):
        """ returns settings in the post import tab """
        post = []
        for p in self.postChecks:
            post.append(p.isChecked())
        return post
        
    def loadSettings(self):
        """ get users previous settings """
        imp_default = [False, False, False, False, False]
        post_default = [True, False, False, True]
        s = QSettings()
        s.beginGroup('xml_import')
        for i, d in zip(self.impChecks, imp_default):
            i.setChecked(s.value(i.objectName(), d, bool))
        for p, f in zip(self.postChecks, post_default):
            p.setChecked(s.value(p.objectName(), f, bool))
        lang = s.value("language", "default", type(""))
        try:
            index = _langlist.index(lang)
        except ValueError:
            index = -1
        self.langCombo.setCurrentIndex(index + 1)
        
    def saveSettings(self):
        """ save users last settings """
        s = QSettings()
        s.beginGroup('xml_import')
        for i in self.impChecks:
            s.setValue(i.objectName(), i.isChecked())
        for p in self.postChecks:
            s.setValue(p.objectName(), p.isChecked())
        index = self.langCombo.currentIndex()
        s.setValue('language', 'default' if index == 0 else _langlist[index-1])

