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
A dialog to view LilyPond source.
"""


from PyQt5.QtCore import QSettings, QSize, Qt
from PyQt5.QtWidgets import QDialog, QLabel, QSizePolicy, QTextBrowser, QVBoxLayout


import app
import qutil
import highlighter
import textformats


class SourceViewer(QDialog):
    def __init__(self, browser):
        super(SourceViewer, self).__init__(browser.parentWidget())

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)

        self.urlLabel = QLabel(wordWrap=True)
        layout.addWidget(self.urlLabel)
        self.textbrowser = QTextBrowser()
        layout.addWidget(self.textbrowser)

        self.urlLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.textbrowser.setLineWrapMode(QTextBrowser.NoWrap)

        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        app.translateUI(self)
        qutil.saveDialogSize(self, "helpbrowser/sourceviewer/size", QSize(400, 300))

    def translateUI(self):
        self.setWindowTitle(app.caption(_("LilyPond Source")))

    def readSettings(self):
        data = textformats.formatData('editor')
        self.textbrowser.setPalette(data.palette())
        self.textbrowser.setFont(data.font)
        highlighter.highlight(self.textbrowser.document())

    def showReply(self, reply):
        reply.setParent(self)
        self.urlLabel.setText(reply.url().toString())
        self._reply = reply
        reply.finished.connect(self.loadingFinished)
        self.textbrowser.clear()
        self.show()

    def loadingFinished(self):
        data = self._reply.readAll()
        self._reply.close()
        self._reply.deleteLater()
        del self._reply
        self.textbrowser.clear()
        self.textbrowser.setText(str(data, 'utf-8', 'replace'))
        highlighter.highlight(self.textbrowser.document())

