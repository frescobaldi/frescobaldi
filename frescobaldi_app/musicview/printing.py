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

from __future__ import unicode_literals

"""
Prints a PDF (or Poppler) document.

On Mac OS X and Linux, the document is just sent to lpr
(via a dialog).

On Windows, another command can be configured or bitmaps of the poppler document
can be printed.
"""


import os
import subprocess

from PyQt4.QtGui import QMessageBox, QPrinter, QPrintDialog

import app
import fileprinter


def printDocument(dock, document):
    """Prints the document described by document (see the musicview.documents module).
    
    The dock is the QDockWidget of the music viewer.
    
    """
    cmd = fileprinter.lprCommand()
    if not cmd:
        # Temporarily return from here, later fallback printing could be implemented
        QMessageBox.information(dock, _("Not Supported"),
            _("No Print command could be found and direct printing is not yet supported."))
        return
        
    printer = QPrinter()
    dlg = QPrintDialog(printer, dock)
    
    numPages = document.document().numPages()
    dlg.setMinMax(1, numPages)
    dlg.setOption(QPrintDialog.PrintToFile, False)
    dlg.setWindowTitle(app.caption(
        _("Print {filename}").format(filename=os.path.basename(document.filename()))))
    
    if not dlg.exec_():
        return # cancelled
    
    if cmd:
        command = fileprinter.printCommand(cmd, printer, document.filename())
        if subprocess.call(command):
            QMessageBox.warning(dock, _("Printing Error"),
                _("Could not send the document to the printer."))
    else:
        pass
        # TODO: implement fall back printing of rendered raster images
        # It is unsure if the Poppler ArthurBackend ever will be ready for
        # good rendering directly to a painter, so we'll fall back to using
        # 300DPI raster images.


