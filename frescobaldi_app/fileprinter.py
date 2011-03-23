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
Constructs a printcommand to print a PDF file.
"""

import os

from PyQt4.QtGui import QPrinter


def printCommand(cmd, printer, filename):
    """Returns a commandline (list) to print a PDF file.
    
    cmd:      "lpr" or "lp" (or something like that)
    printer:  a QPrinter instance
    filename: the filename of the PDF document.
    
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
    
    # job name
    if cmd == "lp":
        command.append('-t')
    else:
        command.append('-J')
    command.append(os.path.basename(filename))
    
    # page range
    if printer.printRange() == QPrinter.PageRange:
        pageRange = "{0}-{1}".format(printer.fromPage(), printer.toPage())
        if cmd == "lp":
            command.append('-P')
            command.append(pageRange)
        else:
            command.append('-o')
            command.append('page-ranges=' + pageRange)

    command.append(filename)
    return command



