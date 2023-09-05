# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2020 - 2020 by Wilbert Berendsen
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
This module is imported from the startup script to perform some checks whether
Frescobaldi can run properly.

The user-visible strings need not to be marked for translation, as the
translation infrastructure is not yet set up.

"""

import os
import importlib.util
import sys

import appinfo


def error(title, message, can_continue=False):
    """Display an error, and exit if can_continue is False.

    Displays a message box if PyQt5 is available, otherwise write the error to
    stderr.

    """
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
    except ImportError:
        write = sys.stderr.write
        write(title + '\n')
        write(message + '\n')
        if can_continue:
            write("Continuing...\n")
        else:
            write("Exiting.\n")
            sys.exit(1)
    else:
        app = QApplication([])
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("Frescobaldi")
        box.setText(title)
        box.setInformativeText(message)
        if can_continue:
            box.setStandardButtons(QMessageBox.Abort|QMessageBox.Ignore)
            box.button(QMessageBox.Ignore).setText("Continue")
        else:
            box.setStandardButtons(QMessageBox.Abort)
        box.button(QMessageBox.Abort).setText("Quit")
        result = box.exec()
        app.quit()
        if not can_continue or result == QMessageBox.Abort:
            sys.exit(1)


# Check Python version
v = sys.version_info
r = appinfo.required_python_version
if v < r:
    error("Python version too old",
        f"Frescobaldi is started with Python {v[0]}.{v[1]} \
but requires at least version {r[0]}.{r[1]}.")


# Check popplerqt5 availability
import importlib
# when Python version requirement > 3.4 we can use importlib.find_spec() -- WB
if importlib.util.find_spec('popplerqt5') is None:
    error("The 'popplerqt5' module can't be found.",
        "Frescobaldi can't find the 'popplerqt5' module. This module is "
        "required for the display of PDF documents. The module is in the "
        "python-poppler-qt5 package which needs to be installed.\n\n"
        "Frescobaldi can run, but cannot display PDF documents.", True)


# Check qpageview availability
if importlib.util.find_spec('qpageview') is None:
    error("The 'qpageview' module can't be found.",
        "Frescobaldi can't find the 'qpageview' module. This module is "
        "required for the Music View and other viewers inside Frescobaldi, "
        "and can be downloaded from http://github.com/frescobaldi/qpageview."
        "\n\n"
        "Unfortunately, Frescobaldi cannot run without it.")


# The python-ly check could also move where, but we don't do it now, because
# the --python-ly option could point to another path, and the startup arguments
# are parsed later.
