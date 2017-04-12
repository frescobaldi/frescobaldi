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
A basic Dialog class.
"""


import functools
import operator

from PyQt5.QtCore import QRegExp, QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QRegExpValidator
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QGridLayout, QLabel, QLineEdit, QStyle,
    QWidget)

from . import Separator


__all__ = ['Dialog', 'TextDialog']


standardicons = {
    'info': QStyle.SP_MessageBoxInformation,
    'warning': QStyle.SP_MessageBoxWarning,
    'critical': QStyle.SP_MessageBoxCritical,
    'question': QStyle.SP_MessageBoxQuestion,
}

standardbuttons = {
    'ok': QDialogButtonBox.Ok,
    'open': QDialogButtonBox.Open,
    'save': QDialogButtonBox.Save,
    'cancel': QDialogButtonBox.Cancel,
    'close': QDialogButtonBox.Close,
    'discard': QDialogButtonBox.Discard,
    'apply': QDialogButtonBox.Apply,
    'reset': QDialogButtonBox.Reset,
    'restoredefaults': QDialogButtonBox.RestoreDefaults,
    'help': QDialogButtonBox.Help,
    'saveall': QDialogButtonBox.SaveAll,
    'yes': QDialogButtonBox.Yes,
    'yestoall': QDialogButtonBox.YesToAll,
    'no': QDialogButtonBox.No,
    'notoall': QDialogButtonBox.NoToAll,
    'abort': QDialogButtonBox.Abort,
    'retry': QDialogButtonBox.Retry,
    'ignore': QDialogButtonBox.Ignore,
}


class Dialog(QDialog):
    """A Dialog with basic layout features:

    a main widget,
    an icon or pixmap,
    a separator,
    buttons (provided by a QDialogButtonBox)

    """
    def __init__(self,
                 parent = None,
                 message = "",
                 title = "",
                 icon = None,
                 iconSize = QSize(64, 64),
                 pixmap = None,
                 separator = True,
                 buttonOrientation = Qt.Horizontal,
                 buttons = ('ok', 'cancel'),
                 help = None,
                 **kwargs):
        """Initializes the dialog.

        parent = a parent widget or None.

        The following keyword arguments are recognized:
        - message: the text to display in the message label
        - title: the window title
        - icon or pixmap: shown in the left area
        - iconSize: size of the icon in the left (QSize, default: 64x64)
        - separator: draw a separator line or not (default: True)
        - buttonOrientation: Qt.Horizontal (default) or Qt.Vertical
        - buttons: which buttons to use (default: Ok, Cancel)
        - help: function to call when a help button is clicked.

        Other keyword arguments are passed to QDialog.

        """
        super(Dialog, self).__init__(parent, **kwargs)
        self._icon = QIcon()
        self._separatorWidget = Separator()
        self._mainWidget = QWidget()
        self._pixmap = QPixmap()
        self._pixmapLabel = QLabel(self)
        self._messageLabel = QLabel(self)
        self._buttonBox = b = QDialogButtonBox(self)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        layout = QGridLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        # handle keyword args
        self._buttonOrientation = buttonOrientation
        self._iconSize = iconSize
        self._separator = separator
        if title:
            self.setWindowTitle(title)
        self.setMessage(message)
        if icon:
            self.setIcon(icon)
        elif pixmap:
            self.setPixmap(pixmap)
        b.helpRequested.connect(help or self.helpRequest)
        self.setStandardButtons(buttons)
        self.reLayout()

    def helpRequest(self):
        """Called when a help button is clicked."""
        pass

    def setButtonOrientation(self, orientation):
        """Sets the button orientation.

        Qt.Horizontal (default) puts the buttons at the bottom of the dialog
        in a horizontal row, Qt.Vertical puts the buttons at the right in a
        vertical column.

        """
        if orientation != self._buttonOrientation:
            self._buttonOrientation = orientation
            self._buttonBox.setOrientation(orientation)
            self.reLayout()

    def buttonOrientation(self):
        """Returns the button orientation."""
        return self._buttonOrientation

    def setIcon(self, icon):
        """Sets the icon to display in the left area.

        May be:
        - None or QIcon()
        - one of 'info', 'warning', 'critical', 'question'
        - a QStyle.StandardPixmap
        - a QIcon.

        """
        if icon in standardicons:
            icon = standardicons[icon]
        if isinstance(icon, QStyle.StandardPixmap):
            icon = self.style().standardIcon(icon)
        if icon is None:
            icon = QIcon()
        self._icon = icon
        self.setPixmap(icon.pixmap(self._iconSize))

    def icon(self):
        """Returns the currently set icon as a QIcon."""
        return self._icon

    def setIconSize(self, size):
        """Sets the icon size (QSize or int)."""
        if isinstance(size, int):
            size = QSize(size, size)
        changed = size != self._iconSize
        self._iconSize = size
        if changed and not self._icon.isNull():
            self.setPixmap(self._icon.pixmap(size))

    def iconSize(self):
        """Returns the icon size (QSize)."""
        return self._iconSize

    def setPixmap(self, pixmap):
        """Sets the pixmap to display in the left area."""
        changed = self._pixmap.isNull() != pixmap.isNull()
        self._pixmap = pixmap
        self._pixmapLabel.setPixmap(pixmap)
        if not pixmap.isNull():
            self._pixmapLabel.setFixedSize(pixmap.size())
        if changed:
            self.reLayout()

    def pixmap(self):
        """Returns the currently set pixmap."""
        return self._pixmap

    def setMessage(self, text):
        """Sets the main text in the dialog."""
        self._messageLabel.setText(text)

    def message(self):
        """Returns the main text."""
        return self._messageLabel.text()

    def messageLabel(self):
        """Returns the QLabel displaying the message text."""
        return self._messageLabel

    def buttonBox(self):
        """Returns our QDialogButtonBox instance."""
        return self._buttonBox

    def setStandardButtons(self, buttons):
        """Convenience method to set standard buttons in the button box.

        Accepts a sequence of string names from the standardbuttons constant,
        or a QDialogButtonBox.StandardButtons value.

        """
        if isinstance(buttons, (set, tuple, list)):
            buttons = functools.reduce(operator.or_,
                map(standardbuttons.get, buttons),
                QDialogButtonBox.StandardButtons())
        self._buttonBox.setStandardButtons(buttons)

    def button(self, button):
        """Returns the given button.

        May be a QDialogButtonBox.StandardButton or a key from standardbuttons.

        """
        if button in standardbuttons:
            button = standardbuttons[button]
        return self._buttonBox.button(button)

    def setSeparator(self, enabled):
        """Sets whether to show a line between contents and buttons."""
        changed = self._separator != enabled
        self._separator = enabled
        if changed:
            self.reLayout()

    def hasSeparator(self):
        """Returns whether a separator line is shown."""
        return self._separator

    def setMainWidget(self, widget):
        """Sets the specified widget as our main widget."""
        old = self._mainWidget
        if old:
            old.setParent(None)
        self._mainWidget = widget
        self.reLayout()

    def mainWidget(self):
        """Returns the current main widget (an empty QWidget by default)."""
        return self._mainWidget

    def reLayout(self):
        """(Internal) Lays out all items in this dialog."""
        layout = self.layout()
        while layout.takeAt(0):
            pass

        if not self._pixmap.isNull():
            col = 1
            layout.addWidget(self._pixmapLabel, 0, 0, 2, 1)
        else:
            layout.setColumnStretch(1, 0)
            col = 0
        layout.setColumnStretch(col, 1)
        self._pixmapLabel.setVisible(not self._pixmap.isNull())
        layout.addWidget(self._messageLabel, 0, col)
        layout.addWidget(self._mainWidget, 1, col)
        if self._buttonOrientation == Qt.Horizontal:
            if self._separator:
                layout.addWidget(self._separatorWidget, 2, 0, 1, col+1)
            layout.addWidget(self._buttonBox, 3, 0, 1, col+1)
        else:
            if self._separator:
                layout.addWidget(self._separatorWidget, 0, col+1, 2, 1)
            layout.addWidget(self._buttonBox, 0, col+2, 2, 1)
        self._separatorWidget.setVisible(self._separator)


class TextDialog(Dialog):
    """A dialog with text string input and validation."""
    def __init__(self, parent, *args, **kwargs):
        super(TextDialog, self).__init__(parent, *args, **kwargs)
        self._validateFunction = None
        self.setMainWidget(QLineEdit())
        self.lineEdit().setFocus()

    def lineEdit(self):
        """Returns the QLineEdit widget."""
        return self.mainWidget()

    def setText(self, text):
        """Sets the text in the lineEdit()."""
        self.lineEdit().setText(text)

    def text(self):
        """Returns the text in the lineEdit()."""
        return self.lineEdit().text()

    def setValidateFunction(self, func):
        """Sets a function to run on every change in the lineEdit().

        If the function returns True, the OK button is enabled, otherwise
        disabled.

        If func is None, an earlier validate function will be removed.

        """
        old = self._validateFunction
        self._validateFunction = func
        if func:
            self._validate(self.lineEdit().text())
            if not old:
                self.lineEdit().textChanged.connect(self._validate)
        elif old:
            self.lineEdit().textChanged.disconnect(self._validate)
            self.button('ok').setEnabled(True)

    def setValidateRegExp(self, regexp):
        """Sets a regular expression the text must match.

        If the regular expression matches the full text, the OK button is
        enabled, otherwise disabled.

        If regexp is None, an earlier set regular expression is removed.

        """
        validator = function = None
        if regexp is not None:
            rx = QRegExp(regexp)
            validator = QRegExpValidator(rx, self.lineEdit())
            function = rx.exactMatch
        self.lineEdit().setValidator(validator)
        self.setValidateFunction(function)

    def _validate(self, text):
        self.button('ok').setEnabled(self._validateFunction(text))


