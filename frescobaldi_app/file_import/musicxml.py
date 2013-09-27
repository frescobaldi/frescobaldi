# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
import collections

from PyQt4.QtCore import QSettings, QSize
from PyQt4.QtGui import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QTextEdit)

import app
import documentinfo
import help
import icons
import job
import jobmanager
import lilypondinfo
import listmodel
import widgets
import qutil
import util


class Dialog(QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self._document = None
        self._path = None
        
        layout = QGridLayout()
        self.setLayout(layout)
        
        
        self.noartCheck = QCheckBox()
        self.norestCheck = QCheckBox()
        self.nolayoutCheck = QCheckBox()
        self.nobeamCheck = QCheckBox()
        
        self.commandLineLabel = QLabel()
        self.commandLine = QTextEdit(acceptRichText=False)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        help.addButton(self.buttons, help_importXML)
        

        layout.addWidget(self.noartCheck, 0, 0, 1, 2)
        layout.addWidget(self.norestCheck, 1, 0, 1, 2)
        layout.addWidget(self.nolayoutCheck, 2, 0, 1, 2)
        layout.addWidget(self.nobeamCheck, 3, 0, 1, 2)
        layout.addWidget(self.commandLineLabel, 4, 0, 1, 2)
        layout.addWidget(self.commandLine, 5, 0, 1, 2)
        layout.addWidget(widgets.Separator(), 6, 0, 1, 2)
        layout.addWidget(self.buttons, 7, 0, 1, 2)
        
        app.translateUI(self)
        qutil.saveDialogSize(self, "importXML/dialog/size", QSize(480, 260))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        self.noartCheck.toggled.connect(self.makeCommandLine)
        self.norestCheck.toggled.connect(self.makeCommandLine)
        self.nolayoutCheck.toggled.connect(self.makeCommandLine)
        self.nobeamCheck.toggled.connect(self.makeCommandLine)
        self.makeCommandLine()
    
    def translateUI(self):
        self.setWindowTitle(app.caption(_("Import Music XML")))
        self.noartCheck.setText(_("No articulation directions"))
        self.norestCheck.setText(_("No rest positions"))
        self.nolayoutCheck.setText(_("No page layout"))
        self.nobeamCheck.setText(_("Auto beaming"))
        self.commandLineLabel.setText(_("Command line:"))
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run musicxml2ly"))

    
    def setDocument(self, doc, path):
        self._document = doc
        self._path = path
    
    def makeCommandLine(self):
        """Reads the widgets and builds a command line."""
        cmd = ["$musicxml2ly"]
        if self.noartCheck.isChecked():
            cmd.append('--nd')
        if self.norestCheck.isChecked():
            cmd.append('--nrp')
        if self.nolayoutCheck.isChecked():
            cmd.append('--npl')
        if self.nobeamCheck.isChecked():
            cmd.append('--no-beaming')

        cmd.append("$filename")
        self.commandLine.setText(' '.join(cmd))
    
    def getCmd(self):
        """Returns the command line."""
        cmd = []
        for t in self.commandLine.toPlainText().split():
            if t == '$musicxml2ly':
                cmd.append('musicxml2ly')
            elif t == '$filename':
                cmd.append(self._document)
            else:
                cmd.append(t)
        return cmd
        
    def run_command(self):
        cmd = self.getCmd()
        os.chdir(self._path)
        stdouterr = os.popen4(cmd)[1].read() #subprocess.Popen?
        return stdouterr
    	


class help_importXML(help.page):
    def title():
        return _("Import Music XML")
    
    def body():
        p = '<p>{0}</p>\n'.format
        text = [p(_("""\
In this dialog you can set some parameters for the musicxml2ly import.
"""))]
        text.append(p(_("The following replacements will be made:")))
        text.append('<dl>\n')
        for name, msg in (
            ('$musicxml2ly', _("The musicxml2ly executable")),
            ('$filename', _("The filename of the document")),
            ):
            text.append('<dt><code>{0}</code></dt>'.format(name))
            text.append('<dd>{0}</dd>\n'.format(msg))
        text.append('</dl>')
        return ''.join(text)



