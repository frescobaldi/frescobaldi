# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2014 - 2019 by Wilbert Berendsen
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

r"""
A simple module using CUPS to send a document directly to a printer described
by a QPrinter. This is especially useful with PDF documents.

Uses the `cups` module, although it elegantly fails when that module is not
present. The cups module can be found in the pycups package at
https://pypi.org/project/pycups/ .

There are two methods to send a document to a printer:

1. Using the `lp` shell command
2. Using the cups module, which uses libcups to directly contact the server.

This module provides both possibilities.

Use `CmdHandle.create()` to get a CmdHandle, if `lp` is available, or use
`IppHandle.create()` to get a IppHandle, if the cups module is available and a
connection to the server can be established.

A function `handle()` is available; that tries first to get an IppHandle and
then a LprHandle. Usage of this module is this simple::

    import qpageview.cupsprinter

    h = qpageview.cupsprinter.handle()
    if h:
        h.printFile('/path/to/document.pdf')

You can supply a QPrinter instance (that'd be the normal workflow :-)

::

    h = qpageview.cupsprinter.handle(printer)
    if h:
        h.printFile('/path/to/document.pdf')

In this case all options that are set in the QPrinter object will be used
when sending the document to the printer.

If `printFile()` returns True, printing is considered successful. If False,
you can read the `status` and `error` attributes::

    if not h.printFile('/path/to/document.pdf'):
        QMessageBox.warning(None, "Printing failure",
            "There was an error:\n{0} (status: {1})".format(h.error, h.status))

To print a list of files in one job, use `printFiles()`.

"""

import os
import shutil
import subprocess

from PyQt5.QtPrintSupport import QPrintEngine, QPrinter


class Handle:
    """Shared implementation of a handle that can send documents to a printer."""
    def __init__(self, printer=None):
        self._printer = printer

    def setPrinter(self, printer):
        """Use the specified QPrinter."""
        self._printer = printer

    def printer(self):
        """Return the QPrinter given on init, or a new default QPrinter instance."""
        if self._printer == None:
            self._printer = QPrinter()
        return self._printer

    def options(self):
        """Return the dict of CUPS options read from the printer object."""
        return options(self.printer())

    def title(self, filenames):
        """Return a sensible job title based on the list of filenames.

        This method is called when the user did not specify a job title.

        """
        maxlen = 5
        titles = [os.path.basename(f) for f in filenames[:maxlen]]
        more = len(filenames) - maxlen
        if more > 0:
            titles.append("(+{0} more)".format(more))
        return ", ".join(titles)

    def printFile(self, filename, title=None, options=None):
        """Print the file."""
        return self.printFiles([filename], title, options)

    def printFiles(self, filenames, title=None, options=None):
        """Print a list of files.

        If the title is None, the basename of the filename is used. Options may
        be a dictionary of CUPS options.  All keys and values should be
        strings.

        Returns True if the operation was successful. Returns False if there was
        an error; after the call to printFile(), the status and error attributes
        contain the returncode of the operation and the error message.

        """
        if filenames:
            if all(f and not f.isspace() and f != "-" for f in filenames):
                if not title:
                    title = self.title(filenames)
                o = self.options()
                if options:
                    o.update(options)
                printerName = self.printer().printerName()
                self.status, self.error = self._doPrintFiles(printerName, filenames, title, o)
            else:
                self.status, self.error = 2, "Not a valid filename"
        else:
            self.status, self.error = 2, "No filenames specified"
        return self.status == 0

    def _doPrintFiles(self, printerName, filenames, title, options):
        """Implement this to perform the printing.

        Should return a tuple (status, error). If status is 0, the operation is
        considered to be successful. If not, the operation is considered to have
        failed, and the `error` message should contain some more information.

        """
        return 0, ""


