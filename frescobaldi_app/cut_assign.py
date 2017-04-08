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
Cut selected text and assign it to a LilyPond variable.
"""


import os.path

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import app
import util
import fileinfo
import documentinfo
import cursortools
import tokeniter
import ly.lex.lilypond
import metainfo
import indent
import inputdialog


def cut_assign(cursor):
    """Cuts selected text and assigns it to a LilyPond variable."""
    # ask the variable name
    name = inputdialog.getText(None, _("Cut and Assign"), _(
        "Please enter the name for the variable to assign the selected "
        "text to:"), regexp="[A-Za-z]+")
    if not name:
        return

    cursortools.strip_selection(cursor)

    # determine state at cursor
    block = cursortools.block(cursor)
    state = tokeniter.state(block)
    for t in tokeniter.partition(cursor).left:
        state.follow(t)

    mode = ""
    for p in state.parsers():
        if isinstance(p, ly.lex.lilypond.ParseInputMode):
            if isinstance(p, ly.lex.lilypond.ParseLyricMode):
                mode = " \\lyricmode"
            elif isinstance(p, ly.lex.lilypond.ParseChordMode):
                mode = " \\chordmode"
            elif isinstance(p, ly.lex.lilypond.ParseFigureMode):
                mode = " \\figuremode"
            elif isinstance(p, ly.lex.lilypond.ParseDrumMode):
                mode = " \\drummode"
            break

    # find insertion place:
    found = False
    while block.previous().isValid():
        block = block.previous()
        state = tokeniter.state(block)
        if isinstance(state.parser(), ly.lex.lilypond.ParseGlobal):
            found = True
            break
        tokens = tokeniter.tokens(block)
        for t in tokens:
            if isinstance(t, ly.lex.lilypond.Name):
                found = True
                break
            elif not isinstance(t, (ly.lex.Space, ly.lex.Comment)):
                break
        if found:
            break
    insert = QTextCursor(block)
    text = cursor.selection().toPlainText()
    space = '\n' if '\n' in text else ' '
    text = ''.join((name, ' =', mode, ' {', space, text, space, '}\n\n'))
    with cursortools.compress_undo(cursor):
        cursor.insertText('\\' + name)
        pos = insert.selectionStart()
        insert.insertText(text)
    if metainfo.info(cursor.document()).auto_indent:
        insert.setPosition(pos, QTextCursor.KeepAnchor)
        with cursortools.compress_undo(insert, True):
            indent.re_indent(insert)


def move_to_include_file(cursor, parent_widget=None):
    """Opens a dialog to save the cursor's selection to a file.

    The cursor's selection is then replaced with an \\include statement.
    This function does its best to supply a good default filename and
    use it correctly in a relative \\include statement.

    Of course it only works well if the document already has a filename.

    """
    doc = cursor.document()
    text = cursor.selection().toPlainText()
    mode = fileinfo.textmode(text)
    caption = app.caption(_("dialog title", "Move to include file"))
    filetypes = app.filetypes(ly.lex.extensions[mode])
    name, ext = os.path.splitext(os.path.basename(doc.url().path()))
    if not ext or mode == "lilypond":
        ext = ".ily"
        version = documentinfo.docinfo(doc).version_string()
        if version:
            text = '\\version "{0}"\n\n{1}'.format(version, text)
    docname = name + "-include" + ext
    dirname = os.path.dirname(doc.url().toLocalFile()) or app.basedir()
    filename = os.path.join(dirname, docname)
    filename = QFileDialog.getSaveFileName(parent_widget, caption, filename, filetypes)[0]
    if not filename:
        return # cancelled
    data = util.encode(util.platform_newlines(text))
    try:
        with open(filename, "wb") as f:
            f.write(data)
    except IOError as e:
        msg = _("{message}\n\n{strerror} ({errno})").format(
            message = _("Could not write to: {url}").format(url=filename),
            strerror = e.strerror,
            errno = e.errno)
        QMessageBox.critical(parent_widget, app.caption(_("Error")), msg)
        return
    filename = os.path.relpath(filename, dirname)
    command = '\\include "{0}"\n'.format(filename)
    cursor.insertText(command)


