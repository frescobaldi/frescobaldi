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


import os
import re
import sys

from PyQt5.QtCore import QSettings, QTimer, QUrl
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication

import appinfo          # Information about our application
import app              # Instantiate global signals etc
import install          # Update QSettings structure etc. if needed
import guistyle         # Setup GUI style
import i18n.setup       # Setup language
import remote           # IPC with other Frescobaldi instances


def parse_commandline():
    """Parses the command line; returns options and filenames.

    If --version, --help or invalid options were given, the application will
    exit.

    """
    import argparse
    argparse._ = _ # let argparse use our translations
    parser = argparse.ArgumentParser(conflict_handler="resolve",
        description = _("A LilyPond Music Editor"))
    parser.add_argument('-v', '--version', action="version",
        version="{0} {1}".format(appinfo.appname, appinfo.version),
        help=_("show program's version number and exit"))
    parser.add_argument('-V', '--version-debug', action="store_true", default=False,
        help=_("show version numbers of {appname} and its supporting modules "
               "and exit").format(appname=appinfo.appname))
    parser.add_argument('-e', '--encoding', metavar=_("ENC"),
        help=_("Encoding to use"))
    parser.add_argument('-l', '--line', type=int, metavar=_("NUM"),
        help=_("Line number to go to, starting at 1"))
    parser.add_argument('-c', '--column', type=int, metavar=_("NUM"),
        help=_("Column to go to, starting at 0"), default=0)
    parser.add_argument('--start', metavar=_("NAME"),
        help=_("Session to start ('{none}' for empty session)").format(none="-"),
        dest="session")
    parser.add_argument('--list-sessions', action="store_true", default=False,
        help=_("List the session names and exit"))
    parser.add_argument('-n', '--new', action="store_true", default=False,
        help=_("Always start a new instance"))
    parser.add_argument('--python-ly', type=str, metavar=_("STR"), default="",
        help=_("Path to python-ly"))
    parser.add_argument('files', metavar=_("file"), nargs='*',
        help=_("File to be opened"))

    # Make sure debugger options are recognized as valid. These are passed automatically
    # from PyDev in Eclipse to the inferior process.
    if "pydevd" in sys.modules:
        parser.add_argument('--vm_type', '-v')
        parser.add_argument('-a', '--client')
        parser.add_argument('-p', '--port')
        parser.add_argument('-f', '--file')
        parser.add_argument('-o', '--output')



    args = QApplication.arguments()

    # Strip interpreter name and its command line options on Windows
    if os.name == 'nt':
        while args:
            if os.path.basename(args[0]).lower().startswith(appinfo.name):
                break
            args.pop(0)

    return parser.parse_args(args[1:])


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


## it would be nice if the LY check could move to checks and be performed
## earlier, before parsing the arguments.  That would mean that the --python-ly
## option be removed, and the PYTHONPATH is used to point Frescobaldi to another
## ly module location (or just use a symlink) -- WB
def check_ly():
    """Check if ly is installed and has the correct version.

    If python-ly is not available or too old, we display a critical message
    and exit.  In the future we will probably remove this function.
    In a good software distribution this should never happen, but it can happen
    when a user leaves the old stale 'ly' package in the frescobaldi_app
    directory, or has not installed python-ly at all.

    Because that yields unexpected behaviour and error messages, we better
    check for the availability of the 'ly' module beforehand.
    Importing ly.pkginfo is not expensive.

    """
    try:
        import ly.pkginfo
        version = tuple(map(int, re.findall(r"\d+", ly.pkginfo.version)))
    except (ImportError, AttributeError):
        pass
    else:
        if version >= appinfo.required_python_ly_version:
            return
    from PyQt5.QtWidgets import QMessageBox
    QMessageBox.critical(None, _("Can't run Frescobaldi"), _(
        "We are sorry, but Frescobaldi can't run properly.\n\n"
        "The python-ly package is not available or too old.\n"
        "At least version {version} is required to run Frescobaldi.\n\n"
        "If you did install python-ly correctly, please remove the old\n"
        "ly package from the frescobaldi_app directory, or completely\n"
        "remove and then reinstall Frescobaldi."
    ).format(version=".".join(format(d) for d in appinfo.required_python_ly_version)))
    sys.exit(1)


def main():
    """Main function."""
    args = parse_commandline()

    if args.version_debug:
        import debuginfo
        sys.stdout.write(debuginfo.version_info_string() + '\n')
        sys.exit(0)

    if args.python_ly:
        # The python-ly path has to be inserted at the *second* position
        # because the first element in sys.path is the directory of the invoked
        # script (an information we need in determining if Frescobaldi is run
        # from its Git repository)
        sys.path.insert(1, args.python_ly)

    check_ly()

    if args.list_sessions:
        import sessions
        for name in sessions.sessionNames():
            sys.stdout.write(name + '\n')
        sys.exit(0)

    urls = list(map(url, args.files))

    if not app.qApp.isSessionRestored():
        if not args.new and remote.enabled():
            api = remote.get()
            if api:
                api.command_line(args, urls)
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
        macosx.setup.initialize()

    if app.qApp.isSessionRestored():
        # Restore session, we are started by the session manager
        session.restoreSession(app.qApp.sessionKey())
        return

    # Just create one MainWindow
    win = mainwindow.MainWindow()
    win.show()
    win.activateWindow()
    # make sure all dock tools are initialized and resized
    app.qApp.processEvents()

    # load specified session?
    doc = None
    if args.session and args.session != "-":
        doc = sessions.loadSession(args.session)

    # load documents given as arguments
    import document
    for u in urls:
        doc = win.openUrl(u, args.encoding, ignore_errors=True)
        if not doc:
            doc = document.EditorDocument(u, args.encoding)

    # were documents loaded?
    if not doc:
        if app.documents:
            doc = app.documents[-1]
        elif not args.session:
            # no docs, load default session
            doc = sessions.loadDefaultSession()

    if doc:
        win.setCurrentDocument(doc)
    else:
        win.cleanStart()

    if urls and args.line is not None:
        # set the last loaded document active and apply navigation if requested
        pos = doc.findBlockByNumber(args.line - 1).position() + args.column
        cursor = QTextCursor(doc)
        cursor.setPosition(pos)
        win.currentView().setTextCursor(cursor)
        win.currentView().centerCursor()
