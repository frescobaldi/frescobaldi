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

from PyQt6.QtPrintSupport import QPrinter


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
        command.append(f'-#{numCopies}')

    # job name
    if cmd == "lp":
        command.append('-t')
    else:
        command.append('-J')
    command.append(printer.docName() or os.path.basename(filename))

    # page range
    if printer.printRange() == QPrinter.PageRange:
        pageRange = f"{printer.fromPage()}-{printer.toPage()}"
        if cmd == "lp":
            command.append('-P')
            command.append(pageRange)

    for option, value in cups_options(printer).items():
        command.append('-o')
        command.append(f"{option}={value}")

    command.append(filename)
    return command


def cups_options(p):
    """Return a dictionary with CUPS `-o` options, read from QPrinter p."""
    o = {}

    # cups options that can be set in QPrintDialog on unix
    # I found this in qt5/qtbase/src/printsupport/kernel/qcups.cpp.
    # Esp. options like page-set even/odd do make sense.
    props = p.printEngine().property(0xfe00)
    if props and isinstance(props, list) and len(props) % 2 == 0:
        for key, value in zip(props[0::2], props[1::2]):
            if value and isinstance(key, str) and isinstance(value, str):
                o[key] = value

    # collate
    if p.collateCopies():
        o['collate'] = 'true'

    # page ranges
    if p.printRange() == QPrinter.PageRange:
        o['page-ranges'] = f"{p.fromPage()}-{p.toPage()}"

    # duplex mode
    if p.duplex() == QPrinter.DuplexLongSide:
        o['sides'] = 'two-sided-long-edge'
    elif p.duplex() == QPrinter.DuplexShortSide:
        o['sides'] = 'two-sided-short-edge'

    # grayscale
    if p.colorMode() == QPrinter.GrayScale:
        o['print-color-mode'] = 'monochrome'

    return o


