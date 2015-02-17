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
Generic import dialog. Presuppose a child instance for the specific import.
"""

from __future__ import unicode_literals

import os
import subprocess

from PyQt4.QtGui import (QCheckBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QTabWidget, QTextEdit, QWidget)

import userguide
import lilypondinfo
import widgets


class ToLyDialog(QDialog):
	
    def __init__(self, parent=None):
        super(ToLyDialog, self).__init__(parent)
        self._document = None
        self._path = None
        
        mainLayout = QGridLayout()
        self.setLayout(mainLayout)
        
        tabs = QTabWidget()
        
        import_tab = QWidget()
        post_tab = QWidget()
        
        itabLayout = QGridLayout(import_tab)
        ptabLayout = QGridLayout(post_tab)
        
        tabs.addTab(import_tab, self.imp_prgm)
        tabs.addTab(post_tab, "after import")

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
        
        self.formatCheck.setObjectName("reformat")
        self.trimDurCheck.setObjectName("trim-durations")
        self.removeScalesCheck.setObjectName("remove-scaling")
        self.runEngraverCheck.setObjectName("engrave-directly")
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        userguide.addButton(self.buttons, self.userg)
        
        row = 0
        for r, w in enumerate(self.impChecks):
            row += r
            itabLayout.addWidget(w, row, 0, 1, 2)
            w.toggled.connect(self.makeCommandLine)
        row += 1    
        for r, w in enumerate(self.impExtra):
            row += r 
            itabLayout.addWidget(w, row, 0, 1, 2)
        
        itabLayout.addWidget(widgets.Separator(), row + 1, 0, 1, 2)
        itabLayout.addWidget(self.commandLineLabel, row + 2, 0, 1, 2)
        itabLayout.addWidget(self.commandLine, row + 2, 0, 1, 2)
        
        ptabLayout.addWidget(self.formatCheck, 0, 0, 1, 2)
        ptabLayout.addWidget(self.trimDurCheck, 1, 0, 1, 2)       
        ptabLayout.addWidget(self.removeScalesCheck, 2, 0, 1, 2)
        ptabLayout.addWidget(self.runEngraverCheck, 3, 0, 1, 2)
        ptabLayout.setRowStretch(4, 10)
        
        mainLayout.addWidget(tabs, 0, 0, 9, 2)
        mainLayout.addWidget(self.buttons, 10, 0, 1, 2)
        
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
    
    def translateUI(self):
        self.commandLineLabel.setText(_("Command line:"))
        self.formatCheck.setText(_("Reformat source"))
        self.trimDurCheck.setText(_("Trim durations (Make implicit per line)"))
        self.removeScalesCheck.setText(_("Remove fraction duration scaling"))
        self.runEngraverCheck.setText(_("Engrave directly"))
    
    def setDocument(self, path):
        """Set the full path to the MusicXML document."""
        self._document = path
    
    def getCmd(self):
        """Returns the command line."""
        cmd = []
        for t in self.commandLine.toPlainText().split():
            if t == '$musicxml2ly':
                cmd.extend(lilypondinfo.preferred().toolcommand('musicxml2ly'))
            elif t == '$midi2ly':
                cmd.extend(lilypondinfo.preferred().toolcommand('midi2ly'))
            elif t == '$abc2ly':
                cmd.extend(lilypondinfo.preferred().toolcommand('abc2ly'))
            elif t == '$filename':
                cmd.append(self._document)
            else:
                cmd.append(t)
        cmd.extend(['--output', '-'])
        return cmd
        
    def run_command(self):
        """Run command line."""
        cmd = self.getCmd()
        directory = os.path.dirname(self._document)
        proc = subprocess.Popen(cmd, cwd=directory,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE)
        stdouterr = proc.communicate()
        return stdouterr
		
    def getPostSettings(self):
        """Returns settings in the post import tab."""
        post = []
        for p in self.postChecks:
            post.append(p.isChecked())
        return post
        
    def loadSettings(self):
        """Get users previous settings."""
        post_default = [True, False, False, True]
        for i, d in zip(self.impChecks, self.imp_default):
            i.setChecked(self.settings.value(i.objectName(), d, bool))
        for p, f in zip(self.postChecks, post_default):
            p.setChecked(self.settings.value(p.objectName(), f, bool))
        
    def saveSettings(self):
        """Save users last settings."""
        for i in self.impChecks:
            self.settings.setValue(i.objectName(), i.isChecked())
        for p in self.postChecks:
            self.settings.setValue(p.objectName(), p.isChecked())
