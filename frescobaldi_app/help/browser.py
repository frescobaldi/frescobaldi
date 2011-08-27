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

from . import __path__


class Window(QMainWindow):
    """The help browser window."""
    def __init__(self):
        super(Window, self).__init__()
        self.setAttribute(Qt.WA_QuitOnClose, False)
        
        self.browser = Browser(self)
        self.setCentralWidget(self.browser)
        
        self.browser.sourceChanged.connect(self.translateUI)
        app.translateUI(self)
        self.loadSettings()
        app.qApp.aboutToQuit.connect(self.saveSettings)
    
    def loadSettings(self):
        self.resize(QSettings().value("helpbrowser/size", QSize(400, 300)))
    
    def saveSettings(self):
        QSettings().setValue("helpbrowser/size", self.size())
    
    def translateUI(self):
        title = self.browser.documentTitle() or _("Help")
        self.setWindowTitle(app.caption(title))
        
    def displayHelp(self, name):
        """Opens the help browser showing the help at name."""
        self.browser.setSource(QUrl("help:{0}".format(name)))
        self.show()
        self.activateWindow()
        self.raise_()


class Browser(QTextBrowser):
    def __init__(self, parent):
        super(Browser, self).__init__(parent)
        app.languageChanged.connect(self.reload, -1)
        
    def loadResource(self, type, url):
        if type == QTextDocument.HtmlResource and url.scheme() == "help":
            return html(url.path())
        elif type == QTextDocument.ImageResource:
            url = QUrl.fromLocalFile(os.path.join(__path__[0], url.path()))
        return super(Browser, self).loadResource(type, url)
    
    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape and int(ev.modifiers()) == 0:
            self.window().hide()
        super(Browser, self).keyPressEvent(ev)


def html(name):
    """Returns the HTML for the named help item."""
    from . import contents
    help = contents.all_pages.get(name, contents.nohelp)
    link = lambda h: '<div><a href="help:{0}">{1}</a><div>\n'.format(h.name, h.title())
    html = []
    if help.popup:
        html.append('<qt type=detail>')
    html.append('<html><head><title>{0}</title></head><body><h3>{0}</h3>'.format(help.title()))
    html.append(help.body())
    html.extend(map(link, help.children()))
    seealso = help.seealso()
    if seealso:
        html.append("<hr/><p>{0}</p>".format(_("See also:")))
        html.extend(map(link, seealso))
    html.append('</body></html>')
    return ''.join(html)

