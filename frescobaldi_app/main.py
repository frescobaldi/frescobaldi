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
Entry point of Frescobaldi.
"""

from __future__ import unicode_literals

import sip
sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

import os
import re
import sys

from PyQt4.QtCore import QSettings, QTimer, QUrl
from PyQt4.QtGui import QApplication, QTextCursor

from . import toplevel  # Find all modules and packages as toplevel
import info             # Information about our application
import app              # Construct QApplication
import install          # Update QSettings structure etc. if needed
import guistyle         # Setup GUI style
import po.setup         # Setup language
import remote           # IPC with other Frescobaldi instances


def parse_commandline():
    """Parses the command line; returns options and filenames.
    
    If --version, --help or invalid options were given, the application will
    exit.
    
    """
    import optparse
    optparse._ = _ # let optparse use our translations
    parser = optparse.OptionParser(
        usage = _("{appname} [options] file ...").format(appname=info.name),
        version = "{0} {1}".format(info.appname, info.version),
        description = _("A LilyPond Music Editor"))
    parser.add_option('-e', '--encoding', metavar=_("ENC"),
        help=_("Encoding to use"))
    parser.add_option('-l', '--line', type="int", metavar=_("NUM"),
        help=_("Line number to go to, starting at 1"))
    parser.add_option('-c', '--column', type="int", metavar=_("NUM"),
        help=_("Column to go to, starting at 0"), default=0)
    parser.add_option('--start', metavar=_("NAME"),
        help=_("Session to start ('{none}' for empty session)").format(none="-"),
        dest="session")
    parser.add_option('--list-sessions', action="store_true", default=False,
        help=_("List the session names and exit"))
    parser.add_option('-n', '--new', action="store_true", default=False,
        help=_("Always start a new instance"))
    
    # Make sure debugger options are recognized as valid. These are passed automatically
    # from PyDev in Eclipse to the inferior process.
    if "pydevd" in sys.modules:
        parser.add_option('-v', '--vm_type')
        parser.add_option('-a', '--client')
        parser.add_option('-p', '--port')
        parser.add_option('-f', '--file')
        parser.add_option('-o', '--output')



    args = QApplication.arguments()
    if os.name == 'nt' and args and 'python' in os.path.basename(args[0]).lower():
        args = args[2:]
    else:
        args = args[1:]
    options, files = parser.parse_args(args)
    return options, files


def url(arg):
    """Converts a filename-like argument to a QUrl."""
    if re.match(r'^(https?|s?ftp)://', arg):
        return QUrl(arg)
    elif arg.startswith('file://'):
        return QUrl.fromLocalFile(os.path.abspath(arg[7:]))
    elif arg.startswith('file:'):
        return QUrl.fromLocalFile(os.path.abspath(arg[5:]))
    else:
        return QUrl.fromLocalFile(os.path.abspath(arg))


def main():
    """Main function."""
    options, files = parse_commandline()
    
    if options.list_sessions:
        import sessions
        for name in sessions.sessionNames():
            sys.stdout.write(name + '\n')
        sys.exit(0)
        
    urls = list(map(url, files))
    
    if not app.qApp.isSessionRestored():
        if not options.new and remote.enabled():
            api = remote.get()
            if api:
                api.command_line(options, urls)
                api.close()
                sys.exit(0)
    
        if QSettings().value("splash_screen", True, bool):
            import splashscreen
            splashscreen.show()

    # application icon
    import icons
    QApplication.setWindowIcon(icons.get("frescobaldi"))
    
    QTimer.singleShot(0, remote.setup)  # Start listening for IPC
    
    import mainwindow       # contains MainWindow class
    import session          # Initialize QSessionManager support
    import sessions         # Initialize our own named session support

    # boot Frescobaldi-specific stuff that should be running on startup
    import viewhighlighter  # highlight arbitrary ranges in text
    import progress         # creates progress bar in view space
    import musicpos         # shows music time in statusbar
    import autocomplete     # auto-complete input
    import wordboundary     # better wordboundary behaviour for the editor
    
    if sys.platform.startswith('darwin'):
        import macosx.setup
    
    if app.qApp.isSessionRestored():
        # Restore session, we are started by the session manager
        session.restoreSession()
        return

    # load specified session?
    doc = None
    if options.session and options.session != "-":
        doc = sessions.loadSession(options.session)
    
    # Just create one MainWindow
    win = mainwindow.MainWindow()
    win.show()
    
    # load documents given as arguments
    for u in urls:
        doc = win.openUrl(u, options.encoding)
    
    # were documents loaded?
    if not doc:
        if app.documents:
            doc = app.documents[-1]
        elif not options.session:
            # no docs, load default session
            doc = sessions.loadDefaultSession()
    
    if doc:
        win.setCurrentDocument(doc)
    else:
        win.cleanStart()
    
    if urls and options.line is not None:
        # set the last loaded document active and apply navigation if requested
        pos = doc.findBlockByNumber(options.line - 1).position() + options.column
        cursor = QTextCursor(doc)
        cursor.setPosition(pos)
        win.currentView().setTextCursor(cursor)
        win.currentView().centerCursor()


main()

sys.displayhook = app.displayhook
