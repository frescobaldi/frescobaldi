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

"""
The help browser window.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import icons

from . import __path__
from . import helpimpl


class Window(QMainWindow):
    """The help browser window."""
    def __init__(self):
        super(Window, self).__init__()
        self.setAttribute(Qt.WA_QuitOnClose, False)
        
        self.browser = Browser(self)
        self.setCentralWidget(self.browser)
        
        self._toolbar = tb = self.addToolBar('')
        self._back = tb.addAction(icons.get('go-previous'), '')
        self._forw = tb.addAction(icons.get('go-next'), '')
        self._home = tb.addAction(icons.get('go-home'), '')
        self._back.triggered.connect(self.browser.backward)
        self._forw.triggered.connect(self.browser.forward)
        self._home.triggered.connect(self.home)
        
        self.browser.sourceChanged.connect(self.slotSourceChanged)
        self.browser.historyChanged.connect(self.slotHistoryChanged)
        app.translateUI(self)
        self.loadSettings()
        app.qApp.aboutToQuit.connect(self.saveSettings)
    
    def loadSettings(self):
        self.resize(QSettings().value("helpbrowser/size", QSize(400, 300)))
    
    def saveSettings(self):
        QSettings().setValue("helpbrowser/size", self.size())
    
    def translateUI(self):
        self.setCaption()
        self._toolbar.setWindowTitle(_("Toolbar"))
        self._back.setText(_("Back"))
        self._forw.setText(_("Forward"))
    
    def slotSourceChanged(self):
        self.setCaption()
    
    def setCaption(self):
        title = self.browser.documentTitle() or _("Help")
        self.setWindowTitle(app.caption(title) + " " + _("Help"))

    def slotHistoryChanged(self):
        self._back.setEnabled(self.browser.isBackwardAvailable())
        self._forw.setEnabled(self.browser.isForwardAvailable())
    
    def home(self):
        self.displayHelp('contents')
        
    def displayHelp(self, page):
        """Opens the help browser showing the specified help page (by name or class)."""
        if isinstance(page, type) and issubclass(page, helpimpl.page):
            page = page.name
        self.browser.setSource(QUrl("help:{0}".format(page)))
        self.show()
        self.activateWindow()
        self.raise_()


class Browser(QTextBrowser):
    def __init__(self, parent):
        super(Browser, self).__init__(parent)
        app.languageChanged.connect(self.reload, -1)
        
    def loadResource(self, type, url):
        if type == QTextDocument.HtmlResource and url.scheme() == "help":
            return helpimpl.html(url.path())
        elif type == QTextDocument.ImageResource:
            url = QUrl.fromLocalFile(os.path.join(__path__[0], url.path()))
        return super(Browser, self).loadResource(type, url)
    
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and int(ev.modifiers()) == 0:
            self.window().hide()
        super(Browser, self).keyPressEvent(ev)


