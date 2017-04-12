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


import app
import documentinfo
import widgets.dialog

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QCompleter, QVBoxLayout, QMessageBox, QWidget)

from . import model
from . import snippets


class TemplateDialog(widgets.dialog.TextDialog):
    def __init__(self, parent):
        self._lineEdit = None
        super(TemplateDialog, self).__init__(parent)
        self.setWindowTitle(app.caption(_("Save as Template")))
        self.setMessage(_("Please enter a template name:"))
        self.setMinimumWidth(320)
        self.setValidateRegExp(r"\w(.*\w)?")
        e = self._lineEdit = self.mainWidget()
        w = QWidget()
        self.setMainWidget(w)
        c = self._runCheck = QCheckBox(
            _("Run LilyPond when creating a new document from this template"))
        layout = QVBoxLayout(margin=0)
        w.setLayout(layout)
        layout.addWidget(e)
        layout.addWidget(c)
        e.setFocus()

    def lineEdit(self):
        """Return the QLineEdit widget."""
        return self._lineEdit or self.mainWidget()

    def runCheck(self):
        """Return the Run LilyPond checkbox."""
        return self._runCheck


def save(mainwindow):

    titles = dict((snippets.title(name), name)
                  for name in model.model().names()
                  if 'template' in snippets.get(name).variables)

    # would it make sense to run LilyPond after creating a document from this
    # template?
    cursor = mainwindow.textCursor()
    template_run = False
    if documentinfo.mode(cursor.document()) == 'lilypond':
        dinfo = documentinfo.docinfo(cursor.document())
        if dinfo.complete() and dinfo.has_output():
            template_run = True

    dlg = TemplateDialog(mainwindow)
    c = QCompleter(sorted(titles), dlg.lineEdit())
    dlg.lineEdit().setCompleter(c)
    dlg.runCheck().setChecked(template_run)

    result = dlg.exec_()
    dlg.deleteLater()
    if not result:
        return # cancelled

    title = dlg.text()
    template_run = dlg.runCheck().isChecked()

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

    # add header line, if desired enable autorun
    headerline = '-*- template; indent: no;'
    if template_run:
        headerline += ' template-run;'
    text = headerline + '\n' + text

    # save the new snippet
    model.model().saveSnippet(name, text, title)


