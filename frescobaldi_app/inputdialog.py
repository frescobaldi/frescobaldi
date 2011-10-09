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
Simple dialogs to ask input from the user.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import Qt, QRegExp
from PyQt4.QtGui import QLineEdit, QRegExpValidator

import widgets.dialog
import help as help_



def getText(
        parent = None,
        title = "",
        message = "",
        text = "",
        icon = None,
        help = None,
        validate_function = None,
        regex = None,
        ):
    """Asks a string of text from the user.
    
    Arguments:
    
    parent: parent widget or None
    title: dialog window title
    message: message, question
    text: pre-entered text in the line edit
    icon: which icon to show
    help: help page or name
    validate_function: a function that accepts text and returns whether
        it is valid.
    regexp: a regular expression string. If given it provides an alternate
        validation method using a QRegExpValidator.
    
    """    
    dlg = widgets.dialog.Dialog(parent,
        title=title, message=message, icon=icon)
    e = QLineEdit()
    dlg.setMainWidget(e)
    e.setText(text)
    e.setFocus()
    if help is not None:
        help_.addButton(dlg.buttonBox(), help)
        dlg.setWindowModality(Qt.WindowModal)
    else:
        dlg.setWindowModality(Qt.ApplicationModal)
    if regex:
        rx = QRegExp(regex)
        e.setValidator(QRegExpValidator(rx, e))
        validate_function = rx.exactMatch
    if validate_function:
        def validate(text):
            dlg.button('ok').setEnabled(validate_function(text))
        e.textChanged.connect(validate)
        validate(text)
    
    if dlg.exec_():
        return e.text()


