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
import network
import textformats
import highlighter

from . import html


class Browser(QWidget):
    """We use an embedded QMainWindow so we can add a toolbar nicely."""
    def __init__(self, dockwidget):
        super(Browser, self).__init__(dockwidget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.toolbar = tb = QToolBar()
        layout.addWidget(self.toolbar)
        self.webview = QWebView()
        layout.addWidget(self.webview)
        
        ac = dockwidget.actionCollection
        ac.help_back.triggered.connect(self.webview.back)
        ac.help_forward.triggered.connect(self.webview.forward)
        ac.help_home.triggered.connect(self.showHomePage)
        ac.help_home_lilypond.triggered.connect(self.showLilyPondHome)
        
        self.webview.page().setNetworkAccessManager(network.accessmanager())
        self.webview.page().setForwardUnsupportedContent(True)
        self.webview.page().unsupportedContent.connect(self.slotUnsupported)
        self.webview.urlChanged.connect(self.slotUrlChanged)
        
        tb.addAction(ac.help_back)
        tb.addAction(ac.help_forward)
        tb.addSeparator()
        tb.addAction(ac.help_home)
        tb.addAction(ac.help_home_lilypond)
        
        dockwidget.mainwindow().iconSizeChanged.connect(self.updateToolBarSettings)
        dockwidget.mainwindow().toolButtonStyleChanged.connect(self.updateToolBarSettings)
        
        self.showHomePage() # show an initial welcome page
    
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
    
    def slotUnsupported(self, reply):
        if reply.url().path().endswith(('.ily', '.lyi', '.ly')):
            # TODO: display ly in small window, or highlighted as html etc.
            self.lyViewer().showReply(reply)
            #data = reply.readAll()
            #dataurl = "data:text/html;charset=UTF-8,<html><pre>{0}</pre></html>".format(data)
            #self.webview.load(QUrl(dataurl))
        else:
            QDesktopServices.openUrl(reply.url())
    
    def lyViewer(self):
        try:
            return self._lyviewer
        except AttributeError:
            self._lyviewer = LyViewer(self)
            return self._lyviewer
    
    def showHomePage(self):
        """Shows an initial welcome page."""
        self.webview.setHtml(html.welcome())
        
    def showLilyPondHome(self):
        """Shows the homepage of the LilyPond documentation."""
        #self.webview.load(QUrl("http://lilypond.org/doc")) # TEMP!!!
        self.webview.load(QUrl.fromLocalFile("/usr/share/doc/lilypond/html/index.html")) # TEMP



class LyViewer(QDialog):
    def __init__(self, browser):
        super(LyViewer, self).__init__(browser)

        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.urlLabel = QLabel(wordWrap=True)
        layout.addWidget(self.urlLabel)
        self.textbrowser = QTextBrowser()
        layout.addWidget(self.textbrowser)
        
        self.textbrowser.setLineWrapMode(QTextBrowser.NoWrap)
        
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        app.translateUI(self)
        
    def translateUI(self):
        self.setWindowTitle(app.caption(_("LilyPond Source")))
        
    def readSettings(self):
        self.textbrowser.setFont(textformats.formatData('editor').font)
        
    def showReply(self, reply):
        self.urlLabel.setText(reply.url().toString())
        self.textbrowser.setText(unicode(reply.readAll(), 'utf-8', 'replace'))
        self.resize(QSettings().value("helpbrowser/sourcedialogsize", QSize(400, 300)))
        self.show()
        highlighter.highlight(self.textbrowser.document())
        
    def resizeEvent(self, ev):
        QSettings().setValue("helpbrowser/sourcedialogsize", ev.size())


