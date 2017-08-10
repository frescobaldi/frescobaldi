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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QTextEdit
from PyQt5.QtGui import QTextDocument

from . import differ
import css

class VCSDiffWindow(QWidget):
    def __init__(self, content_dict):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        document = QTextDocument()
        document.setDefaultStyleSheet(css.diff_popup)
        document.setHtml(differ.highlight_diff(content_dict['deleted_lines'], content_dict['added_lines']))
        textEdit = QTextEdit()
        textEdit.setDocument(document)
        layout.addWidget(textEdit)
        self.setLayout(layout)
        self.setWindowFlags(Qt.Popup)