class CmdHandle(Handle):
    """Print a document using the `lp` shell command."""
    def __init__(self, command, server="", port=0, user="", printer=None):
        self._command = command
        self._server = server
        self._port = port
        self._user = user
        super().__init__(printer)

    @classmethod
    def create(cls, printer=None, server="", port=0, user="", cmd="lp"):
        """Create a handle to print using a shell command, if available."""
        cmd = shutil.which(cmd)
        if cmd:
            return cls(cmd, server, port, user, printer)

    def _doPrintFiles(self, printerName, filenames, title, options):
        """Print filenames using the `lp` shell command."""
        cmd = [self._command]
        if self._server:
            if self._port:
                cmd.extend(['-h', "{0}:{1}".format(self._server, self._port)])
            else:
                cmd.extend(['-h', self._server])
        if self._user:
            cmd.extend(['-U', self._user])
        cmd.extend(['-d', printerName])
        cmd.extend(['-t', title])
        if options:
            for option, value in options.items():
                cmd.extend(['-o', '{0}={1}'.format(option, value)])
        if any(f.startswith('-') for f in filenames):
            cmd.append('--')
        cmd.extend(filenames)
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as e:
            return e.errno, e.strerror
        message = p.communicate()[1].decode('UTF-8', 'replace')
        return p.wait(), message


class IppHandle(Handle):
    """Print a document using a connection to the CUPS server."""
    def __init__(self, connection, printer=None):
        super().__init__(printer)
        self._connection = connection

    @classmethod
    def create(cls, printer=None, server="", port=0, user=""):
        """Return a handle to print using a connection to the (local) CUPS server, if available."""
        try:
            import cups
        except ImportError:
            return
        cups.setServer(server or "")
        cups.setPort(port or 0)
        cups.setUser(user or "")
        try:
            c = cups.Connection()
        except RuntimeError:
            return
        h = cls(c, printer)
        if h.printer().printerName() in c.getPrinters():
            return h

    def _doPrintFiles(self, printerName, filenames, title, options):
        """Print filenames using a connection to the CUPS server."""
        import cups
        # cups.Connection.printFiles() behaves flaky: version 1.9.74 can
        # silently fail (without returning an error), and after having fixed
        # that, there are strange error messages on some options.
        # Therefore we use cups.printFile() for every file.
        for filename in filenames:
            try:
                self._connection.printFile(printerName, filename, title, options)
            except cups.IPPError as err:
                return err.args
        return 0, ""


def handle(printer=None, server="", port=0, user=""):
    """Return the first available handle to print a document to a CUPS server."""
    return (IppHandle.create(printer, server, port, user) or
            CmdHandle.create(printer, server, port, user))


def options(printer):
    """Return the dict of CUPS options read from the QPrinter object."""
    o = {}

    # cups options that can be set in QPrintDialog on unix
    # I found this in qt5/qtbase/src/printsupport/kernel/qcups.cpp.
    # Esp. options like page-set even/odd do make sense.
    props = printer.printEngine().property(0xfe00)
    if props and isinstance(props, list) and len(props) % 2 == 0:
        for key, value in zip(props[0::2], props[1::2]):
            if value and isinstance(key, str) and isinstance(value, str):
                o[key] = value

    o['copies'] = format(printer.copyCount())
    if printer.collateCopies():
        o['collate'] = 'true'

    # TODO: in Qt5 >= 5.11 page-ranges support is more fine-grained!
    if printer.printRange() == QPrinter.PageRange:
        o['page-ranges'] = '{0}-{1}'.format(printer.fromPage(), printer.toPage())

    # page order
    if printer.pageOrder() == QPrinter.LastPageFirst:
        o['outputorder'] = 'reverse'

    # media size
    media = []
    size = printer.paperSize()
    if size == QPrinter.Custom:
        media.append('Custom.{0}x{1}mm'.format(printer.heightMM(), printer.widthMM()))
    elif size in PAGE_SIZES:
        media.append(PAGE_SIZES[size])

    # media source
    source = printer.paperSource()
    if source in PAPER_SOURCES:
        media.append(PAPER_SOURCES[source])

    if media:
        o['media'] = ','.join(media)

    # page margins
    if printer.printEngine().property(QPrintEngine.PPK_PageMargins):
        left, top, right, bottom = printer.getPageMargins(QPrinter.Point)
        o['page-left'] = format(left)
        o['page-top'] = format(top)
        o['page-right'] = format(right)
        o['page-bottom'] = format(bottom)

    # orientation
    landscape = printer.orientation() == QPrinter.Landscape
    if landscape:
        o['landscape'] = 'true'

    # double sided
    duplex = printer.duplex()
    o['sides'] = (
        'two-sided-long-edge' if duplex == QPrinter.DuplexLongSide or
                        (duplex == QPrinter.DuplexAuto and not landscape) else
        'two-sided-short-edge' if duplex == QPrinter.DuplexShortSide or
                        (duplex == QPrinter.DuplexAuto and landscape) else
        'one-sided')

    # grayscale
    if printer.colorMode() == QPrinter.GrayScale:
        o['print-color-mode'] = 'monochrome'

    return o


