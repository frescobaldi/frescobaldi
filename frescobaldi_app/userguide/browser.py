# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2013 by Wilbert Berendsen
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
import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import helpers
import icons
import simplemarkdown

from . import __path__
from . import page


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
        self._toc = tb.addAction(icons.get('help-contents'), '')
        self._print = tb.addAction(icons.get('document-print'), '')
        self._back.triggered.connect(self.browser.backward)
        self._forw.triggered.connect(self.browser.forward)
        self._home.triggered.connect(self.home)
        self._toc.triggered.connect(self.toc)
        self._print.triggered.connect(self.print_)
        
        self.browser.sourceChanged.connect(self.slotSourceChanged)
        self.browser.historyChanged.connect(self.slotHistoryChanged)
        app.translateUI(self)
        self.loadSettings()
    
    def closeEvent(self, ev):
        self.saveSettings()
        super(Window, self).closeEvent(ev)
        
    def loadSettings(self):
        self.resize(QSettings().value("helpbrowser/size", QSize(400, 300), QSize))
    
    def saveSettings(self):
        QSettings().setValue("helpbrowser/size", self.size())
    
    def translateUI(self):
        self.setCaption()
        self._toolbar.setWindowTitle(_("Toolbar"))
        self._back.setText(_("Back"))
        self._forw.setText(_("Forward"))
        self._home.setText(_("Start"))
        self._toc.setText(_("Contents"))
        self._print.setText(_("Print"))
        
    def slotSourceChanged(self):
        self.setCaption()
    
    def setCaption(self):
        title = self.browser.documentTitle() or _("Help")
        self.setWindowTitle(app.caption(title) + " " + _("Help"))

    def slotHistoryChanged(self):
        self._back.setEnabled(self.browser.isBackwardAvailable())
        self._forw.setEnabled(self.browser.isForwardAvailable())
    
    def home(self):
        self.displayPage('index')
        
    def toc(self):
        self.displayPage('toc')
    
    def displayPage(self, name=None):
        """Opens the help browser showing the specified help page."""
        if name:
            self.browser.setSource(QUrl("help:" + name))
        self.show()
        self.activateWindow()
        self.raise_()
    
    def print_(self):
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle(app.caption(_("Print")))
        options = (QAbstractPrintDialog.PrintToFile
                   | QAbstractPrintDialog.PrintShowPageSize
                   | QAbstractPrintDialog.PrintPageRange)
        if self.browser.textCursor().hasSelection():
            options |= QAbstractPrintDialog.PrintSelection
        dlg.setOptions(options)
        if dlg.exec_():
            self.browser.print_(printer)


class Browser(QTextBrowser):
    def __init__(self, parent):
        super(Browser, self).__init__(parent)
        app.settingsChanged.connect(self.reload, 1)
        self.anchorClicked.connect(self.slotAnchorClicked)
        self.setOpenLinks(False)
        
    def slotAnchorClicked(self, url):
        url = self.source().resolved(url)
        if url.scheme() == "help":
            self.setSource(url)
        else:
            helpers.openUrl(url)
        
    def loadResource(self, type, url):
        if type == QTextDocument.HtmlResource:
            return Formatter().html(url.path())
        elif type == QTextDocument.ImageResource:
            url = QUrl.fromLocalFile(os.path.join(__path__[0], url.path()))
        return super(Browser, self).loadResource(type, url)
    
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and int(ev.modifiers()) == 0:
            self.window().close()
        super(Browser, self).keyPressEvent(ev)


class Formatter(object):
    def html(self, name):
        """Return a full userguide page HTML."""
        page_ = page.Page(name)
        from info import appname, version
        
        def format_link(name):
            title = simplemarkdown.html_escape(page.Page(name).title())
            return '<a href="{0}">{1}</a>'.format(name, title)
        
        # TODO get the parents
        parents = []
        
        qt_detail = '<qt type=detail>' if page_.is_popup() else ''
        title = page_.title()
        nav_up = ''
        if parents and not page_.is_popup():
            nav_up = '<p>{0} {1}</p>'.format(
                _("Up:"),
                ' '.join(map(format_link, parents)))
        body = self.markexternal(page_.body())
        nav_children, nav_next, nav_seealso = '', '', ''
        if page_.children():
            nav_children = '\n'.join(
                '<div>{0}</div>'.format(format_link(c))
                for c in page_.children())
        else:
            html = []
            for p in parents:
                i = p.children().index(page)
                if i < len(p.children()) - 1:
                    html.append('<div>{0} {1}</div>'.format(
                        _("Next:"), p.children()[i+1].link()))
            nav_next = '\n'.join(html)
        if page_.seealso():
            html = []
            html.append("<p>{0}</p>".format(_("See also:")))
            html.extend('<div>{0}</div>'.format(format_link(p))
                        for p in page_.seealso())
            nav_seealso = '\n'.join(html)
        return self._html_template().format(**locals())

    def markexternal(self, text):
        """Marks http(s)/ftp(s) links as external with an arrow."""
        pat = re.compile(r'''<a\s+.*?href\s*=\s*(['"])(ht|f)tps?.*?\1[^>]*>''', re.I)
        return pat.sub(r'\g<0>&#11008;', text)
    
    def _html_template(self):
        """Return the userguide html template to render the html().
        
        The default implementation returns _userguide_html_template.
        
        """
        return _userguide_html_template


_userguide_html_template = '''\
{qt_detail}<html>
<head>
<style type="text/css">
body {{
  margin: 10px;
}}
</style>
<title>{title}</title>
</head>
<body>
{nav_up}
{body}
{nav_children}
{nav_next}
{nav_seealso}
<br/><hr width=80%/>
<address><center>{appname} {version}</center></address>
</body>
</html>
'''

