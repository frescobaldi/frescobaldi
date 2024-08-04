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
LilyPond preferences page
"""


from dataclasses import dataclass
import functools
import json
import os
import platform
import shutil
import sys
import tempfile

from PyQt6.QtCore import pyqtSignal, QSettings, Qt, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox,
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidgetItem,
    QMenu, QMessageBox, QPushButton, QRadioButton, QTabWidget, QVBoxLayout,
    QWidget)

import app
import userguide
import qutil
import icons
import preferences
import lilypondinfo
import linux
import qsettings
import widgets.listedit
import widgets.urlrequester


def settings():
    s = QSettings()
    s.beginGroup("lilypond_settings")
    return s

@functools.lru_cache(maxsize=None) # can become @functools.cache in Python 3.9+
def _network_manager():
    return QNetworkAccessManager()


class LilyPondPrefs(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super().__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(Versions(self))
        layout.addWidget(Target(self))
        layout.addWidget(Running(self))


class Versions(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.instances = InfoList(self)
        self.instances.changed.connect(self.changed)
        self.instances.defaultButton.clicked.connect(self.defaultButtonClicked)
        layout.addWidget(self.instances)
        self.autoVersion = QCheckBox(clicked=self.changed)
        layout.addWidget(self.autoVersion)
        app.translateUI(self)
        userguide.openWhatsThis(self)

    def defaultButtonClicked(self):
        item = self.instances.listBox.currentItem()
        # This holds because otherwise the "Set as Default" button would
        # be greyed out.
        assert isinstance(item.state, InstalledState)
        # Register the current default instance (identified by its command)
        self._defaultCommand = item.state.info.command
        # Remove the [default] marker from the previous item that had it.
        for item in self.instances.items():
            item.display()
        self.changed.emit()

    def translateUI(self):
        self.setTitle(_("LilyPond versions to use"))
        self.autoVersion.setText(_("Automatically choose LilyPond version from document"))
        self.autoVersion.setToolTip(_(
            "If checked, the document's version determines the LilyPond version to use.\n"
            "See \"What's This\" for more information."))
        self.autoVersion.setWhatsThis(userguide.html("prefs_lilypond_autoversion") +
            _("See also {link}.").format(link=userguide.link("prefs_lilypond")))

    def loadSettings(self):
        s = settings()
        default = lilypondinfo.default()
        self._defaultCommand = s.value("default", default.command, str)
        self.autoVersion.setChecked(s.value("autoversion", False, bool))
        infos = sorted(lilypondinfo.infos(), key=lambda i: i.version())
        if not infos:
            infos = [default]
        items = [InfoItem(InstalledState(info)) for info in infos]
        self.instances.setItems(items)
        # Make the default version selected initially
        for item in items:
            if item.state.info.command == self._defaultCommand:
                self.instances.setCurrentItem(item)
                break

    def saveSettings(self):
        infos = []
        pending_items = []
        for item in self.instances.items():
            if isinstance(item.state, DownloadingState):
                pending_items.append(item)
            elif isinstance(item.state, InstalledState):
                infos.append(item.state.info)
            # nothing to do for DownloadErrorState, just discard these
        if pending_items:
            answer = QMessageBox.warning(
                self, app.caption("Downloads pending"),
                _("LilyPond downloads are in progress. Stop them?"),
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if answer == QMessageBox.StandardButton.Cancel:
                raise preferences.CancelClosingPreferences
            else:
                # Stop unfinished downloads
                for item in pending_items:
                    item.abortDownload()
        if infos:
            for info in infos:
                if info.command == self._defaultCommand:
                    break
            else:
                self._defaultCommand = infos[0].command
        else:
            infos = [lilypondinfo.default()]
            self._defaultCommand = infos[0].command
        s = settings()
        s.setValue("default", self._defaultCommand)
        s.setValue("autoversion", self.autoVersion.isChecked())
        lilypondinfo.setinfos(infos)
        lilypondinfo.saveinfos()


class InfoList(widgets.listedit.ListEdit):
    def __init__(self, group):
        # Compared to a basic ListEdit, this widget also has a "Set as Default"
        # button. This must be initialized before the base class __init__, because
        # it calls updateSelection().
        self.defaultButton = QPushButton()

        super().__init__(group)

        # The "Add" button is transformed into a menu.
        self.addMenu = AddMenu(self)
        self.addButton.setMenu(self.addMenu)

        self.layout().addWidget(self.defaultButton, 3, 1)
        self.layout().addWidget(self.listBox, 0, 0, 5, 1)

    def translateUI(self):
        super().translateUI()
        self.defaultButton.setText(_("Set as &Default"))

    def updateSelection(self):
        """Overridden to grey out the "Edit" and "Set as Default" buttons in more cases."""
        super().updateSelection()
        # "Edit" and "Set as Default" are greyed out not only when there are
        # no items at all, but also when the current item is for a version that
        # is being downloaded. In theory, "Edit" could be made to work (with
        # some refactorings) on such items, but the use case for auto-managed
        # versions is not clear. Likewise, we could make "Set as Default" work,
        # but it is problematic to know what to do if a version is set as
        # default while being downloaded, and then the download fails (which
        # becomes the default afterwards?). Practically, not being able to
        # edit an installation that is being downloaded is probably intuitively
        # normal for most people.
        item = self.listBox.currentItem()
        is_installed_item = bool(item) and isinstance(item.state, InstalledState)
        self.defaultButton.setEnabled(is_installed_item)
        self.editButton.setEnabled(is_installed_item)

    def createItem(self):
        if linux.inside_flatpak():
            QMessageBox.critical(self, app.caption(_("Error")),
                                 _("""You have installed Frescobaldi from Flathub using \
