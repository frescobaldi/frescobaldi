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
Session dialog for named session stuff.
"""


import os
import json

from PyQt5.QtCore import Qt, QSettings, QUrl
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QGroupBox, QLabel, QListWidgetItem, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout)

import app
import widgets.listedit
import widgets.urlrequester
import sessions.manager
import qsettings
import userguide


class SessionManagerDialog(QDialog):
    def __init__(self, mainwindow):
        super(SessionManagerDialog, self).__init__(mainwindow)
        self.setWindowModality(Qt.WindowModal)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.sessions = SessionList(self)
        layout.addWidget(self.sessions)

        self.imp = QPushButton(self)
        self.exp = QPushButton(self)
        self.act = QPushButton(self)
        self.imp.clicked.connect(self.importSession)
        self.exp.clicked.connect(self.exportSession)
        self.act.clicked.connect(self.activateSession)

        self.sessions.layout().addWidget(self.imp, 5, 1)
        self.sessions.layout().addWidget(self.exp, 6, 1)
        self.sessions.layout().addWidget(self.act, 7, 1)

        layout.addWidget(widgets.Separator())

        self.buttons = b = QDialogButtonBox(self)
        layout.addWidget(b)
        b.setStandardButtons(QDialogButtonBox.Close)
        b.rejected.connect(self.accept)
        userguide.addButton(b, "sessions")
        self.sessions.load()
        app.translateUI(self)
        self.sessions.changed.connect(self.enableButtons)
        self.sessions.listBox.itemSelectionChanged.connect(self.enableButtons)
        self.enableButtons()

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Manage Sessions")))
        self.imp.setText(_("&Import..."))
        self.imp.setToolTip(_("Opens a dialog to import a session from a file."))
        self.exp.setText(_("E&xport..."))
        self.exp.setToolTip(_("Opens a dialog to export a session to a file."))
        self.act.setText(_("&Activate"))
        self.act.setToolTip(_("Switches to the selected session."))

    def enableButtons(self):
        """Called when the selection in the listedit changes."""
        enabled = bool(self.sessions.listBox.currentItem())
        self.act.setEnabled(enabled)
        self.exp.setEnabled(enabled)

    def importSession(self):
        """Called when the user clicks Import."""
        filetypes = '{0} (*.json);;{1} (*)'.format(_("JSON Files"), _("All Files"))
        caption = app.caption(_("dialog title", "Import session"))
        mainwindow = self.parent()
        directory = os.path.dirname(mainwindow.currentDocument().url().toLocalFile()) or app.basedir()
        importfile = QFileDialog.getOpenFileName(mainwindow, caption, directory, filetypes)[0]
        if not importfile:
            return # cancelled by user
        try:
            with open(importfile, 'r') as f:
                self.sessions.importItem(json.load(f))
        except IOError as e:
            msg = _("{message}\n\n{strerror} ({errno})").format(
                message = _("Could not read from: {url}").format(url=importfile),
                strerror = e.strerror,
                errno = e.errno)
            QMessageBox.critical(self, app.caption(_("Error")), msg)

    def exportSession(self):
        """Called when the user clicks Export."""
        itemname, jsondict = self.sessions.exportItem()
        caption = app.caption(_("dialog title", "Export session"))
        filetypes = '{0} (*.json);;{1} (*)'.format(_("JSON Files"), _("All Files"))
        mainwindow = self.parent()
        directory = os.path.dirname(mainwindow.currentDocument().url().toLocalFile()) or app.basedir()
        filename = os.path.join(directory, itemname + ".json")
        filename = QFileDialog.getSaveFileName(mainwindow, caption, filename, filetypes)[0]
        if not filename:
            return False # cancelled
        try:
            with open(filename, 'w') as f:
                json.dump(jsondict, f, indent=4)
        except IOError as e:
            msg = _("{message}\n\n{strerror} ({errno})").format(
                message = _("Could not write to: {url}").format(url=filename),
                strerror = e.strerror,
                errno = e.errno)
            QMessageBox.critical(self, app.caption(_("Error")), msg)

    def activateSession(self):
        """Called when the user clicks Activate."""
        item = self.sessions.listBox.currentItem()
        if item:
            name = item.text()
            mainwindow = self.parent()
            man = sessions.manager.get(mainwindow)
            man.saveCurrentSessionIfDesired()
            self.accept()
            man.startSession(name)


class SessionList(widgets.listedit.ListEdit):
    """Manage the list of sessions."""
    def load(self):
        """Loads the list of session names in the list edit."""
        names = sessions.sessionNames()
        current = sessions.currentSession()
        self.setValue(names)
        if current in names:
            self.setCurrentRow(names.index(current))

    def removeItem(self, item):
        """Reimplemented to delete the specified session."""
        sessions.deleteSession(item.text())
        super(SessionList, self).removeItem(item)

    def openEditor(self, item):
        """Reimplemented to allow editing the specified session."""
        name = SessionEditor(self).edit(item.text())
        if name:
            item.setText(name)
            return True

    def importItem(self, data):
        """Implement importing a new session from a json data dict."""
        name = data['name']
        session = sessions.sessionGroup(name)
        for key in data:
            if key == 'urls':
                urls = []
                for u in data[key]:
                    urls.append(QUrl(u))
                session.setValue("urls", urls)
            elif key != 'name':
                session.setValue(key, data[key])
        self.load()
        names = sessions.sessionNames()
        if name in names:
            self.setCurrentRow(names.index(name))

    def exportItem(self):
        """Implement exporting the currently selected session item to a dict.

        Returns the dict, which can be dumped as a json data dictionary.

        """
        jsondict = {}
        item = self.listBox.currentItem()
        s = sessions.sessionGroup(item.text())
        for key in s.allKeys():
            if key == 'urls':
                urls = []
                for u in s.value(key):
                    urls.append(u.toString())
                jsondict[key] = urls
            else:
                jsondict[key] = s.value(key)
        return (item.text(), jsondict)


class SessionEditor(QDialog):
    def __init__(self, parent=None):
        super(SessionEditor, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)

        layout = QVBoxLayout()
        self.setLayout(layout)

        grid = QGridLayout()
        layout.addLayout(grid)

        self.name = QLineEdit()
        self.nameLabel = l = QLabel()
        l.setBuddy(self.name)
        grid.addWidget(l, 0, 0)
        grid.addWidget(self.name, 0, 1)

        self.autosave = QCheckBox()
        grid.addWidget(self.autosave, 1, 1)

        self.basedir = widgets.urlrequester.UrlRequester()
        self.basedirLabel = l = QLabel()
        l.setBuddy(self.basedir)
        grid.addWidget(l, 2, 0)
        grid.addWidget(self.basedir, 2, 1)

        self.inclPaths = ip = QGroupBox(self, checkable=True, checked=False)
        ipLayout = QVBoxLayout()
        ip.setLayout(ipLayout)

        self.replPaths = QCheckBox()
        ipLayout.addWidget(self.replPaths)
        self.replPaths.toggled.connect(self.toggleReplace)

        self.include = widgets.listedit.FilePathEdit()
        self.include.listBox.setDragDropMode(QAbstractItemView.InternalMove)
        ipLayout.addWidget(self.include)

        grid.addWidget(ip, 3, 1)

        self.revt = QPushButton(self)
        self.clear = QPushButton(self)
        self.revt.clicked.connect(self.revertPaths)
        self.clear.clicked.connect(self.clearPaths)

        self.include.layout().addWidget(self.revt, 5, 1)
        self.include.layout().addWidget(self.clear, 6, 1)

        layout.addWidget(widgets.Separator())
        self.buttons = b = QDialogButtonBox(self)
        layout.addWidget(b)
        b.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "sessions")
        app.translateUI(self)

    def translateUI(self):
        self.nameLabel.setText(_("Name:"))
        self.autosave.setText(_("Always save the list of documents in this session"))
        self.basedirLabel.setText(_("Base directory:"))
        self.inclPaths.setTitle(_("Use session specific include path"))
        self.replPaths.setText(_("Replace global path"))
        self.replPaths.setToolTip(_("When checked, paths in LilyPond preferences are not included."))
        self.revt.setText(_("Copy global path"))
        self.revt.setToolTip(_("Add and edit the path from LilyPond preferences."))
        self.clear.setText(_("Clear"))
        self.clear.setToolTip(_("Remove all paths."))

    def load(self, name):
        settings = sessions.sessionGroup(name)
        self.autosave.setChecked(settings.value("autosave", True, bool))
        self.basedir.setPath(settings.value("basedir", "", str))
        self.include.setValue(qsettings.get_string_list(settings, "include-path"))
        self.inclPaths.setChecked(settings.value("set-paths", False, bool))
        self.replPaths.setChecked(settings.value("repl-paths", False, bool))
        if not self.replPaths.isChecked():
            self.addDisabledGenPaths()
            self.revt.setEnabled(False)
        # more settings here

    def fetchGenPaths(self):
        """Fetch paths from general preferences."""
        return qsettings.get_string_list(QSettings(),
            "lilypond_settings/include_path")

    def addDisabledGenPaths(self):
        """Add global paths, but set as disabled."""
        genPaths = self.fetchGenPaths()
        for p in genPaths:
            i = QListWidgetItem(p, self.include.listBox)
            i.setFlags(Qt.NoItemFlags)

    def toggleReplace(self):
        """Called when user changes setting for replace of global paths."""
        if self.replPaths.isChecked():
            items = self.include.items()
            for i in items:
                if not (i.flags() & Qt.ItemIsEnabled): #is not enabled
                    self.include.listBox.takeItem(self.include.listBox.row(i))
            self.revt.setEnabled(True)
        else:
            self.addDisabledGenPaths()
            self.revt.setEnabled(False)

    def revertPaths(self):
        """Add global paths (for edit)."""
        genPaths = self.fetchGenPaths()
        for p in genPaths:
            i = QListWidgetItem(p, self.include.listBox)

    def clearPaths(self):
        """Remove all active paths."""
        items = self.include.items()
        for i in items:
            if i.flags() & Qt.ItemIsEnabled:
                self.include.listBox.takeItem(self.include.listBox.row(i))

    def save(self, name):
        settings = sessions.sessionGroup(name)
        settings.setValue("autosave", self.autosave.isChecked())
        settings.setValue("basedir", self.basedir.path())
        settings.setValue("set-paths", self.inclPaths.isChecked())
        settings.setValue("repl-paths", self.replPaths.isChecked())
        path = [i.text() for i in self.include.items() if i.flags() & Qt.ItemIsEnabled]
        settings.setValue("include-path", path)
        # more settings here

    def defaults(self):
        self.autosave.setChecked(True)
        self.basedir.setPath('')
        self.inclPaths.setChecked(False)
        self.replPaths.setChecked(False)
        self.addDisabledGenPaths()
        self.revt.setEnabled(False)
        # more defaults here

    def edit(self, name=None):
        self._originalName = name
        if name:
            caption = _("Edit session: {name}").format(name=name)
            self.name.setText(name)
            self.load(name)
        else:
            caption = _("Edit new session")
            self.name.clear()
            self.name.setFocus()
            self.defaults()
        self.setWindowTitle(app.caption(caption))
        if self.exec_():
            # name changed?
            name = self.name.text()
            if self._originalName and name != self._originalName:
                sessions.renameSession(self._originalName, name)
            self.save(name)
            return name

    def done(self, result):
        if not result or self.validate():
            super(SessionEditor, self).done(result)

    def validate(self):
        """Checks if the input is acceptable.

        If this method returns True, the dialog is accepted when OK is clicked.
        Otherwise a messagebox could be displayed, and the dialog will remain
        visible.
        """
        name = self.name.text().strip()
        self.name.setText(name)
        if not name:
            self.name.setFocus()
            QMessageBox.warning(self, app.caption(_("Warning")),
                _("Please enter a session name."))
            if self._originalName:
                self.name.setText(self._originalName)
            return False

        elif name == '-':
            self.name.setFocus()
            QMessageBox.warning(self, app.caption(_("Warning")),
                _("Please do not use the name '{name}'.".format(name="-")))
            return False

        elif self._originalName != name and name in sessions.sessionNames():
            self.name.setFocus()
            box = QMessageBox(QMessageBox.Warning, app.caption(_("Warning")),
                _("Another session with the name {name} already exists.\n\n"
                  "Do you want to overwrite it?").format(name=name),
                QMessageBox.Discard | QMessageBox.Cancel, self)
            box.button(QMessageBox.Discard).setText(_("Overwrite"))
            result = box.exec_()
            if result != QMessageBox.Discard:
                return False

        return True

