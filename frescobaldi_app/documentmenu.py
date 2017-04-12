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
The Documents menu.
"""


from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QActionGroup, QMenu

import app
import icons
import plugin
import engrave
import documenticon


class DocumentMenu(QMenu):
    def __init__(self, mainwindow):
        super(DocumentMenu, self).__init__(mainwindow)
        self.aboutToShow.connect(self.populate)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_('menu title', '&Documents'))

    def populate(self):
        self.clear()
        mainwindow = self.parentWidget()
        for a in DocumentActionGroup.instance(mainwindow).actions():
            self.addAction(a)


class DocumentActionGroup(plugin.MainWindowPlugin, QActionGroup):
    """Maintains a list of actions to set the current document.

    The actions are added to the View->Documents menu in the order
    of the tabbar. The actions also get accelerators that are kept
    during the lifetime of a document.

    """
    def __init__(self, mainwindow):
        QActionGroup.__init__(self, mainwindow)
        self._acts = {}
        self._accels = {}
        self.setExclusive(True)
        for d in app.documents:
            self.addDocument(d)
        app.documentCreated.connect(self.addDocument)
        app.documentClosed.connect(self.removeDocument)
        app.documentUrlChanged.connect(self.setDocumentStatus)
        app.documentModificationChanged.connect(self.setDocumentStatus)
        app.jobStarted.connect(self.setDocumentStatus)
        app.jobFinished.connect(self.setDocumentStatus)
        mainwindow.currentDocumentChanged.connect(self.setCurrentDocument)
        engrave.engraver(mainwindow).stickyChanged.connect(self.setDocumentStatus)
        self.triggered.connect(self.slotTriggered)

    def actions(self):
        return [self._acts[doc] for doc in self.mainwindow().documents()]

    def addDocument(self, doc):
        a = QAction(self)
        a.setCheckable(True)
        if doc is self.mainwindow().currentDocument():
            a.setChecked(True)
        self._acts[doc] = a
        self.setDocumentStatus(doc)

    def removeDocument(self, doc):
        self._acts[doc].deleteLater()
        del self._acts[doc]
        del self._accels[doc]

    def setCurrentDocument(self, doc):
        self._acts[doc].setChecked(True)

    def setDocumentStatus(self, doc):
        # create accels
        accels = [self._accels[d] for d in self._accels if d is not doc]
        name = doc.documentName().replace('&', '&&')
        for index, char in enumerate(name):
            if char.isalnum() and char.lower() not in accels:
                name = name[:index] + '&' + name[index:]
                self._accels[doc] = char.lower()
                break
        else:
            self._accels[doc] = ''
        # add [sticky] mark if necessary
        if doc == engrave.engraver(self.mainwindow()).stickyDocument():
            # L10N: 'always engraved': the document is marked as 'Always Engrave' in the LilyPond menu
            name += " " + _("[always engraved]")
        self._acts[doc].setText(name)
        icon = documenticon.icon(doc, self.mainwindow())
        if icon.name() == "text-plain":
            icon = QIcon()
        self._acts[doc].setIcon(icon)

    def slotTriggered(self, action):
        for doc, act in self._acts.items():
            if act == action:
                self.mainwindow().setCurrentDocument(doc)
                break


