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
Insert snippets into a Document.
"""


import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QMessageBox

import cursortools
import tokeniter
import indent

from . import snippets
from . import expand


def insert(name, view):
    """Insert named snippet into the view."""
    text, variables = snippets.get(name)
    cursor = view.textCursor()

    selection = variables.get('selection', '')
    if 'yes' in selection and not cursor.hasSelection():
        return
    if 'strip' in selection:
        cursortools.strip_selection(cursor)

    pos = cursor.selectionStart()
    with cursortools.compress_undo(cursor):

        # insert the snippet, might return a new cursor
        if 'python' in variables:
            new = insert_python(text, cursor, name, view)
        elif 'macro' in variables:
            new = insert_macro(text, view)
        else:
            new = insert_snippet(text, cursor, variables)

    # QTextBlocks the snippet starts and ends
    block = cursor.document().findBlock(pos)
    last = cursor.block()

    # re-indent if not explicitly suppressed by a 'indent: no' variable
    if last != block and 'no' not in variables.get('indent', ''):
        c = QTextCursor(last)
        c.setPosition(block.position(), QTextCursor.KeepAnchor)
        with cursortools.compress_undo(c, True):
            indent.re_indent(c, True)

    if not new and 'keep' in selection:
        end = cursor.position()
        cursor.setPosition(pos)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
    view.setTextCursor(new or cursor)


def insert_snippet(text, cursor, variables):
    """Inserts a normal text snippet.

    After the insert, the cursor points to the end of the inserted snippet.

    If this function returns a cursor it must be set as the cursor for the view
    after the snippet has been inserted.

    """
    exp_base = expand.Expander(cursor)

    evs = [] # make a list of events, either text or a constant
    for text, key in snippets.expand(text):
        if text:
            evs.append(text)
        if key == '$':
            evs.append('$')
        elif key:
            # basic variables
            func = getattr(exp_base, key, None)
            if func:
                evs.append(func())

    selectionUsed = expand.SELECTION in evs
    # do the padding if 'selection: strip;' is used
    if selectionUsed and 'strip' in variables.get('selection', ''):
        space = '\n' if '\n' in cursor.selection().toPlainText() else ' '
        # change whitespace in previous and next piece of text
        i = evs.index(expand.SELECTION)
        for j in range(i-1, -i, -1):
            if evs[j] not in expand.constants:
                evs[j] = evs[j].rstrip() + space
                break
        for j in range(i+1, len(evs)):
            if evs[j] not in expand.constants:
                evs[j] = space + evs[j].lstrip()
                break
    # now insert the text
    ins = QTextCursor(cursor)
    selectionUsed and ins.setPosition(cursor.selectionStart())
    a, c = -1, -1
    for e in evs:
        if e == expand.ANCHOR:
            a = ins.position()
        elif e == expand.CURSOR:
            c = ins.position()
        elif e == expand.SELECTION:
            ins.setPosition(cursor.selectionEnd())
        else:
            ins.insertText(e)
    cursor.setPosition(ins.position())
    # return a new cursor if requested
    if (a, c) != (-1, -1):
        new = QTextCursor(cursor)
        if a != -1:
            new.setPosition(a)
        if c != -1:
            new.setPosition(c, QTextCursor.KeepAnchor if a != -1 else QTextCursor.MoveAnchor)
        return new


def insert_python(text, cursor, name, view):
    """Regards the text as Python code, and exec it.

    name and view are given in case an exception occurs.

    The following variables are available:

    - text: contains selection or '', set it to insert new text
    - state: contains simplestate for the cursor position
    - cursor: the QTextCursor

    After the insert, the cursor points to the end of the inserted snippet.

    """
    namespace = {
        'cursor': QTextCursor(cursor),
        'state': state(cursor),
        'text': cursor.selection().toPlainText(),
        'view': view,
        'ANCHOR': 1,
        'CURSOR': 2,
    }
    try:
        code = compile(text, "<snippet>", "exec")
        if sys.version_info < (3, 0):
            exec("exec code in namespace")
        else:
            exec(code, namespace)
        if 'main' in namespace:
            return namespace['main']()
    except Exception:
        handle_exception(name, view)
    else:
        text = namespace.get('text', '')
        if isinstance(text, (tuple, list)):
            ANCHOR = namespace.get('ANCHOR', 1)
            CURSOR = namespace.get('CURSOR', 2)
            a, c = -1, -1
            for t in text:
                if t == ANCHOR:
                    a = cursor.selectionStart()
                elif t == CURSOR:
                    c = cursor.selectionStart()
                else:
                    cursor.insertText(t)
            if (a, c) != (-1, -1):
                new = QTextCursor(cursor)
                if a != -1:
                    new.setPosition(a)
                if c != -1:
                    new.setPosition(c, QTextCursor.KeepAnchor if a != -1 else QTextCursor.MoveAnchor)
                return new
        else:
            cursor.insertText(namespace['text'])


def insert_macro(text, view):
    """The macro snippet is a sequence of commands which are either
    Frescobaldi actions or other snippets.
    """
    import re
    import actioncollectionmanager
    from . import model

    avail_snippets = {}
    for n in model.model().names():
        varname = snippets.get(n).variables.get('name')
        if varname:
            avail_snippets[varname] = n

    avail_actions = {}
    win = view.window()
    for collection in actioncollectionmanager.manager(win).actionCollections():
        for name, action in collection.actions().items():
            avail_actions[name] = action

    commands = [x.strip() for x in text.split('\n') if x]
    for c in commands:
        if c in avail_snippets:
            insert(avail_snippets[c], view)
        elif c in avail_actions:
            avail_actions[c].trigger()


def state(cursor):
    """Returns the simplestate string for the position of the cursor."""
    import simplestate
    pos = cursor.selectionStart()
    block = cursor.document().findBlock(pos)
    tokens = tokeniter.tokens(block)
    state = tokeniter.state(block)
    column = pos - block.position()
    for t in tokens:
        if t.end > column:
            break
        state.follow(t)
    return simplestate.state(state)


def handle_exception(name, view):
    """Called when a snippet raises a Python exception.

    Shows the error message and offers the option to edit the offending snippet.

    """
    import sys, traceback
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb = traceback.extract_tb(exc_traceback)
    while tb and tb[0][0] != "<snippet>":
        del tb[0]
    msg = ''.join(traceback.format_list(tb) +
                    traceback.format_exception_only(exc_type, exc_value))
    dlg = QMessageBox(QMessageBox.Critical, _("Snippet error"), msg,
        QMessageBox.Ok | QMessageBox.Cancel)
    dlg.button(QMessageBox.Ok).setText(_("Edit Snippet"))
    dlg.setDefaultButton(QMessageBox.Cancel)
    dlg.setEscapeButton(QMessageBox.Cancel)
    if dlg.exec_() != QMessageBox.Ok:
        return

    # determine line number
    if exc_type is SyntaxError:
        lineno = exc_value.lineno
    elif tb:
        lineno = tb[0][1]
    else:
        lineno = None

    import panelmanager
    from . import edit
    widget = panelmanager.manager(view.window()).snippettool.widget()
    textedit = edit.Edit(widget, name).text
    if lineno is not None:
        # convert to line number in full snippet text
        for block in cursortools.all_blocks(textedit.document()):
            if block.text().startswith('-*- '):
                lineno += 1
            else:
                break
        block = textedit.document().findBlockByNumber(lineno-1)
        if block.isValid():
            textedit.setTextCursor(QTextCursor(block))


