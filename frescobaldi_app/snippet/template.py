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
Save the current document as a snippet that appears in File->New from Template.
"""

from __future__ import unicode_literals

import documentinfo
import inputdialog

from PyQt4.QtGui import QMessageBox

from . import model
from . import snippets


def save(mainwindow):
    
    titles = dict((snippets.title(name), name)
                  for name in model.model().names()
                  if 'template' in snippets.get(name).variables)
    title = inputdialog.getText(mainwindow,
        _("Save as Template"),
        _("Please enter a template name:"),
        regexp=r"\w(.*\w)?", complete=sorted(titles))
    if not title:
        return
    
    if title in titles:
        if QMessageBox.critical(mainwindow,
            _("Overwrite Template?"),
            _("A template named \"{name}\" already exists.\n\n"
              "Do you want to overwrite it?").format(name=title),
            QMessageBox.Yes | QMessageBox.Cancel) != QMessageBox.Yes:
            return
        name = titles[title]
    else:
        name = None
    
    # get the text and insert cursor position or selection
    cursor = mainwindow.textCursor()
    text = cursor.document().toPlainText()
    
    repls = [(cursor.position(), '${CURSOR}')]
    if cursor.hasSelection():
        repls.append((cursor.anchor(), '${ANCHOR}'))
        repls.sort()
        
    result = []
    prev = 0
    for pos, what in repls:
        result.append(text[prev:pos].replace('$', '$$'))
        result.append(what)
        prev = pos
    result.append(text[prev:].replace('$', '$$'))
    text = ''.join(result)
    
    # add header line, if it is lilypond, enable autorun
    headerline = '-*- template; indent: no;'
    if documentinfo.mode(cursor.document()) == 'lilypond':
        dinfo = documentinfo.docinfo(cursor.document())
        if dinfo.complete() and dinfo.has_output():
            headerline += ' template-run;'
    text = headerline + '\n' + text
    
    # save the new snippet
    model.model().saveSnippet(name, text, title)