def clearPageSetSetting(printer):
    """Remove 'page-set' even/odd cups options from the printer's CUPS options.

    Qt's QPrintDialog fails to reset the 'page-set' option back to 'all pages',
    so a previous value (even or odd) could remain in the print options, even
    if the user has selected All Pages in the print dialog.

    This function clears the page-set setting from the cups options. If the
    user selects or has selected even or odd pages, it will be added again by
    the dialog.

    So call this function on a QPrinter, just before showing a QPrintDialog.

    """
    # see qt5/qtbase/src/printsupport/kernel/qcups.cpp
    opts = printer.printEngine().property(0xfe00)
    if opts and isinstance(opts, list) and len(opts) % 2 == 0:
        try:
            i = opts.index('page-set')
        except ValueError:
            return
        if i % 2 == 0:
            del opts[i:i+2]
            printer.printEngine().setProperty(0xfe00, opts)


PAGE_SIZES = {
    QPrinter.A0: "A0",
    QPrinter.A1: "A1",
    QPrinter.A2: "A2",
    QPrinter.A3: "A3",
    QPrinter.A4: "A4",
    QPrinter.A5: "A5",
    QPrinter.A6: "A6",
    QPrinter.A7: "A7",
    QPrinter.A8: "A8",
    QPrinter.A9: "A9",
    QPrinter.B0: "B0",
    QPrinter.B1: "B1",
    QPrinter.B10: "B10",
    QPrinter.B2: "B2",
    QPrinter.B3: "B3",
    QPrinter.B4: "B4",
    QPrinter.B5: "B5",
    QPrinter.B6: "B6",
    QPrinter.B7: "B7",
    QPrinter.B8: "B8",
    QPrinter.B9: "B9",
    QPrinter.C5E: "C5",         # Correct Translation?
    QPrinter.Comm10E: "Comm10", # Correct Translation?
    QPrinter.DLE: "DL",         # Correct Translation?
    QPrinter.Executive: "Executive",
    QPrinter.Folio: "Folio",
    QPrinter.Ledger: "Ledger",
    QPrinter.Legal: "Legal",
    QPrinter.Letter: "Letter",
    QPrinter.Tabloid: "Tabloid",
}

PAPER_SOURCES = {
    QPrinter.Cassette: "Cassette",
    QPrinter.Envelope: "Envelope",
    QPrinter.EnvelopeManual: "EnvelopeManual",
    QPrinter.FormSource: "FormSource",
    QPrinter.LargeCapacity: "LargeCapacity",
    QPrinter.LargeFormat: "LargeFormat",
    QPrinter.Lower: "Lower",
    QPrinter.MaxPageSource: "MaxPageSource",
    QPrinter.Middle: "Middle",
    QPrinter.Manual: "Manual",
    QPrinter.OnlyOne: "OnlyOne",
    QPrinter.Tractor: "Tractor",
    QPrinter.SmallFormat: "SmallFormat",
}

