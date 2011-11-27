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
The browser widget for the help browser.
"""

from __future__ import unicode_literals

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

import app
import lilypondinfo
import lilydoc.manager
import lilydoc.network


class Browser(QWidget):
    """We use an embedded QMainWindow so we can add a toolbar nicely."""
    def __init__(self, dockwidget):
        super(Browser, self).__init__(dockwidget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.toolbar = tb = QToolBar()
        self.webview = QWebView()
        self.chooser = QComboBox(sizeAdjustPolicy=QComboBox.AdjustToContents)
        self.chooser.activated[int].connect(self.showHomePage)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.webview)
        
        ac = dockwidget.actionCollection
        ac.help_back.triggered.connect(self.webview.back)
        ac.help_forward.triggered.connect(self.webview.forward)
        ac.help_home.triggered.connect(self.showHomePage)
        
        self.webview.page().setNetworkAccessManager(lilydoc.network.accessmanager())
        self.webview.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.webview.page().linkClicked.connect(self.openUrl)
        self.webview.page().setForwardUnsupportedContent(True)
        self.webview.page().unsupportedContent.connect(self.slotUnsupported)
        self.webview.urlChanged.connect(self.slotUrlChanged)
        
        tb.addAction(ac.help_back)
        tb.addAction(ac.help_forward)
        tb.addSeparator()
        tb.addAction(ac.help_home)
        tb.addSeparator()
        tb.addWidget(self.chooser)
        
        dockwidget.mainwindow().iconSizeChanged.connect(self.updateToolBarSettings)
        dockwidget.mainwindow().toolButtonStyleChanged.connect(self.updateToolBarSettings)
        
        self.loadDocumentation()
        self.showInitialPage()
        app.settingsChanged.connect(self.loadDocumentation)
    
    def showInitialPage(self):
        """Shows the preferred start page if all docs have their version loaded."""
        if self.webview.url().isEmpty():
            if not lilydoc.manager.loaded():
                lilydoc.manager.allLoaded.connect(self.showInitialPage)
                return
            # all are loaded
            docs = lilydoc.manager.docs()
            version = lilypondinfo.preferred().version
            index = len(docs) - 1
            if version:
                for num, doc in enumerate(docs):
                    if doc.version() >= version:
                        index = num
                        break
            self.chooser.setCurrentIndex(index)
            self.showHomePage()
    
    def loadDocumentation(self):
        """Puts the available documentation instances in the combobox."""
        if not lilydoc.manager.loaded():
            lilydoc.manager.allLoaded.connect(self.loadDocumentation, -1)
            return
        self.chooser.clear()
        for doc in lilydoc.manager.docs():
            v = doc.versionString() or _("<unknown>")
            if doc.isLocal():
                t = _("(local)")
            else:
                t = _("({hostname})").format(hostname=doc.url().host())
            self.chooser.addItem("{0} {1}".format(v, t))
        
    def updateToolBarSettings(self):
        mainwin = self.parentWidget().mainwindow()
        self.toolbar.setIconSize(mainwin.iconSize())
        self.toolbar.setToolButtonStyle(mainwin.toolButtonStyle())
        
    def showManual(self):
        """Invoked when the user presses F1."""
        self.slotHomeFrescobaldi() # TEMP
        
    def slotUrlChanged(self):
        ac = self.parentWidget().actionCollection
        ac.help_back.setEnabled(self.webview.history().canGoBack())
        ac.help_forward.setEnabled(self.webview.history().canGoForward())
    
    def openUrl(self, url):
        if url.path().endswith(('.ily', '.lyi', '.ly')):
            self.sourceViewer().showReply(lilydoc.network.get(url))
        else:
            self.webview.load(url)
    
    def slotUnsupported(self, reply):
        QDesktopServices.openUrl(reply.url())
    
    def sourceViewer(self):
        try:
            return self._sourceviewer
        except AttributeError:
            from . import sourceviewer
            self._sourceviewer = sourceviewer.SourceViewer(self)
            return self._sourceviewer
    
    def showHomePage(self):
        """Shows the homepage of the LilyPond documentation."""
        i = self.chooser.currentIndex()
        if i < 0:
            i = 0
        doc = lilydoc.manager.docs()[i]
        
        url = doc.home()
        if doc.isLocal():
            path = url.toLocalFile()
            langs = lilydoc.network.langs()
            if langs:
                for lang in langs:
                    if os.path.exists(path + '.' + lang + '.html'):
                        path += '.' + lang
                        break
            url = QUrl.fromLocalFile(path + '.html')
        self.webview.load(url)


