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
Simple dialogs to ask input from the user.
"""


from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QCompleter, QColorDialog, QWidget

import app
import widgets.dialog
import userguide


def getText(
        parent = None,
        title = "",
        message = "",
        text = "",
        icon = None,
        help = None,
        validate = None,
        regexp = None,
        wordWrap = True,
        complete = None,
        ):
    """Asks a string of text from the user.

    Arguments:

    parent: parent widget or None
    title: dialog window title (without appname)
    message: message, question
    text: pre-entered text in the line edit
    icon: which icon to show
    help: help page or name
    validate: a function that accepts text and returns whether it is valid.
    regexp: a regular expression string. If given it provides an alternate
        validation method using a QRegExpValidator.
    wordWrap: whether to word-wrap the message text (default: True).
    complete: a string list or QAbstractItemModel to provide completions.

    """
    dlg = widgets.dialog.TextDialog(parent,
        title=app.caption(title), message=message, icon=icon)
    dlg.setText(text)
    dlg.setMinimumWidth(320)
    dlg.messageLabel().setWordWrap(wordWrap)
    if help is not None:
        userguide.addButton(dlg.buttonBox(), help)
        dlg.setWindowModality(Qt.WindowModal)
    else:
        dlg.setWindowModality(Qt.ApplicationModal)
    if regexp:
        dlg.setValidateRegExp(regexp)
    elif validate:
        dlg.setValidateFunction(validate)
    if complete:
        c = QCompleter(complete, dlg.lineEdit())
        dlg.lineEdit().setCompleter(c)
    if dlg.exec_():
        return dlg.text()


def getColor(
        parent = None,
        title = "",
        color = None,
        alpha = False,
        ):
    """Ask the user a color."""
    global _savedColor
    if color is None:
        color = _savedColor
    dlg = QColorDialog(color, parent)
    options = QColorDialog.ColorDialogOptions()
    if alpha:
        options |= QColorDialog.ShowAlphaChannel
    if not QSettings().value("native_dialogs/colordialog", True, bool):
        options |= QColorDialog.DontUseNativeDialog
    dlg.setOptions(options)
    dlg.setWindowTitle(title or app.caption(_("Select Color")))
    if dlg.exec_():
        _savedColor = dlg.selectedColor()
        return _savedColor

_savedColor = QColor(Qt.white)


