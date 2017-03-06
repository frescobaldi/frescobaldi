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
The Document statistics dialog.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import userguide
import documentinfo

class DocumentStatisticsDialog(QDialog):
    """
    A dialog to analyse the current score and produce
    statistical data.
    """

    def __init__(self, mainwindow):
        super(DocumentStatisticsDialog, self).__init__(mainwindow)
        self.mainwindow = mainwindow
        self.addAction(mainwindow.actionCollection.help_whatsthis)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.resultField = QTextEdit()
        self.resultField.setReadOnly(True)
        layout.addWidget(self.resultField)

        b = self.dialogButtons = QDialogButtonBox()
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "docstatistics")
        self.runButton = b.addButton('', QDialogButtonBox.ActionRole)
        self.runButton.clicked.connect(self.doStatistics)
        self.settingsButton = b.addButton('', QDialogButtonBox.ActionRole)
        layout.addWidget(b)
        

        app.translateUI(self)

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Document Statistics")))
        self.runButton.setText(_("&Run"))
        self.runButton.setToolTip(_(
            "Runs and displays statistics."))
        self.settingsButton.setText(_("&Settings..."))
        self.settingsButton.setToolTip(_("Configure document statistics."))
        
    def doStatistics(self):
        print "do statistics"
        doc = self.mainwindow.currentDocument()
        mustree = documentinfo.music(doc)
        self.resultField.setText(mustree.dump())
