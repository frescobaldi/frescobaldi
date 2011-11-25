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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

import app
import network
import lilypondinfo
import lilydoc.manager


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
        
        self.webview.page().setNetworkAccessManager(network.accessmanager())
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
            docs = lilydoc.manager.docs()
            for doc in docs:
                if doc.version() is None:
                    doc.versionLoaded.connect(self.showInitialPage)
                    return
            # all are loaded
            version = lilypondinfo.preferred().version
            if version:
                for num, doc in enumerate(docs):
                    if doc.version() >= version:
                        self.chooser.setCurrentIndex(num)
                        break
                else:
                    self.chooser.setCurrentIndex(len(docs) - 1)
            self.showHomePage()
    
    def loadDocumentation(self):
        """Puts the available documentation instances in the combobox."""
        docs = lilydoc.manager.docs()
        self.chooser.clear()
        self.chooser.addItems([''] * len(docs))
        def settext(num, doc):
            v = doc.versionString()
            if doc.isLocal():
                t = _("(local)")
            else:
                t = _("({hostname})").format(hostname=doc.url().host())
            self.chooser.setItemText(num, "{0} {1}".format(v, t))
            
        for n, doc in enumerate(docs):
            if doc.version() is not None:
                settext(n, doc)
            else:
                def makefunc(n, doc):
                    def func():
                        settext(n, doc)
                        doc.versionLoaded.disconnect(func)
                    return func
                doc.versionLoaded.connect(makefunc(n, doc))
        
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
            self.sourceViewer().showReply(network.get(url))
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
        doc = lilydoc.manager.docs()[self.chooser.currentIndex()]
        
        url = doc.home()
        if doc.isLocal():
            # TODO: language
            url = QUrl.fromLocalFile(url.toLocalFile() + '.html')
        self.webview.load(url)


