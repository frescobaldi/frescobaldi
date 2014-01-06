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
Display a tooltip showing part of a Document.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSize
from PyQt4.QtGui import (
    QFont, QLabel, QPainter, QPixmap, QTextCursor, QTextDocument)

import metainfo
import tokeniter
import highlighter
import textformats
import widgets.customtooltip


def show(cursor, pos=None, num_lines=6):
    """Displays a tooltip showing part of the cursor's Document.
    
    If the cursor has a selection, those blocks are displayed.
    Otherwise, num_lines lines are displayed.
    
    If pos is not given, the global mouse position is used.
    
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
    font.setPointSizeF(font.pointSizeF() * .8)
    doc.setDefaultFont(font)
    doc.setPlainText(c2.selection().toPlainText())
    if metainfo.info(cursor.document()).highlighting:
        highlighter.highlight(doc, state=tokeniter.state(block))
    size = doc.size().toSize() + QSize(8, -4)
    pix = QPixmap(size)
    pix.fill(data.baseColors['background'])
    doc.drawContents(QPainter(pix))
    label = QLabel()
    label.setPixmap(pix)
    label.setStyleSheet("QLabel { border: 1px solid #777; }")
    label.resize(size)
    widgets.customtooltip.show(label, pos)


