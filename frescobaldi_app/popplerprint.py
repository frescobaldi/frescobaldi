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
Prints a PDF (or Poppler) document.

On Mac OS X and Linux, the document is just sent to lpr
(via a dialog).

On Windows, another command can be configured or bitmaps of the poppler document
can be printed.
"""



import os
import sys
import subprocess
import weakref

from PyQt5.QtCore import pyqtSignal, QSettings, QTemporaryFile, Qt, QThread
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

import app
import helpers
import fileprinter
import qpopplerview.printer


# store QPrinter instances for a widget
_printers = weakref.WeakKeyDictionary()


def print_(doc, filename=None, widget=None):
    """Prints the popplerqt5.Poppler.Document.

    The filename is used in the dialog and print job name.
    If the filename is not given, it defaults to a translation of "PDF Document".
    The widget is a widget to use as parent for the print dialog etc.

    """
    # Decide how we will print.
    # on Windows and Mac OS X a print command must be specified, otherwise
    # we'll use raster printing
    s = QSettings()
    s.beginGroup("helper_applications")
    cmd = s.value("printcommand", "", str)
    use_dialog = s.value("printcommand/dialog", False, bool)
    resolution = s.value("printcommand/dpi", 300, int)
    linux_lpr = False

    if os.name != 'nt' and not sys.platform.startswith('darwin'):
        # we're probably on Linux
        if not cmd:
            cmd = fileprinter.lprCommand()
            if cmd:
                linux_lpr = True
        elif cmd.split('/')[-1] in fileprinter.lpr_commands:
            linux_lpr = True

    print_file = filename
    title = os.path.basename(filename) if filename else _("PDF Document")

    if widget:
        try:
            printer = _printers[widget]
        except KeyError:
            printer = _printers[widget] = QPrinter()
        else:
            printer.setCopyCount(1)
    else:
        printer = QPrinter()

    printer.setDocName(title)
    printer.setPrintRange(QPrinter.AllPages)

    if linux_lpr or use_dialog or not cmd:
        dlg = QPrintDialog(printer, widget)
        dlg.setMinMax(1, doc.numPages())
        dlg.setOption(QPrintDialog.PrintToFile, False)
        dlg.setWindowTitle(app.caption(_("Print {filename}").format(filename=title)))

        result = dlg.exec_()
        if widget:
            dlg.deleteLater() # because it has a parent
        if not result:
            return # cancelled

    if linux_lpr or '$ps' in cmd:
        # make a PostScript file with the desired paper size
        ps = QTemporaryFile()
        if ps.open() and qpopplerview.printer.psfile(doc, printer, ps):
            ps.close()
            print_file = ps.fileName()
    elif cmd:
        if printer.printRange() != QPrinter.AllPages:
            cmd = None # we can't cut out pages from a PDF file
        elif '$pdf' not in cmd:
            cmd += ' $pdf'

    command = []
    if linux_lpr:
        # let all converted pages print
        printer.setPrintRange(QPrinter.AllPages)
        command = fileprinter.printCommand(cmd, printer, ps.fileName())
    elif cmd and print_file:
        for arg in helpers.shell_split(cmd):
            if arg in ('$ps', '$pdf'):
                command.append(print_file)
            else:
                arg = arg.replace('$printer', printer.printerName())
                command.append(arg)
    if command:
        if subprocess.call(command):
            QMessageBox.warning(widget, _("Printing Error"),
                _("Could not send the document to the printer."))
        return
    else:
        # Fall back printing of rendered raster images.
        # It is unsure if the Poppler ArthurBackend ever will be ready for
        # good rendering directly to a painter, so we'll fall back to using
        # raster images.

        p = Printer()
        p.setDocument(doc)
        p.setPrinter(printer)
        p.setResolution(resolution)

        d = QProgressDialog()
        d.setModal(True)
        d.setMinimumDuration(0)
        d.setRange(0, len(p.pageList()) + 1)
        d.canceled.connect(p.abort)

        def progress(num, total, page):
            d.setValue(num)
            d.setLabelText(_("Printing page {page} ({num} of {total})...").format(
                page=page, num=num, total=total))

        def finished():
            p.deleteLater()
            d.deleteLater()
            d.hide()
            if not p.success and not p.aborted():
                QMessageBox.warning(widget, _("Printing Error"),
                    _("Could not send the document to the printer."))

        p.finished.connect(finished)
        p.printing.connect(progress)
        p.start()


class Printer(QThread, qpopplerview.printer.Printer):
    """Simple wrapper that prints the raster images in a background thread."""
    printing = pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        qpopplerview.printer.Printer.__init__(self)
        self.success = None

    def run(self):
        self.success = self.print_()

    def progress(self, num, total, page):
        self.printing.emit(num, total, page)


def printDocument(document, widget=None):
    """Prints the document described by the popplertools.Document.

    The widget is a widget to use as parent for the print dialog etc.

    """
    print_(document.document(), document.filename(), widget)


