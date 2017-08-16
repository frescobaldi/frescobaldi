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
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QTextEdit, QFrame, QSplitter
from PyQt5.QtGui import QTextDocument, QPalette, QColor

from vcs import differ
import css

class VCSDiffWindow(QWidget):
    def __init__(self, content_dict):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        document1 = QTextDocument()
        document1.setDefaultStyleSheet(css.diff_popup)
        document2 = QTextDocument()
        document2.setDefaultStyleSheet(css.diff_popup)
        old_lines = content_dict['deleted_lines']
        new_lines = content_dict['added_lines']
        old_start_pos = content_dict['old_start_pos']
        new_start_pos = content_dict['start_pos']
        differ.absolute_index = old_start_pos
        document1.setHtml(differ.ori_highlight_diff(old_lines, new_lines))
        differ.absolute_index = new_start_pos
        document2.setHtml(differ.chg_highlight_diff(old_lines, new_lines))

        textEdit1 = QTextEdit()
        textEdit1.setDocument(document1)
        p1 = textEdit1.palette()
        p1.setColor(QPalette.Base, QColor('#ffeef0'))
        textEdit1.setPalette(p1)
        textEdit1.setReadOnly(True)
        textEdit2 = QTextEdit()
        textEdit2.setDocument(document2)
        p2 = textEdit2.palette()
        p2.setColor(QPalette.Base, QColor('#e6ffed'))
        textEdit2.setPalette(p2)
        textEdit2.setReadOnly(True)
        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(textEdit1)
        splitter1.addWidget(textEdit2)
        layout.addWidget(splitter1)
        self.setLayout(layout)
        self.setWindowFlags(Qt.Popup)

