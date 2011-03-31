# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
The browser widget for the help browser.
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *


import app


class Browser(QMainWindow):
    """We use an embedded QMainWindow so we can add a toolbar nicely."""
    def __init__(self, dockwidget):
        super(Browser, self).__init__(dockwidget)
        self.setWindowFlags(Qt.Widget)
        self.webview = QWebView()
        self.setCentralWidget(self.webview)
        
        ac = dockwidget.actionCollection
        ac.help_back.triggered.connect(self.webview.back)
        ac.help_forward.triggered.connect(self.webview.forward)
        ac.help_home_frescobaldi.triggered.connect(self.slotHomeFrescobaldi)
        ac.help_home_lilypond.triggered.connect(self.slotHomeLilyPond)
        
        self.webview.urlChanged.connect(self.slotUrlChanged)
        
        self._toolbar = tb = self.addToolBar('')
        tb.addAction(ac.help_back)
        tb.addAction(ac.help_forward)
        tb.addSeparator()
        tb.addAction(ac.help_home_lilypond)
        tb.addAction(ac.help_home_frescobaldi)
        
        
        self.slotUrlChanged()
        app.translateUI(self)
        
    def translateUI(self):
        self._toolbar.setWindowTitle(_("Help Browser Toolbar"))
        
    def showManual(self):
        """Invoked when the user presses F1."""
        self.slotHomeFrescobaldi() # TEMP
        
    def slotUrlChanged(self):
        ac = self.parentWidget().actionCollection
        ac.help_back.setEnabled(self.webview.history().canGoBack())
        ac.help_forward.setEnabled(self.webview.history().canGoForward())
        


    def slotHomeFrescobaldi(self):
        self.webview.load(QUrl("http://www.frescobaldi.org/")) # TEMP!!!
        
    def slotHomeLilyPond(self):
        self.webview.load(QUrl("http://lilypond.org/doc")) # TEMP!!!
        