# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2016 by Wilbert Berendsen
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
Various routines to display meaningful tooltips (text or graphical).

The show() function displays a tooltip showing part of a Document.

"""


from PyQt5.QtCore import QSize
from PyQt5.QtGui import (
    QFont, QPainter, QPixmap, QTextCursor, QTextDocument)
from PyQt5.QtWidgets import QLabel

import metainfo
import tokeniter
import highlighter
import textformats
import gadgets.customtooltip
import tokeniter
import ly.lex.lilypond


def pixmap(cursor, num_lines=6, scale=0.8):
    """Return a QPixmap displaying the selected lines of the document.
    
    If the cursor has no selection, num_lines are drawn.
    
    By default the text is drawn 0.8 * the normal font size. You can change
    that by supplying the scale parameter.
    
    """
    block = cursor.document().findBlock(cursor.selectionStart())
    c2 = QTextCursor(block)
    if cursor.hasSelection():
        c2.setPosition(cursor.selectionEnd(), QTextCursor.KeepAnchor)
        c2.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
    else:
        c2.movePosition(QTextCursor.NextBlock, QTextCursor.KeepAnchor, num_lines)
    
    data = textformats.formatData('editor')
    doc = QTextDocument()
    font = QFont(data.font)
    font.setPointSizeF(font.pointSizeF() * scale)
    doc.setDefaultFont(font)
    doc.setPlainText(c2.selection().toPlainText())
    if metainfo.info(cursor.document()).highlighting:
        highlighter.highlight(doc, state=tokeniter.state(block))
    size = doc.size().toSize() + QSize(8, -4)
    pix = QPixmap(size)
    pix.fill(data.baseColors['background'])
    doc.drawContents(QPainter(pix))
    return pix


def show(cursor, pos=None, num_lines=6):
    """Displays a tooltip showing part of the cursor's Document.
    
    If the cursor has a selection, those blocks are displayed.
    Otherwise, num_lines lines are displayed.
    
    If pos is not given, the global mouse position is used.
    
    """
    pix = pixmap(cursor, num_lines)
    label = QLabel()
    label.setPixmap(pix)
    label.setStyleSheet("QLabel { border: 1px solid #777; }")
    label.resize(pix.size())
    gadgets.customtooltip.show(label, pos)


def text(cursor):
    """Return basic tooltip text displaying filename, line and column information.
    
    If the position is inside a music expression, the name of the variable the
    expression is assigned to is also appended on a new line. If the time
    position can be determined it is appended on a third line.
    
    """
    filename = cursor.document().documentName()
    line = cursor.blockNumber() + 1
    column = cursor.position() - cursor.block().position()
    text = "{0} ({1}:{2})".format(filename, line, column)
    definition = get_definition(cursor)
    if definition:
        text += '\n' + definition
    time_pos = time_position(cursor)
    if time_pos:
        text += '\n' + _("Position: {pos}").format(pos=time_pos)
    return text


def get_definition(cursor):
    """Return the variable name the cursor's music expression is assigned to.
    
    If the music is in a \\score instead, "\\score" is returned.
    Returns None if no variable name can be found.
    
    """
    block = cursor.block()
    while block.isValid():
        state = tokeniter.state(block)
        if isinstance(state.parser(), ly.lex.lilypond.ParseGlobal):
            for t in tokeniter.tokens(block)[:2]:
                if type(t) is ly.lex.lilypond.Name:
                    return t[:]
                elif isinstance(t, ly.lex.lilypond.Keyword) and t == '\\score':
                    return '\\score'
        block = block.previous()


def time_position(cursor):
    """Returns the time position of the music the cursor points at.
    
    Format the value as "5/1" etc.
    
    """
    import documentinfo
    pos = documentinfo.music(cursor.document()).time_position(cursor.position())
    if pos is not None:
        import ly.duration
        return ly.duration.format_fraction(pos)


