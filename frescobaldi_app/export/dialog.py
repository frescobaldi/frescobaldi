# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Export settings dialog.
"""

from __future__ import unicode_literals

import collections
import os

from PyQt4.QtCore import QSettings, QSize, Qt, QUrl
from PyQt4.QtGui import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QTextEdit)
from PyQt4.QtGui import (
    QDialog, QDialogButtonBox, QLabel, QLayout, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget)

import app
import help
import icons
import qutil

import widgets
import info
from . import options


class ExportDialog(QDialog):
    """A dialog to define source code export settings.
    
    Tries to be as strict about interdepending properties.
    Optionally saves to Preferences.
    # autosave if enabled
    
    """
    def __init__(self, mainwindow):
        """Creates the about dialog. exec_() returns True or False."""
        super(ExportDialog, self).__init__(mainwindow)
        
        self.setWindowTitle(_("Export Source Code"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        text = QTextBrowser()
        text.setHtml((
            "<p>{app_name}: {app_version}</p>\n"
            "<p>Export formatted source code.</p>\n"
            "<p>Currently hardcoded options:"
            "<ul><li>Source = {source}</li>"
            "<li>Dest = {dest}</li>"
            "<li>Style = {style}</li>"
            "<li>External CSS = {external_css}</li>"
            "<li>Format = {format}</li>"
            "<li>Document = {document}</li></ul>"
            ).format(
                app_name = info.appname,
                app_version = info.version, 
                source = options.source, 
                dest = options.dest, 
                style = options.style, 
                external_css = options.external_css, 
                format = options.format, 
                document = options.document))
        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.setCenterButtons(True)
        button.accepted.connect(self.accept)
        layout.addWidget(text)
        layout.addWidget(button)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        

