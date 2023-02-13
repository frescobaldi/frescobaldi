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
The browser widget for the help browser.
"""


import os

from PyQt5.QtCore import QSettings, Qt, QUrl
from PyQt5.QtGui import QKeySequence
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QComboBox, QLineEdit, QMenu, QToolBar, QVBoxLayout, QWidget

import app
import icons
import helpers
import lilypondinfo
import lilydoc.manager
import lilydoc.network
import textformats


class Browser(QWidget):
    """LilyPond documentation browser widget."""
    def __init__(self, dockwidget):
        super(Browser, self).__init__(dockwidget)

        layout = QVBoxLayout(spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.toolbar = tb = QToolBar()
        self.webview = QWebEngineView(self, contextMenuPolicy=Qt.CustomContextMenu)
        self.webview.setPage(WebEnginePage(self.webview))
        self.chooser = QComboBox(sizeAdjustPolicy=QComboBox.AdjustToContents)
        self.search = SearchEntry(maximumWidth=200, clearButtonEnabled=True)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.webview)

        ac = dockwidget.actionCollection
        ac.help_back.triggered.connect(self.webview.back)
        ac.help_forward.triggered.connect(self.webview.forward)
        ac.help_home.triggered.connect(self.showHomePage)
        ac.help_web_browser_homepage.triggered.connect(self.openWebBrowserHomePage)
        ac.help_web_browser.triggered.connect(self.openWebBrowser)
        ac.help_print.triggered.connect(self.slotPrint)

        self.webview.urlChanged.connect(self.slotUrlChanged)
        self.webview.customContextMenuRequested.connect(self.slotShowContextMenu)

        tb.addAction(ac.help_back)
        tb.addAction(ac.help_forward)
        tb.addSeparator()
        tb.addAction(ac.help_home)
        tb.addAction(ac.help_web_browser)
        w = tb.widgetForAction(ac.help_web_browser)
        w.addAction(ac.help_web_browser_homepage)
        tb.addAction(ac.help_print)
        tb.addSeparator()
        tb.addWidget(self.chooser)
        tb.addWidget(self.search)

        self.chooser.activated[int].connect(self.showHomePage)
        self.search.textChanged.connect(self.slotSearchChanged)
        self.search.returnPressed.connect(self.slotSearchReturnPressed)
        dockwidget.mainwindow().iconSizeChanged.connect(self.updateToolBarSettings)
        dockwidget.mainwindow().toolButtonStyleChanged.connect(self.updateToolBarSettings)

        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        self.loadDocumentation()
        self.showInitialPage()
        app.settingsChanged.connect(self.loadDocumentation)
        app.translateUI(self)

    def readSettings(self):
        s = QSettings()
        s.beginGroup("documentation")
        ws = self.webview.page().settings()
        family = s.value("fontfamily", self.font().family(), str)
        size = s.value("fontsize", 16, int)
        ws.setFontFamily(QWebEngineSettings.StandardFont, family)
        ws.setFontSize(QWebEngineSettings.DefaultFontSize, size)
        fixed = textformats.formatData('editor').font
        ws.setFontFamily(QWebEngineSettings.FixedFont, fixed.family())
        ws.setFontSize(QWebEngineSettings.DefaultFixedFontSize, int(fixed.pointSizeF() * 96 / 72))
        self.webview.page().profile().setHttpAcceptLanguage(','.join(lilydoc.network.langs()))

    def keyPressEvent(self, ev):
        if ev.text() == "/":
            self.search.setFocus()
        else:
            super(Browser, self).keyPressEvent(ev)

    def translateUI(self):
        try:
            self.search.setPlaceholderText(_("Search..."))
        except AttributeError:
            pass # not in Qt 4.6

    def showInitialPage(self):
        """Shows the preferred start page.

        If a local documentation instance already has a suitable version,
        just loads it. Otherwise connects to the allLoaded signal, that is
        emitted when all the documentation instances have loaded their version
        information and then shows the start page (if another page wasn't yet
        loaded).

        """
        if self.webview.url().isEmpty():
            docs = lilydoc.manager.docs()
            version = lilypondinfo.preferred().version()
            index = -1
            if version:
                for num, doc in enumerate(docs):
                    if doc.version() is not None and doc.version() >= version:
                        index = num # a suitable documentation is found
                        break
            if index == -1:
                # nothing found (or LilyPond version not available),
                # wait for loading or show the most recent version
                if not lilydoc.manager.loaded():
                    lilydoc.manager.allLoaded.connect(self.showInitialPage)
                    return
                index = len(docs) - 1
            self.chooser.setCurrentIndex(index)
            self.showHomePage()

    def loadDocumentation(self):
        """Puts the available documentation instances in the combobox."""
        i = self.chooser.currentIndex()
        self.chooser.clear()
        for doc in lilydoc.manager.docs():
            v = doc.versionString()
            if doc.isLocal():
                t = _("(local)")
            else:
                t = _("({hostname})").format(hostname=doc.url().host())
            self.chooser.addItem("{0} {1}".format(v or _("<unknown>"), t))
        self.chooser.setCurrentIndex(i)
        if not lilydoc.manager.loaded():
            lilydoc.manager.allLoaded.connect(self.loadDocumentation, -1)
            return

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
        helpers.openUrl(reply.url())

    def slotSearchChanged(self):
        text = self.search.text()
        if not text.startswith(':'):
            self.webview.page().findText(text)

    def slotSearchReturnPressed(self):
        text = self.search.text()
        if not text.startswith(':'):
            self.slotSearchChanged()
        else:
            pass # TODO: implement full doc search

    def sourceViewer(self):
        try:
            return self._sourceviewer
        except AttributeError:
            from . import sourceviewer
            self._sourceviewer = sourceviewer.SourceViewer(self)
            return self._sourceviewer

    def getHomePageUrl(self):
        """Returns the URL of the LilyPond documentation."""
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
        return url

    def showHomePage(self):
        self.webview.load(self.getHomePageUrl())

    def openWebBrowser(self):
        helpers.openUrl(self.webview.url())

    def openWebBrowserHomePage(self):
        helpers.openUrl(self.getHomePageUrl())

    def slotPrint(self):
        printer = self._printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle(app.caption(_("Print")))
        if dlg.exec_():
            self.webview.page().print(printer, self.slotPrintingDone)

    def slotPrintingDone(self, success):
        del self._printer

    def slotShowContextMenu(self, pos):
        d = self.webview.page().contextMenuData()
        menu = QMenu()
        if d.linkUrl().isValid():
            a = self.webview.pageAction(QWebEnginePage.CopyLinkToClipboard)
            a.setIcon(icons.get("edit-copy"))
            a.setText(_("Copy &Link"))
            menu.addAction(a)
            menu.addSeparator()
            a = menu.addAction(icons.get("internet-web-browser"), _("Open Link in Web Browser"))
            a.triggered.connect((lambda url: lambda: self.slotNewWindow(url))(d.linkUrl()))
        else:
            if d.selectedText():
                a = self.webview.pageAction(QWebEnginePage.Copy)
                a.setIcon(icons.get("edit-copy"))
                a.setText(_("&Copy"))
                menu.addAction(a)
                menu.addSeparator()
            a = menu.addAction(icons.get("internet-web-browser"), _("Open Current Page in Web Browser"))
            a.triggered.connect((lambda url: lambda: self.slotNewWindow(url))(self.webview.url()))
        if menu.actions():
            menu.exec_(self.webview.mapToGlobal(pos))

    def slotNewWindow(self, url):
        helpers.openUrl(url)


class SearchEntry(QLineEdit):
    """A line edit that clears itself when ESC is pressed."""
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape:
            if self.text():
                self.clear()
            else:
                webview = self.parentWidget().parentWidget().webview
                webview.setFocus()
                webview.page().findText(None)
        elif any(ev.matches(key) for key in (
            QKeySequence.MoveToNextLine, QKeySequence.MoveToPreviousLine,
            QKeySequence.MoveToNextPage, QKeySequence.MoveToPreviousPage,
                )):
            webview = self.parentWidget().parentWidget().webview
            webview.keyPressEvent(ev)
        else:
            super(SearchEntry, self).keyPressEvent(ev)


class WebEnginePage(QWebEnginePage):
    """QWebEnginePage that shows LY files using the source viewer."""
    def acceptNavigationRequest(self, url, type, isMainFrame):
        if url.path().endswith(('.ily', '.lyi', '.ly')):
            self.view().parent().sourceViewer().showReply(lilydoc.network.get(url))
            return False
        return super().acceptNavigationRequest(url, type, isMainFrame)
