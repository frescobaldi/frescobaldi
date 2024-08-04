# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Completer providing completions in a Q(Plain)TextEdit.
"""


from PyQt6.QtCore import QEvent, QModelIndex, Qt
from PyQt6.QtGui import QKeySequence, QTextCursor
from PyQt6.QtWidgets import QCompleter, QApplication


class Completer(QCompleter):
    """A QCompleter providing completions in a Q(Plain)TextEdit.

    Use setWidget() to assign the completer to a text edit.

    You can reimplement completionCursor() to make your own, other than simple
    string-based completions.

    Call showCompletionPopup() to force the popup to show.

    """
    autoComplete = True
    autoCompleteLength = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.activated[QModelIndex].connect(self.insertCompletion)

    def eventFilter(self, obj, ev):
        if ev.type() != QEvent.Type.KeyPress:
            return super().eventFilter(obj, ev)
        # we can't test for self.popup() as that will recursively call
        # eventFilter during instantiation.
        popupVisible = obj != self.widget()
        if popupVisible:
            # a key was pressed while the popup is visible
            cur = self.textCursor()
            modifier = QApplication.keyboardModifiers()

            # local handler functions for certain key events
            def backspace():
                # deliver event, hide popup if completionPrefix already none
                self.widget().event(ev)
                if self.completionPrefix():
                    self.showCompletionPopup()
                    return False
                else:
                    self.popup().hide()
                    return True

            def down():
                self.gotoNextEntry(1)
                return True

            def enter():
                # insert the highlighted completion
                self.setCurrentRow(self.popup().currentIndex().row())
                self.insertCompletion(self.currentIndex())
                if ev.text() == '.':
                    # deliver event and keep showing popup if necessary
                    cur.insertText('.')
                self.popup().hide()
                return True

            def tab():
                if modifier == Qt.KeyboardModifier.AltModifier:
                    # Don't block Alt-Tab for switching applications
                    self.popup().hide()
                    return False
                if cur.hasSelection():
                    self.acceptPartialCompletion()
                    self.showCompletionPopup()
                direction = -1 if modifier == Qt.KeyboardModifier.ControlModifier else 1
                self.gotoNextEntry(direction)
                return False

            def up():
                self.gotoNextEntry(-1)
                return True

            # map keys to handler functions
            handlers = {
                Qt.Key.Key_Return: enter,
                Qt.Key.Key_Enter: enter,
                Qt.Key.Key_Backspace: backspace,
                Qt.Key.Key_Tab: tab,
                Qt.Key.Key_Up: up,
                Qt.Key.Key_Down: down
            }

            handler = handlers.get(ev.key())
            if handler:
                return handler()

            elif self.isTextEvent(ev, True):
                # deliver event and keep showing popup if necessary
                self.widget().event(ev)
                self.showCompletionPopup()
                self.insertPartialCompletion(self.currentIndex())
                return True
            elif ev.key() not in (
                Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
                Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
                # hide on anything except navigation keys
                self.popup().hide()
            return super().eventFilter(obj, ev)
        # a key was pressed while the popup is not visible
        if self.autoComplete and self.isTextEvent(ev, False):
            self.widget().event(ev)
            self.showCompletionPopup(False)
            return True
        return False

    def isTextEvent(self, ev, visible):
        """Called when a key is pressed.

        Should return True if the given KeyPress event 'ev' represents text that
        makes sense for showing the completions popup.

        The 'visible' argument is True when the popup is currently visible.

        """
        return ev.text()[-1:] > " " and ev.key() != Qt.Key.Key_Delete

    def textCursor(self):
        """Returns the current text cursor of the TextEdit."""
        return self.widget().textCursor()

    def completionCursor(self):
        """Should return a QTextCursor or None.

        If a QTextCursor is returned, its selection is used as the completion
        prefix and its selectionStart() as the place to popup the popup.

        This method may also alter the completion model.

        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.setPosition(cursor.selectionEnd())
        cursor.movePosition(QTextCursor.MoveOperation.StartOfWord, QTextCursor.MoveMode.KeepAnchor)
        return cursor

    def showCompletionPopup(self, forced=True):
        """Shows the completion popup.

        Calls completionCursor() to get the place where to popup, and that
        method may also alter the completion model.

        If forced is True (the default) the popup is always shown (if it
        contains any entries). Otherwise it is only shown self.autoComplete is
        True and the cursor returned by completionCursor() has at least
        self.autoCompleteLength characters selected.

        """
        cursor = self.completionCursor()
        if not cursor:
            self.popup().hide()
            return
        text = cursor.selectedText()
        if forced or (self.autoComplete and len(text) >= self.autoCompleteLength):
            self.setCompletionPrefix(text)
            # hide if there is only one completion left
            if (not self.setCurrentRow(1) and self.setCurrentRow(0)
                and self.currentCompletion() == text):
                self.popup().hide()
                return
            self.setCurrentRow(0)
            rect = self.widget().cursorRect(cursor)
            rect.setWidth(self.popup().sizeHintForColumn(0)
                + self.popup().verticalScrollBar().sizeHint().width())
            rect.translate(self.widget().viewport().pos())
            frameWidth = self.popup().frameWidth()
            rect.translate(-frameWidth, frameWidth + 2)
            rect.translate(-self.popup().viewport().pos())
            self.complete(rect)
            self.setCurrentRow(0)
            self.popup().setCurrentIndex(self.currentIndex())

    def insertCompletion(self, index):
        """Inserts the completion at the given index.

        The default implementation reads the model data under the Qt.ItemDataRole.EditRole,
        and inserts that with the (already entered) completionPrefix removed.

        """
        cursor = self.textCursor()
        sel_len = cursor.selectionEnd() - cursor.selectionStart() if cursor.hasSelection() else 0
        cursor.setPosition(cursor.selectionEnd())
        prefix_len = len(self.completionPrefix())
        cursor.setPosition(cursor.position() - prefix_len - sel_len, cursor.KeepAnchor)
        cursor.insertText(self.completionModel().data(index, Qt.ItemDataRole.EditRole))

    def insertPartialCompletion(self, index):
        r"""Called when a tab key is pressed. Here index in current index item selected

        function to check for partial similar text in suggestions
        example:
            \sourcefileline
            \sourcefilename
            are suggestion
            on tab press text change to sourcefile
        """
        partial = True
        string = ''
        rows = []
        rem_len = 0
        compl_prefix = self.completionPrefix()
        text_len = len(compl_prefix)
        for irow in range(self.completionModel().rowCount()):
            self.setCurrentRow(irow)
            cell = self.completionModel().data(self.currentIndex())[text_len:]
            if cell:
                rows.append(cell)
                rem_len = min(rem_len, len(cell)) if rem_len > 0 else len(cell)
        self.setCurrentRow(index.row())
        if rows and not self.currentCompletion() == compl_prefix:
            for i in range(rem_len):
                if not partial:
                    break
                ch = None
                for j in range(len(rows)):
                    if ch is None:
                        ch = rows[j][i]
                    elif ch != rows[j][i]:
                        partial = False
                        break
                    elif j == len(rows) - 1:
                        string = string + ch

            if string != '':
                cur = self.textCursor()
                pos = cur.position()
                cur.insertText(string)
                cur.setPosition(pos)
                cur.setPosition(pos + len(string), cur.KeepAnchor)
                self.widget().setTextCursor(cur)
                self.showCompletionPopup()

    def acceptPartialCompletion(self):
        # if some text is selected it's a previous partial completion
        # "accept" by clearing selection and move cursor to the end.
        cur = self.textCursor()
        # selection is previous partial completion
        cur.setPosition(cur.selectionEnd())
        cur.clearSelection()
        self.widget().setTextCursor(cur)

    def gotoNextEntry(self, direction):
        self.setCurrentRow((self.currentIndex().row() + direction) %
                           self.completionCount())
        self.popup().setCurrentIndex(self.currentIndex())
