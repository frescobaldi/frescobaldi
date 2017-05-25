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
Opens a file the current textcursor points at (or has selected).

Highlight the included files.
"""


import os

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QTextCharFormat, QFont, QTextCursor  

import documentinfo
import browseriface



def hightlightIncluded(cursor, option):
    """Highligtht / Unhighlight all the included files in current view.
    
    - When option is True, highlight the included files.
    
    - When option is False, unhighlight the included files.      
    
    """
    # search starts from startIndex
    startIndex = 0
    cursor = cursor.document().find('\include', startIndex)
    
    # find and highlight an include file each loop
    while not cursor.isNull():
        block = cursor.block()
        blockText = block.text()
        blockHead = block.position()
        blockTail = blockHead + block.length()
        # update startIndex
        startIndex = blockTail
        dinfo = documentinfo.info(cursor.document())
        i = dinfo.lydocinfo().range(blockHead, blockTail)
        fnames = i.include_args() or i.scheme_load_args()
        if not fnames:
            continue
        for name in fnames:
            nameHead = blockText.find(name) + blockHead
            nameTail = len(name) + nameHead
            testFormat = QTextCharFormat()
            if option:
                # highlight the file name
                testFormat.setFontWeight(QFont.Bold)
                testFormat.setUnderlineStyle(QTextCharFormat.SingleUnderline)
            else:
                # unhighlight the file name
                testFormat.setFontWeight(QFont.Normal)
                testFormat.setUnderlineStyle(QTextCharFormat.NoUnderline)
            cursor.setPosition(nameHead)
            cursor.setPosition(nameTail, QTextCursor.KeepAnchor)
            cursor.setCharFormat(testFormat)
        cursor = cursor.document().find('\include', startIndex)      

def filenames_at_cursor(cursor, existing=True):
    """Return a list of filenames at the cursor.

    If existing is False, also names are returned that do not exist on disk.

    """
    # take either the selection or the include-args found by lydocinfo
    start = cursor.document().findBlock(cursor.selectionStart()).position()
    end = cursor.selectionEnd()
    if not cursor.hasSelection():
        end = start + len(cursor.block().text()) + 1
    dinfo = documentinfo.info(cursor.document())
    i = dinfo.lydocinfo().range(start, end)
    fnames = i.include_args() or i.scheme_load_args()
    if not fnames and cursor.hasSelection():
        text = cursor.selection().toPlainText()
        if '\n' not in text.strip():
            fnames = [text]

    # determine search path: doc dir and other include path names
    filename = cursor.document().url().toLocalFile()
    directory = os.path.dirname(filename)
    if filename:
        path = [directory]
    else:
        path = []
    path.extend(dinfo.includepath())

    # find all docs, trying all include paths
    filenames = []
    for f in fnames:
        for p in path:
            name = os.path.normpath(os.path.join(p, f))
            if os.access(name, os.R_OK):
                filenames.append(name)
                break
        else:
            if not existing:
                name = os.path.normpath(os.path.join(directory, f))
                filenames.append(name)
    return filenames

def open_file_at_cursor(mainwindow, cursor=None):
    """Open the filename(s) mentioned at the mainwindow's text cursor.

    Return True if there were one or more filenames that were opened.

    """
    if cursor is None:
        cursor = mainwindow.textCursor()
    d = None
    for name in filenames_at_cursor(cursor):
        d = mainwindow.openUrl(QUrl.fromLocalFile(name))
    # unghlight the files before open the new document      
    hightlightIncluded(cursor, False) 
    if d:
        browseriface.get(mainwindow).setCurrentDocument(d, True)
        return True
