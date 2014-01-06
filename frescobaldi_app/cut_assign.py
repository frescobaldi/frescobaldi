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

from __future__ import unicode_literals

from PyQt4.QtGui import QTextCursor

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