Flatpak. Because Flatpak isolates apps from the rest of the system, it is not possible \
to use custom LilyPond binaries in this configuration. Please either let Frescobaldi auto-install \
a given LilyPond version, using the “Add…” menu, or if you wish to use a custom build, \
install Frescobaldi using a distribution package or from source."""))
            return None
        return InfoItem(InstalledState(lilypondinfo.LilyPondInfo("lilypond")))

    def openEditor(self, item):
        if item is None: # Flatpak case above
            return False

        # Either we're adding a custom version and the item is created in createItem
        # above, or we're editing an existing version because the "Edit" button was clicked,
        # and it's disabled for versions that are being downloaded or failed to download.
        # Either way, we can only edit fully installed versions.
        assert isinstance(item.state, InstalledState)

        dlg = InfoDialog(self, item.state.info)
        # Since we use the command as the way to remember which version is the
        # default, and the user may edit the command here, we need to update
        # it. The check "item in self.items()" is true if this is an existing
        # item that we are updating, with the "Edit" button, but false if it's
        # a fresh item as created by the "Add" button in createItem() above.
        was_default = (item in self.items()
                       and item.state.info.command == self.parentWidget()._defaultCommand)
        if dlg.exec():
            item.state.info = dlg.newInfo()
            if was_default:
                self.parentWidget()._defaultCommand = item.state.info.command
            return True
        return False

    def itemChanged(self, item):
        item.display()
        self.setCurrentItem(item)


    def itemRemoved(self, item):
        if isinstance(item.state, DownloadingState):
            # Cancel a pending download
            item.abortDownload()
        elif isinstance(item.state, InstalledState):
            # Wipe out if auto-managed
            item.state.info.forget()
        # If this version of LilyPond is no longer installed, the menu needs to know
        # about it, to reenable the action.
        self.addButton.menu().updateActions()



class ItemState:
    """Base class for classes holding the state of an InfoItem."""

@dataclass
class DownloadingState(ItemState):
    """Data for an InfoItem whose LilyPond is being downloaded from the network."""
    version_string: str
    download_progress: int  = 0 # percentage

@dataclass
class DownloadErrorState(ItemState):
    """Data for an InfoItem whose LilyPond could not be downloaded."""
    version_string: str

@dataclass
class InstalledState(ItemState):
    """Data for an InfoItem whose LilyPond is fully installed on the system."""
    info: lilypondinfo.LilyPondInfo


_LILYPOND_PACKAGE_URL = (
    "https://gitlab.com/api/v4/projects/lilypond%2Flilypond/packages/"
    + "generic/lilypond/{version_string}/{archive}"
)

class InfoItem(QListWidgetItem):
    """An item in the list of LilyPond versions.

    The `state` attribute holds an instance of `ItemState`.
    """

    # TODO: Currently, download progress is displayed with a percentage in text,
    # but it would be very nice to have it shown as a translucent progress bar
    # overlaid behind the item.

    def __init__(self, state):
        super().__init__()
        self.state = state

    @classmethod
    def fromNetwork(cls, infolist, version):
        """Make an InfoItem that will auto-download and install a given LilyPond version."""
        major, minor, micro = version
        version_string = f"{major}.{minor}.{micro}"
        self = cls(DownloadingState(version_string))

        self.parent = infolist

        if platform.system() == 'Linux':
            archive = f"lilypond-{major}.{minor}.{micro}-linux-x86_64.tar.gz"
            self.archive_format = "gztar"
        elif platform.system() == 'Darwin':
            archive = f"lilypond-{major}.{minor}.{micro}-darwin-x86_64.tar.gz"
            self.archive_format = "gztar"
        elif platform.system() == 'Windows':
            archive = f"lilypond-{major}.{minor}.{micro}-mingw-x86_64.zip"
            self.archive_format = "zip"
        else:
            raise AssertionError

        # Download an archive of LilyPond binaries from GitLab
        archive_url = QUrl(_LILYPOND_PACKAGE_URL.format(
                             version_string=version_string, archive=archive))

        self.reply = _network_manager().get(QNetworkRequest(archive_url))
        self.reply.downloadProgress.connect(self.updateProgress)
        self.reply.finished.connect(self.downloadFinished)
        self.reply.errorOccurred.connect(self.downloadError)

        if platform.system() == "Windows":
            exec_name = "lilypond.exe"
        else:
            exec_name = "lilypond"
        self.executable_path = os.path.join(lilypondinfo.LILYPOND_AUTOINSTALL_DIR,
                                            f"lilypond-{version_string}", "bin",
                                            exec_name)
        return self

    def updateProgress(self, bytes_received, bytes_total):
        if isinstance(self.state, DownloadErrorState):
            # This happens when the download is cancelled with abortDownload();
            # Qt triggers the downloadProgress signal one last time.
            return
        progress = round(bytes_received/bytes_total * 100)
        assert isinstance(self.state, DownloadingState)
        self.state.download_progress = progress
        self.display()

    def downloadFinished(self):
        if isinstance(self.state, DownloadErrorState):
            return # the finished signal is called even in the error case
        assert isinstance(self.state, DownloadingState)
        # Unpack the downloaded archive
        with tempfile.NamedTemporaryFile() as tfile:
            tfile.write(self.reply.readAll())
            shutil.unpack_archive(tfile.name, lilypondinfo.LILYPOND_AUTOINSTALL_DIR,
                                  format=self.archive_format)
        # Switch to "installed" state
        self.state = InstalledState(lilypondinfo.LilyPondInfo(self.executable_path))
        self.display()
        # If this item is still selected, the parent will need to reenable
        # the "Edit" and "Set as Default" buttons.
        self.parent.updateSelection()

    def downloadError(self, code):
        assert isinstance(self.state, DownloadingState)
        self.state = DownloadErrorState(self.state.version_string)
        self.display()

    def abortDownload(self):
        self.reply.abort() # also calls downloadError()

    def display(self):
        if isinstance(self.state, DownloadErrorState):
            icon = "dialog-error"
            text = _("Could not download LilyPond {version}").format(
                       version=self.state.version_string)
        elif isinstance(self.state, DownloadingState):
            icon = "view-refresh"
            text = _("Downloading LilyPond {version}... {progress}%").format(
                      version=self.state.version_string,
                      progress=self.state.download_progress)
        elif isinstance(self.state, InstalledState):
            if self.state.info.version():
                icon = "lilypond-run"
            else:
                icon = "dialog-error"
            text = self.state.info.prettyName()
            default = self.listWidget().parentWidget().parentWidget()._defaultCommand
            if self.state.info.command == default:
                text += " [{}]".format(_("default"))

        self.setIcon(icons.get(icon))
        self.setText(text)


_LILYPOND_RELEASES_API_URL = "https://gitlab.com/api/v4/projects/18695663/releases"

class AddMenu(QMenu):
    """Menu added to the "Add" button of the version list.

    It offers several methods of adding: auto-download, or use a local install.
    There is a set of actions for auto-download and one "Custom" action.
    Initially, the auto-download part displays a greyed-out action while
    downloading the list of available LilyPond versions. When the download
    completes, the normal buttons are added. If the download fails, the
    greyed-out action is replaced with another one to signal the failure.
    """
    def __init__(self, parent):
        super().__init__(parent)
        # Fake menu item as placeholder while the download is in progress.
        self.addAction(_("Downloading LilyPond version list...")).setEnabled(False)
        # Action to add custom LilyPond version anywhere on the file system.
        self.customAction = QAction(_("Button to register a custom LilyPond installation", "Custom..."))
        self.addAction(self.customAction)
        # In most ListEdit's, this is the slot connected to the "Add"
        # button, here's it's connected to the "Custom" button.
        self.customAction.triggered.connect(parent.addClicked)

        # Get the list of available LilyPond versions using the GitLab API.
        url = QUrl(_LILYPOND_RELEASES_API_URL)
        self.reply = _network_manager().get(QNetworkRequest(url))
        self.reply.finished.connect(self.downloadFinished)
        self.reply.errorOccurred.connect(self.downloadError)
        self.hasError = False
        self.downloadSuccessful = False

    def downloadFinished(self):
        if self.hasError:
            return # self.reply.finished is triggered even in case of error

        self.downloadSuccessful = True

        # Decode the JSON data returned by the API
        data = json.loads(bytes(self.reply.readAll()))
        versions = []
        for item in data:
            tag = item["tag_name"]
            # This release dates back to before LilyPond binaries became simple
            # for us to install. (Its tag also uses a different naming convention.)
            if tag == "release/2.22.2-1":
                continue
            # tag has the form v2.x.y
            version = tuple(int(n) for n in tag.lstrip("v").split("."))
            versions.append(version)
        versions.sort(reverse=True) # most recent version first
        self.clear() # rebuild the menu
        self.actions = []
        # Find the latest stable version
        for (major, minor, micro) in versions:
            if minor % 2 == 0:
                latest_stable = (major, minor, micro)
                stable_text = (_("latest stable LilyPond release",
                                 "{major}.{minor}.{micro} (latest &stable)")
                               .format(major=major, minor=minor, micro=micro))
                # Make a dedicated menu item for this version, to make it
                # reachable very easily.
                self.makeVersionAction(latest_stable, stable_text, self)
                versions.remove(latest_stable)
                break
        else: # no `break` reached
            raise AssertionError # at least 2.24 should be in the list
        # Likewise, find the latest unstable version and add a menu item
        for (major, minor, micro) in versions:
            if minor % 2 == 1:
                latest_unstable = (major, minor, micro)
                unstable_text = (_("latest unstable LilyPond release",
                                   "{major}.{minor}.{micro} (latest &unstable)")
                                 .format(major=major, minor=minor, micro=micro))
                self.makeVersionAction(latest_unstable, unstable_text, self)
                versions.remove(latest_unstable)
                break
        else:
            raise AssertionError
        # Add a submenu for all other versions.
        other_text = _("LilyPond versions other than latest stable/unstable",
                       "Other...")
        self.otherMenu = self.addMenu(other_text)
        for version in versions:
            major, minor, micro = version
            text = f"{major}.{minor}.{micro}"
            self.makeVersionAction(version, text, self.otherMenu)

        # Add the "Custom" action that we already had.
        self.addAction(self.customAction)

        # Update which actions are enabled
        self.updateActions()

    def makeVersionAction(self, version, text, parent):
        action = QAction(text, parent)
        parent.addAction(action)
        # Connect the action
        action.triggered.connect(self.autoDownload(version))
        self.actions.append((version, action))

    def downloadError(self, code):
        self.hasError = True
        self.clear() # rebuild the menu
        self.addAction(_("Could not download LilyPond version list")).setEnabled(False)
        self.addAction(self.customAction)

    def autoDownload(self, version):
        """Return a function that downloads a certain version, for connecting to menu actions."""
        def download_inner():
            item = InfoItem.fromNetwork(self.parent(), version)
            self.parent().addItem(item)
            self.updateActions()
        return download_inner

    def updateActions(self):
        """
        Disable a menu action if there is already an auto-managed LilyPond installation for the same version.

        Prevents the user from doing something silly and spares us error
        handling downstream to cope with duplicate LilyPondInfo's for the same
        installation (e.g., when removing them).
        """
        if not self.downloadSuccessful:
            # We aren't done downloading the list of versions yet (or there was
            # an error), so we don't have the version actions and we needn't care
            # about this.
            return

        disabled_versions = set()
        for item in self.parent().items():
            if isinstance(item.state, InstalledState) and item.state.info.isAutoManaged:
                disabled_versions.add(item.state.info.versionString())
            elif isinstance(item.state, DownloadingState):
                disabled_versions.add(item.state.version_string)

        for (major, minor, micro), action in self.actions:
            enable = (f"{major}.{minor}.{micro}" not in disabled_versions)
            action.setEnabled(enable)


class InfoDialog(QDialog):
    def __init__(self, parent, info):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowType.WindowModal)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)

        self.tab = QTabWidget()
        tab_general = QWidget()
        tab_toolcommands = QWidget()
        self.tab.addTab(tab_general, "")
        self.tab.addTab(tab_toolcommands, "")

        # general tab
        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        tab_general.setLayout(vbox)

        hbox = QHBoxLayout()
        self.lilyname = QLineEdit()
        self.lilyname.setText(info.name)
        self.lilynameLabel = l = QLabel()
        l.setBuddy(self.lilyname)
        hbox.addWidget(l)
        hbox.addWidget(self.lilyname)
        vbox.addLayout(hbox)

        # For auto-managed installation, don't show the installation
        # path to the user or let them edit it.
        self.haveCommandEdit = not info.isAutoManaged
        if self.haveCommandEdit:
            self.lilypond = widgets.urlrequester.UrlRequester()
            self.lilypond.setFileMode(QFileDialog.ExistingFile)
            self.lilypond.setPath(info.command)
            self.lilypond.lineEdit.setFocus()
            self.lilypondLabel = l = QLabel()
            l.setBuddy(self.lilypond)
            vbox.addWidget(l)
            vbox.addWidget(self.lilypond)
        else:
            self.lilypondCommand = info.command

        self.autoVersionIncluded = QCheckBox()
        self.autoVersionIncluded.setChecked(info.autoVersionIncluded)
        vbox.addWidget(self.autoVersionIncluded)
        vbox.addStretch(1)

        # toolcommands tab
        grid = QGridLayout()
        grid.setSpacing(4)
        tab_toolcommands.setLayout(grid)

        self.ly_tool_widgets = {}
        row = 0
        for name, gui in self.toolnames():
            w = QLineEdit()
            l = QLabel()
            l.setBuddy(w)
            grid.addWidget(l, row, 0)
            grid.addWidget(w, row, 1)
            row += 1
            self.ly_tool_widgets[name] = (l, w)
            self.ly_tool_widgets[name][1].setText(info.ly_tool(name))

        layout.addWidget(self.tab)
        layout.addWidget(widgets.Separator())
        b = self.buttons = QDialogButtonBox(self)
        layout.addWidget(b)

        b.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "prefs_lilypond")
        app.translateUI(self)
        qutil.saveDialogSize(self, "/preferences/lilypond/lilypondinfo/dialog/size")

    def toolnames(self):
        """Yield tuples (name, GUI name) for the sub tools we allow to be configured."""
        yield 'convert-ly', _("Convert-ly:")
        yield 'lilypond-book', _("LilyPond-book:")
        yield 'midi2ly', _("Midi2ly:")
        yield 'musicxml2ly', _("MusicXML2ly:")
        yield 'abc2ly', _("ABC2ly:")

    def translateUI(self):
        self.setWindowTitle(app.caption(_("LilyPond")))
        self.lilynameLabel.setText(_("Label:"))
        self.lilynameLabel.setToolTip(_("How this version of LilyPond will be displayed."))
        if self.haveCommandEdit:
            self.lilypondLabel.setText(_("LilyPond Command:"))
            self.lilypond.lineEdit.setToolTip(_("Name or full path of the LilyPond program."))
        self.autoVersionIncluded.setText(_("Include in automatic version selection"))
        self.tab.setTabText(0, _("General"))
        self.tab.setTabText(1, _("Tool Commands"))
        for name, gui in self.toolnames():
            self.ly_tool_widgets[name][0].setText(gui)

    def newInfo(self):
        """Returns a new LilyPondInfo instance for our settings."""
        if not self.haveCommandEdit:
            info = lilypondinfo.LilyPondInfo(self.lilypondCommand)
        elif platform.system() == "Darwin" and self.lilypond.path().endswith('.app'):
            info = lilypondinfo.LilyPondInfo(
                self.lilypond.path() + '/Contents/Resources/bin/lilypond')
        else:
            info = lilypondinfo.LilyPondInfo(self.lilypond.path())
        if self.lilyname.text() and not self.lilyname.text().isspace():
            info.name = self.lilyname.text()
        info.autoVersionIncluded = self.autoVersionIncluded.isChecked()
        for name, gui in self.toolnames():
            info.set_ly_tool(name, self.ly_tool_widgets[name][1].text())
        return info


class Running(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.saveDocument = QCheckBox(clicked=self.changed)
        self.deleteFiles = QCheckBox(clicked=self.changed)
        self.embedSourceCode = QCheckBox(clicked=self.changed)
        self.noTranslation = QCheckBox(clicked=self.changed)
        self.includeLabel = QLabel()
        self.include = widgets.listedit.FilePathEdit()
        self.include.listBox.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove)
        self.include.changed.connect(self.changed)
        layout.addWidget(self.saveDocument)
        layout.addWidget(self.deleteFiles)
        layout.addWidget(self.embedSourceCode)
        layout.addWidget(self.noTranslation)
        layout.addWidget(self.includeLabel)
        layout.addWidget(self.include)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Running LilyPond"))
        self.saveDocument.setText(_("Save document if possible"))
        self.saveDocument.setToolTip(_(
            "If checked, the document is saved when it is local and modified.\n"
            "Otherwise a temporary file is used to run LilyPond."))
        self.deleteFiles.setText(_("Delete intermediate output files"))
        self.deleteFiles.setToolTip(_(
            "If checked, LilyPond will delete intermediate PostScript files."))
        self.embedSourceCode.setText(_("Embed Source Code files in publish mode"))
        self.embedSourceCode.setToolTip(_(
            "If checked, the LilyPond source files will be embedded in the PDF\n"
            "when LilyPond is started in publish mode."))
        self.noTranslation.setText(_("Run LilyPond with English messages"))
        self.noTranslation.setToolTip(_(
            "If checked, LilyPond's output messages will be in English.\n"
            "This can be useful for bug reports."))
        self.includeLabel.setText(_("LilyPond include path:"))

    def loadSettings(self):
        s = settings()
        self.saveDocument.setChecked(s.value("save_on_run", False, bool))
        self.deleteFiles.setChecked(s.value("delete_intermediate_files", True, bool))
        self.embedSourceCode.setChecked(s.value("embed_source_code", False, bool))
        self.noTranslation.setChecked(s.value("no_translation", False, bool))
        include_path = qsettings.get_string_list(s, "include_path")
        self.include.setValue(include_path)

    def saveSettings(self):
        s = settings()
        s.setValue("save_on_run", self.saveDocument.isChecked())
        s.setValue("delete_intermediate_files", self.deleteFiles.isChecked())
        s.setValue("embed_source_code", self.embedSourceCode.isChecked())
        s.setValue("no_translation", self.noTranslation.isChecked())
        s.setValue("include_path", self.include.value())


class Target(preferences.Group):
    def __init__(self, page):
        super().__init__(page)

        layout = QGridLayout()
        self.setLayout(layout)

        self.targetPDF = QRadioButton(toggled=page.changed)
        self.targetSVG = QRadioButton(toggled=page.changed)
        self.openDefaultView = QCheckBox(clicked=page.changed)

        layout.addWidget(self.targetPDF, 0, 0)
        layout.addWidget(self.targetSVG, 0, 1)
        layout.addWidget(self.openDefaultView, 1, 0, 1, 5)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Default output format"))
        self.targetPDF.setText(_("PDF"))
        self.targetPDF.setToolTip(_(
            "Create PDF (Portable Document Format) documents by default."))
        self.targetSVG.setText(_("SVG"))
        self.targetSVG.setToolTip(_(
            "Create SVG (Scalable Vector Graphics) documents by default."))
        self.openDefaultView.setText(_("Open default viewer after successful compile"))
        self.openDefaultView.setToolTip(_(
            "Shows the PDF or SVG music view when a compile job finishes "
            "successfully."))

    def loadSettings(self):
        s = settings()
        target = s.value("default_output_target", "pdf", str)
        if target == "svg":
            self.targetSVG.setChecked(True)
            self.targetPDF.setChecked(False)
        else:
            self.targetSVG.setChecked(False)
            self.targetPDF.setChecked(True)
        self.openDefaultView.setChecked(s.value("open_default_view", True, bool))

    def saveSettings(self):
        s = settings()
        if self.targetSVG.isChecked():
            target = "svg"
        else:
            target = "pdf"
        s.setValue("default_output_target", target)
        s.setValue("open_default_view", self.openDefaultView.isChecked())
