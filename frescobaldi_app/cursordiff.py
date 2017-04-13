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
Replaces selected text of a QTextCursor without erasing all the other
QTextCursor instances that exist in the selected range.

This is done by making a diff between the existing selection and the replacing
text, and applying that diff.
"""


import difflib

import cursortools


def insert_text(cursor, text):
    """Replaces selected text of a QTextCursor.

    This is done without erasing all the other QTextCursor instances that could
    exist in the selected range. It works by making a diff between the
    existing selection and the replacement text, and applying that diff.

    """
    if not cursor.hasSelection() or text == "":
        cursor.insertText(text)
        return

    start = cursor.selectionStart()
    new_pos = start + len(text)

    old = cursor.selection().toPlainText()
    diff = difflib.SequenceMatcher(None, old, text).get_opcodes()

    # make a list of edits
    edits = sorted(
        ((start + i1, start + i2, text[j1:j2])
         for tag, i1, i2, j1, j2 in diff
         if tag != 'equal'),
        reverse = True)

    # perform the edits
    with cursortools.compress_undo(cursor):
        for pos, end, text in edits:
            cursor.setPosition(pos)
            cursor.setPosition(end, cursor.KeepAnchor)
            cursor.insertText(text)
    cursor.setPosition(new_pos)


