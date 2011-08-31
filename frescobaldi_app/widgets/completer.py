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

"""
Completer providing completions in a Q(Plain)TextEdit.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QEvent, QModelIndex, Qt
from PyQt4.QtGui import QCompleter, QKeySequence, QTextCursor

# most used keyboard modifiers
_SCAM = (Qt.SHIFT | Qt.CTRL | Qt.ALT | Qt.META)


class Completer(QCompleter):
    """A QCompleter providing completions in a Q(Plain)TextEdit.
    
    Use setWidget() to assign the completer to a text edit.
    
    You can reimplement completionCursor to make your own, other than simple
    string-based completions.
    
    Call showCompletionPopup() to force the popup to show.
    
    """
    autoComplete = True
    autoCompleteLength = 1
    
    def __init__(self, *args, **kwargs):
        super(Completer, self).__init__(*args, **kwargs)
        self.activated[QModelIndex].connect(self.insertCompletion)
        
    def eventFilter(self, obj, ev):
        key = (ev.type() == QEvent.KeyPress) and ev.key()
        modifiers = key and int(ev.modifiers() & _SCAM)
        # we can't test for self.popup() as that will recursively call
        # eventFilter during instantiation.
        if not key:
            return super(Completer, self).eventFilter(obj, ev)
        if obj != self.widget():
            # a key was pressed while the popup is visible
            if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Escape):
                # let QCompleter handle navigation in popup
                return super(Completer, self).eventFilter(obj, ev)
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                # insert the highlighted completion
                self.setCurrentRow(self.popup().currentIndex().row())
                self.insertCompletion(self.currentIndex())
                self.popup().hide()
                return True
            else:
                # deliver event and then look for the cursor position
                self.widget().event(ev)
                if self.popupWanted(ev, True):
                    # text was entered, look for the cursor position and
                    # adjust the completionPrefix
                    self.showCompletionPopup()
                    return True
                elif key in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
                    # a modifier key was pressed
                    return True
                elif (ev.matches(QKeySequence.MoveToNextChar) or
                      ev.matches(QKeySequence.MoveToPreviousChar)):
                    # the cursor was moved, hide popup if out range
                    # TODO: implement
                    return True
                # any other key hides the popup
                self.popup().hide()
                return True
        # a key was pressed while the popup is not visible
        self.widget().event(ev)
        if self.autoComplete and self.popupWanted(ev, False):
            self.showCompletionPopup(False)
            
        return True
    
    def popupWanted(self, ev, visible):
        """Called when a key is pressed. Returns whether to show the popup.
        
        ev is the KeyPress event, visible is the current visibility of the popup.
        
        """
        istext = ev.text()[-1:] > " "
        if visible:
            return istext or ev.key() == Qt.Key_Backspace
        else:
            return istext and ev.key() != Qt.Key_Delete

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
        cursor.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
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
            return
        text = cursor.selectedText()
        if forced or (self.autoComplete and len(text) >= self.autoCompleteLength):
            self.setCompletionPrefix(text)
            rect = self.widget().cursorRect(cursor)
            rect.setWidth(self.popup().sizeHintForColumn(0)
                + self.popup().verticalScrollBar().sizeHint().width())
            frameWidth = self.popup().frameWidth()
            rect.translate(-frameWidth, frameWidth + 2)
            self.complete(rect)
        
    def insertCompletion(self, index):
        """Inserts the completion at the given index.
        
        The default implementation reads the model data under the Qt.EditRole,
        and inserts that with the (already entered) completionPrefix removed.
        
        """
        text = self.completionModel().data(index, Qt.EditRole)
        text = text[len(self.completionPrefix()):]
        self.textCursor().insertText(text)



