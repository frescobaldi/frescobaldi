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

Generate the include files' tooltips
"""


import os
import re

from PyQt5.QtCore import QUrl 

import documentinfo
import browseriface

# regular expression for finding \include expressions
incl_regex = re.compile('(\\include\s*\")(.*)(\")')

def includeTarget(cursor):
    """Given a cursor determine an absolute path to an include file present below the cursor.
    Return path or empty string if no valid file is found.

    Note that there is still functionality related to opening all targets in the current block.
    Once it has decided that we only want to open *one* target at a time we should change
    from a list back to a single string (here and in view.py).
    """

    block = cursor.block()
    cursor_pos = cursor.position() - block.position()
    fnames = []

    m = incl_regex.search(block.text())
    while m:
        start = m.span()[0] + len(m.group(1))
        if start <= cursor_pos <= m.span()[1] - 1:
            fnames.append(m.group(2))
            break
        m = incl_regex.search(block.text(), m.span()[1])

    if not fnames:
        return ""

    # determine search path: doc dir and other include path names
    filename = cursor.document().url().toLocalFile()
    path = [os.path.dirname(filename)] if filename else []
    dinfo = documentinfo.info(cursor.document())
    path.extend(dinfo.includepath())

    targets = []
    # iterating over the search paths, find the first combination pointing to an existing file
    for f in fnames:
        for p in path:
            name = os.path.normpath(os.path.join(p, f))
            if os.path.exists(name) and not os.path.isdir(name):
                targets.append(name)
                continue
    return targets

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
    return open_targets(filenames_at_cursor(cursor))

def open_targets(mainwindow, targets):
    """Open all given files, giving focus to the last one.

    Return True if there were one or more filenames that were opened.

    """
    d = None
    for t in targets:
        d = mainwindow.openUrl(QUrl.fromLocalFile(t))
    if d:
        browseriface.get(mainwindow).setCurrentDocument(d, True)
        return True
