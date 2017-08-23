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
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QTextEdit, QFrame, QSplitter, QPushButton
from PyQt5.QtGui import QTextDocument, QPalette, QColor, QTextCursor

from vcs import differ
import css

class VCSDiffWindow(QWidget):
    def __init__(self, content_dict, view):
        super().__init__()
        self._view = view
        self._dict = content_dict

        old_doc = QTextDocument()
        old_doc.setDefaultStyleSheet(css.diff_popup)
        new_doc = QTextDocument()
        new_doc.setDefaultStyleSheet(css.diff_popup)
        old_doc.setHtml(differ.ori_highlight_diff(content_dict['deleted_lines'],
                                                  content_dict['added_lines'],
                                                  content_dict['old_start_pos']))
        new_doc.setHtml(differ.chg_highlight_diff(content_dict['deleted_lines'],
                                                  content_dict['added_lines'],
                                                  content_dict['start_pos']))

        old_view = QTextEdit()
        old_view.setDocument(old_doc)
        old_view.setReadOnly(True)
        old_plt = old_view.palette()
        old_plt.setColor(QPalette.Base, QColor('#ffeef0'))
        old_view.setPalette(old_plt)

        new_view = QTextEdit()
        new_view.setDocument(new_doc)
        new_view.setReadOnly(True)
        new_plt = new_view.palette()
        new_plt.setColor(QPalette.Base, QColor('#e6ffed'))
        new_view.setPalette(new_plt)

        diff_splitter = QSplitter(Qt.Horizontal)
        diff_splitter.addWidget(old_view)
        diff_splitter.addWidget(new_view)

        diff_layout = QHBoxLayout()
        diff_layout.setContentsMargins(0, 0, 0, 0)
        diff_layout.setSpacing(0)
        diff_layout.addWidget(diff_splitter)

        revertButton = QPushButton("revert")
        revertButton.clicked.connect(self.revert)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(revertButton)


        main_layout = QVBoxLayout()
        main_layout.addLayout(diff_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        self.setLayout(main_layout)
        self.setWindowFlags(Qt.Popup)

    def revert(self):
        """Replace the new text with the old text in working view
        """
        cursor = self._view.textCursor()
        cursor.movePosition(QTextCursor.Start)
        new_lines = self._dict['added_lines']
        old_lines = self._dict['deleted_lines']
        if not new_lines:
            # Handle "deleted" hunk
            old_text = '\n'.join(old_lines)
            if self._dict['start_pos'] == 0:
                old_text = old_text + '\n'
                cursor.insertText(old_text)
            else:
                cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, self._dict['start_pos']-1)
                cursor.movePosition(QTextCursor.EndOfBlock)
                old_text = '\n'+old_text
                cursor.insertText(old_text)
        else:
            # Handle "modified" and "added" hunk
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, self._dict['start_pos']-1)
            if self._dict['start_pos'] == 1:
                for line in new_lines:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    text = cursor.selectedText()
                    cursor.removeSelectedText()
                    cursor.deleteChar()
            else:
                for line in new_lines:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    text = cursor.selectedText()
                    if not text:
                        # When the block under cursor is an empty block
                        cursor.deleteChar()
                    else:
                        cursor.removeSelectedText()
                        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
            if old_lines:
                old_text = '\n'.join(old_lines)
                if (self._dict['start_pos'] <= self._view.blockCount()):
                    cursor.movePosition(QTextCursor.StartOfBlock)
                    old_text = old_text + '\n'
                else:
                    cursor.movePosition(QTextCursor.End)
                    old_text = '\n'+old_text
                cursor.insertText(old_text)
        self.close()
