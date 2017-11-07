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
        self._reverted = False

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
        # Revert button could be clicked more than once
        if self._reverted:
            return
        else:
            self._reverted = True
        cursor = self._view.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        new_lines = self._dict['added_lines']
        old_lines = self._dict['deleted_lines']

        if not new_lines:
        # Handle "deleted" hunk (new_lines == [])
        # Basically we are inserting the deleted lines in to certain position
            old_text = '\n'.join(old_lines)
            # Special case:
            # When we should insert at the start of the view
            if self._dict['start_pos'] == 0:
                old_text = old_text + '\n'
                print("Insert")
                cursor.insertText(old_text)
            else:
            # When we insert at other positions in the view
            # We go the the previous line of the insert position and then insert
            # at the line's ending.
                # Move cursor to the previous line
                cursor.movePosition(QTextCursor.Down,
                                    QTextCursor.MoveAnchor,
                                    self._dict['start_pos']-1)
                # Move cursor to this line's end
                cursor.movePosition(QTextCursor.EndOfBlock)
                # add a '\n' at head to come into a new line
                old_text = '\n' + old_text
                # Special case:
                # When we need insert at last line (cursor.pos = blockCount-2).
                # We should handle the line ending of the last line.
                if cursor.blockNumber() == self._view.blockCount()-2:
                    cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)
                    cursor.select(QTextCursor.BlockUnderCursor)
                    text = cursor.selectedText()
                    # Checking whether the last line is empty
                    if not text:
                        # delete the last line (an empty block)
                        cursor.removeSelectedText()
                        cursor.deletePreviousChar()
                        # Checking whether we need to add '\n' at the text end
                        if not self._dict['no_newline_at_end_of_old_file']:
                            old_text = old_text + '\n'
                    else:
                        # If the last line is not empty, cursor go back to
                        # previous line. We don't need to handle the
                        # last-line-ending Here.
                        cursor.clearSelection()
                        cursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor)
                # Insert the deleted text, so the deleted hunk is reverted
                print("Insert")
                cursor.insertText(old_text)
        else:
        # Handle "modified" and "added" hunk
            # Move cursor to the position where we should delete new added line
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor,
                                self._dict['start_pos']-1)
            # Special case:
            # When we should delete the new added lines at the file-beginning
            if self._dict['start_pos'] == 1:
                for line in new_lines:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    text = cursor.selectedText()
                    cursor.removeSelectedText()
                    # Althogh the line is removed, but the block remains.
                    # So delete the empty block
                    cursor.deleteChar()
            else:
                for line in new_lines:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    text = cursor.selectedText()
                    if not text:
                        # Delete the empty block
                        cursor.deleteChar()
                    else:
                        cursor.removeSelectedText()
                        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor)

                # Special case:
                # When the new added lines are added at the end of the file
                # To remove all the new added lines, we need to check whether
                # the new file ends with a '\n'
                if cursor.blockNumber() == self._view.blockCount()-1:
                    cursor.select(QTextCursor.BlockUnderCursor)
                    text = cursor.selectedText()
                    if not text and not self._dict['no_newline_at_end_of_new_file']:
                        # If so, delete the last block
                        cursor.removeSelectedText()
                        cursor.deletePreviousChar()
                    cursor.clearSelection()

            # Special case:
            # When there are no old_lines, this is "added" hunk.
            # But we may affect the last-line-ending of original file through
            # above deleting operations. So we check it here.
            if not old_lines and self._dict['start_pos'] > self._view.blockCount():
                if not self._dict['no_newline_at_end_of_old_file']:
                    old_text = '\n'
                    print("Insert")
                    cursor.insertText(old_text)

            elif old_lines:
            # Insert the old_lines into the view
                old_text = '\n'.join(old_lines)
                # When the contents is inserted at normal positions
                if (self._dict['start_pos'] <= self._view.blockCount()):
                    cursor.movePosition(QTextCursor.StartOfBlock)
                    old_text = old_text + '\n'
                # When the contents is inserted at the end of the file
                # We need to check whether we should add a '\n' and the end of
                # the file.
                elif self._dict['no_newline_at_end_of_old_file']:
                    cursor.movePosition(QTextCursor.End)
                    old_text = '\n'+old_text
                else:
                    cursor.movePosition(QTextCursor.End)
                    old_text = '\n'+old_text+'\n'

                print("Insert")
                cursor.insertText(old_text)

        cursor.endEditBlock()
        self.close()
