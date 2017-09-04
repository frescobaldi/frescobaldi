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
Constructs a printcommand to print a PDF file.
"""


import itertools
import os

from PyQt5.QtPrintSupport import QPrinter


lpr_commands = (
    "lpr-cups",
    "lpr.cups",
    "lpr",
    "lp",
)

def lprCommand():
    """Returns a suitable 'lpr'-like command to send a file to the printer queue.

    Returns None if no such command could be found.
    Prefers the CUPS command 'lpr' or 'lp' if it can be found.

    """
    paths = os.environ.get("PATH", os.defpath).split(os.pathsep)
    for cmd, path in itertools.product(lpr_commands, paths):
        if os.access(os.path.join(path, cmd), os.X_OK):
            return cmd


def printCommand(cmd, printer, filename):
    """Returns a commandline (list) to print a PDF file.

    cmd:      "lpr" or "lp" (or something like that)
    printer:  a QPrinter instance
    filename: the filename of the PDF document to print.

    """
    command = [cmd]

    # printer name
    if cmd == "lp":
        command.append('-d')
    else:
        command.append('-P')
    command.append(printer.printerName())

    # copies
    numCopies = 1
    try:
        numCopies = printer.copyCount()
    except AttributeError: # only in Qt >= 4.7
        try:
            numCopies = printer.actualNumCopies()
        except AttributeError: # only in Qt >= 4.6
            numCopies = printer.numCopies()

    if cmd == "lp":
        command.append('-n')
        command.append(format(numCopies))
    else:
        command.append('-#{0}'.format(numCopies))

    # collate
    if printer.collateCopies():
        command.append('-o')
        command.append('collate=true')

    # job name
    if cmd == "lp":
        command.append('-t')
    else:
        command.append('-J')
    command.append(printer.docName() or os.path.basename(filename))

    # page range
    if printer.printRange() == QPrinter.PageRange:
        pageRange = "{0}-{1}".format(printer.fromPage(), printer.toPage())
        if cmd == "lp":
            command.append('-P')
            command.append(pageRange)
        else:
            command.append('-o')
            command.append('page-ranges=' + pageRange)

    # duplex mode
    if printer.duplex() == QPrinter.DuplexLongSide:
        command.extend(['-o', 'sides=two-sided-long-edge'])
    elif printer.duplex() == QPrinter.DuplexShortSide:
        command.extend(['-o', 'sides=two-sided-short-edge'])

    command.append(filename)
    return command



