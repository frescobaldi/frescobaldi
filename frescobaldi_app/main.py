# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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
Entry point of Frescobaldi.
"""

import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

import os
import re

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QApplication, QTextCursor

import info             # Information about our application
import app              # Construct QApplication
import po               # Setup language
import mainwindow       # contains MainWindow class
import session          # Initialize QSessionManager support
import document

if app.qApp.isSessionRestored():
    # Restore session, we are started by the session manager
    session.restoreSession()
else:
    # Just create one MainWindow
    win = mainwindow.MainWindow()
    
    # Parse command line arguments
    import optparse
    parser = optparse.OptionParser(
        usage = _("usage: {appname} [options] file ...").format(appname=info.name),
        version = "{0} {1}".format(info.name, info.version))
    parser.add_option('-e', '--encoding', metavar=_("ENC"),
        help=_("Encoding to use"))
    parser.add_option('-l', '--line', type="int", metavar=_("NUM"),
        help=_("Line number to go to, starting at 1"))
    parser.add_option('-c', '--column', type="int", metavar=_("NUM"),
        help=_("Column to go to, starting at 0"))
    parser.add_option('--start', metavar=_("NAME"),
        help=_("Session to start"), dest="session")

    options, files = parser.parse_args(QApplication.arguments()[1:])

    if options.session:
        app.startSession(options.session)
    
    win.show()
    
    # make urls
    urls = []
    for arg in files:
        if re.match(r'^(https?|s?ftp)://', arg):
            url = QUrl(arg)
        elif arg.startswith('file://'):
            url = QUrl.fromLocalFile(arg[7:])
        elif arg.startswith('file:'):
            url = QUrl.fromLocalFile(os.path.abspath(arg[5:]))
        else:
            url = QUrl.fromLocalFile(os.path.abspath(arg))
        urls.append(url)
    
    docs = [win.openUrl(url, options.encoding) for url in urls]
    if docs:
        # set the last document active and apply navigation if requested
        doc = docs[-1]
        win.setCurrentDocument(doc)
        if options.line is not None:
            cursor = QTextCursor(doc)
            cursor.setPosition(doc.findBlockByNumber(options.line - 1).position() + (options.column or 0))
            win.currentView().setTextCursor(cursor)
    else:
        # just create one empty and nameless document
        win.setCurrentDocument(document.Document())

app.run()
