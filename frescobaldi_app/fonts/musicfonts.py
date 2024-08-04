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
Manage lists of music/notation fonts, providing tools to install or
uninstall to/from a LilyPond installation."
"""


import os
import re
from enum import Enum
from shutil import copyfile
from pathlib import Path

from PyQt6.QtCore import (
    QObject,
    QSettings,
    Qt
)
from PyQt6.QtGui import (
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

import app
import fonts
from . import textfonts


class MusicFontsWidget(QWidget):
    """Display list of installed music fonts,
    show font preview score, install/remove fonts."""

    def __init__(self, parent):
        super().__init__(parent)
        s = QSettings()
        s.beginGroup('music-fonts')
        self._auto_install = s.value('auto-install', True, bool)
        self._font_repo = fonts.music_fonts_repo()

        self.music_fonts = parent.available_fonts.music_fonts()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.button_download = bd = QPushButton(self)
        # TODO: This hasn't been implemented yet
        bd.setEnabled(False)
        self.button_auto_install = bai = QPushButton(self)
        self.button_install = bi = QPushButton(self)
        self.button_remove = br = QPushButton(self)
        bai.setEnabled(bool(self._font_repo and not self._auto_install))
        br.setEnabled(False)
        self.button_download.clicked.connect(self.download_music_fonts)
        self.button_auto_install.clicked.connect(self.install_button_clicked)
        self.button_install.clicked.connect(self.install_button_clicked)
        self.button_remove.clicked.connect(self.remove_music_font)
        bl = QHBoxLayout()
        bl.addStretch()
        bl.addWidget(bai)
        bl.addWidget(bi)
        bl.addWidget(bd)
        bl.addWidget(br)
        layout.addLayout(bl)

        # If conditions for automatic install are met do so
        if self._font_repo and self._auto_install:
            self.install_music_fonts('auto')

        self.tree_view = tv = QTreeView(self)
        tv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tv.setSelectionMode(QAbstractItemView.SingleSelection)
        tv.setSelectionBehavior(QAbstractItemView.SelectRows)
        tv.setModel(self.music_fonts.item_model())
        tv.selectionModel().selectionChanged.connect(
            self.music_fonts_selection_changed
        )
        layout.addWidget(tv)

        app.translateUI(self)

    def translateUI(self):
        self.button_remove.setText(_("Remove..."))
        self.button_remove.setToolTip(_("Remove selected music font"))
        self.button_download.setText(_("Download..."))
        self.button_download.setToolTip(_(
            "Download music fonts from a repository on Github.\n"
            "NOTE: Not implemented yet."
        ))
        self.button_install.setText(_("Install..."))
        self.button_install.setToolTip(_(
            "Link fonts from a directory to the current LilyPond installation"
        ))
        self.button_auto_install.setText(_("Install (repo)"))
        self.button_auto_install.setToolTip(_(
            "Link fonts from the global music font repository\n"
            "to the current LilyPond installation."
        ))

    def download_music_fonts(self):
        """Opens a dialog to download and install music fonts from Github."""
        # TODO: implement
        # from . import download
        # ...
        pass

    def install_button_clicked(self):
        mode = 'auto' if self.sender() == self.button_auto_install else 'dlg'
        self.install_music_fonts(mode)

    def install_music_fonts(self, mode):
        """'Install' music fonts from a directory (structure) by
        linking fonts into the LilyPond installation's font
        directories (otf and svg)."""

        if mode == 'auto':
            # Use the global fonts repository
            repo = fonts.music_fonts_repo()
        else:
            dlg = QFileDialog(self)
            dlg.setFileMode(QFileDialog.Directory)
            if not dlg.exec():
                return
            repo = MusicFontRepo(dlg.selectedFiles()[0])

        installed = self.music_fonts
        repo.flag_for_install(installed)

        try:
            repo.install_flagged(installed)
            if mode == 'auto':
                self.button_auto_install.setEnabled(False)
        except MusicFontPermissionException as e:
            msg_box = QMessageBox()
            msg_box.setText(_("Fonts could not be installed!"))
            msg_box.setInformativeText(_(
                "Installing fonts in the LilyPond installation "
                "appears to require administrator privileges on "
                "your system and can unfortunately not be handled "
                "by Frescobaldi."
            ))
            msg_box.setDetailedText(f"{e}")
            msg_box.exec()

    def music_font_family(self):
        try:
            family_name = (
                self.tree_view.selectionModel().selectedIndexes()[0].data())
        except IndexError:
            family_name = 'emmentaler'
        return family_name

    def music_fonts_selection_changed(self, new, old):
        """Show a new score example with the selected music font"""
        has_font = self.tree_view.selectionModel().hasSelection()
        if has_font:
            music_name = self.music_font_family()
            brace_name = (
                music_name
                if self.music_fonts.family(music_name).has_brace('otf')
                else 'emmentaler'
            )
            self.window().select_font('music', music_name)
            self.window().select_font('brace', brace_name)
        else:
            self.window().select_font('emmentaler')
            self.window().select_font('emmentaler')
        self.window().invalidate_command()
        self.button_remove.setEnabled(has_font)

    def remove_music_font(self):
        """Remove one or more font family/ies from the LilyPond installation.
        Works only for *links*, not for *files*."""
        text = ''
        informative_text = ''
        detailed_text = ''
        try:
            indexes = self.tree_view.selectionModel().selectedRows()
            self.music_fonts.remove(indexes)
            self.button_auto_install.setEnabled(bool(self._font_repo))
        except MusicFontFileRemoveException as e:
            text = _("Font family could not be removed!")
            informative_text = _(
                "To avoid persistent damage Frescobaldi only supports "
                + "removing music fonts that are linked into a LilyPond "
                + "installation. The font being removed includes real "
                + "files and can therefore not be removed directly.")
            detailed_text = f"{e}"
        if text:
            from PyQt6.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setText(text)
            msg_box.setInformativeText(informative_text)
            msg_box.setDetailedText(detailed_text)
            msg_box.exec()


class MusicFontException(Exception):
    pass


class MusicFontPermissionException(MusicFontException):
    pass


class MusicFontFileRemoveException(MusicFontException):
    pass


class MusicFontStatus(Enum):
    """Status value enumeration for registered font files.
    Actually the 'MISSING' and 'BROKEN' values should never
    occur since this is already checked upon the creation
    of any font object."""
    FILE = 0
    MISSING_FILE = 1
    LINK = 2
    BROKEN_LINK = 3
    MISSING = 4


class MusicFontFile(QObject):
    """Represents a font file within a font family."""

    def __init__(self, file):
        self.file = file
        self.status = None
        self.install = False


class MusicFontFamily(QObject):
    """Represents a single music font family.
    Keep track of completeness status and add files to the family.
    Other classes make use of some class functions and variables."""

    # List of sizes expected for a complete music font
    sizes_list = ['11', '13', '14', '16', '18', '20', '23', '26']
    # Regular expression to determine a LilyPond music font
    font_re = re.compile(
        r'(?P<family>.*)-(?P<size>brace|\d\d)\.(?P<type>otf|svg|woff)$')

    @classmethod
    def parse_filename(cls, file):
        """Check if a given filename represents a LilyPond music font.
        Returns a match object with three named groups ('family', 'size',
        'type') or None if no match is found."""
        return MusicFontFamily.font_re.match(os.path.basename(file))

    @classmethod
    def check_file(cls, file):
        """Test if a file is a LilyPond music font.
        Returns three family, type, size if successful or raises a
        MusicFontException otherwise."""
        if not os.path.exists(file):
            raise MusicFontException(
                f'Not an existing file or link: {file}')
        font = cls.parse_filename(file)
        if not font:
            raise MusicFontException(
                f'File {file} does not appear to be a valid font file')
        return font['family'], font['type'], font['size']

    def __init__(self, file=None):
        self.family = None
        self._files = {
            'otf': {},
            'svg': {},
            'woff': {}
        }
        if file:
            self.add_file(file)

    def __getitem__(self, key):
        return self._files[key]

    def add(self, type, size, file):
        """Add a file if it has already been parsed to type/size.
        Existing entries are silently overwritten."""
        self._files[type][size] = MusicFontFile(file)

    def add_file(self, file):
        """Add a given file to the font family if it is a valid
        music font and if it does not belong to a different font
        family."""
        family, type, size = MusicFontFamily.check_file(file)
        if self.family and self.family != family:
            raise MusicFontException(
                'File {name} does not belong to font family {family}'.format(
                    name=file, family=self.family))
        if not self.family:
            self.family = family
        self.add(type, size, file)

    def flag_all_for_install(self):
        for type in self._files:
            for size in self._files[type]:
                self._files[type][size].install = True

    def flag_for_install(self, target_family):
        for type in self._files:
            for size in self._files[type]:
                file = self._files[type][size]
                if (
                    self.status(type, size)
                    in [MusicFontStatus.FILE, MusicFontStatus.LINK]
                    and target_family.status(type, size)
                    not in [MusicFontStatus.FILE, MusicFontStatus.LINK]
                ):
                    file.install = True

    def has_brace(self, type):
        return 'brace' in self._files[type].keys()

    def is_complete(self, type=None):
        """Determines if the given type is complete with all sizes
        and a brace font. If no type is given *all* types are checked."""
        if type:
            return self.has_brace(type) and not self.missing_sizes(type)
        else:
            return (
                self.is_complete('otf')
                and self.is_complete('svg')
                and self.is_complete('woff')
            )

    def missing_sizes(self, type):
        """Returns a list of size strings representing missing
        font sizes for the given type. For a complete font this
        will be an empty list, which is checked in is_complete()
        for example."""
        return (
            [size for size in MusicFontFamily.sizes_list
                if size not in self.sizes(type)]
        )

    def remove(self, type, size):
        """Remove a given type/size combination."""
        self._files[type].pop(size, None)

    def sizes(self, type):
        """Returns a string list with the installed sizes for a given type."""
        return sorted(self._files[type].keys())

    def status(self, type, size):
        """Returns the status for a given type/size combination."""
        if size not in self._files[type].keys():
            return MusicFontStatus.MISSING

        font = self._files[type][size]
        if font.status is None:
            from pathlib import Path
            file = Path(font.file)
            if file.is_symlink():
                if file.exists():
                    font.status = MusicFontStatus.LINK
                else:
                    font.status = MusicFontStatus.BROKEN_LINK
            elif file.is_file():
                font.status = MusicFontStatus.FILE
            else:
                font.status = MusicFontStatus.MISSING_FILE
        return font.status

    def walk(self):
        """Return entries for all registered fonts."""
        for type in self._files:
            for size in self._files[type]:
                yield type, size, self._files[type][size]


class AbstractMusicFontList(QObject):
    """Abstract class managing a list of music fonts."""

    def __init__(self):
        self._item_model = None
        self.clear()

    def add_file(self, file):
        """Add the given file to a MusicFontFamily.
        If the file doesn't point to a music font a MusicFontException
        will simply be forwarded, so a caller must handle that.
        If the font family is already present the file is added to it
        (silently overwriting an existing type/size combination),
        otherwise the MusicFont object is created."""
        family, type, size = MusicFontFamily.check_file(file)
        if family not in self._families.keys():
            self._families[family] = MusicFontFamily(file)
        else:
            self._families[family].add(type, size, file)

    def add_family(self, family):
        """Add a MusicFontFamily object that is already composed.
        An existing family with the same name will get overwritten."""
        family_name = family.family
        self._families[family_name] = family

    def clear(self):
        """Reset the list of fonts/files."""
        self._families = {}
        if self._item_model:
            self._item_model.reset()

    def families(self):
        """Return a sorted list with all family names."""
        return sorted(self._families.keys())

    def family(self, name):
        """Returns a MusicFont for the given family name,
        or None if it isn't present yet."""
        return self._families.get(name, None)

    def add_tree(self, root):
        """Walk through a given directory tree and add all found
        music fonts to the list."""
        for dir, dirs, files in os.walk(root):
            for file in files:
                try:
                    self.add_file(os.path.join(dir, file))
                except Exception:
                    # file is not a music font, ignore
                    pass

    def item_model(self):
        """Return the (cached) item model."""
        if not self._item_model:
            self._item_model = MusicFontsModel()
            self._item_model.populate(self)
        return self._item_model

    def walk(self):
        """Generator to produce *all* font files for the repository."""
        for family_name in self._families:
            family = self.family(family_name)
            for type in family._files:
                for size in family._files[type]:
                    yield (
                        family, family_name, type, size,
                        family._files[type][size]
                    )


class MusicFontRepo(AbstractMusicFontList):
    """Represents a repository of music fonts, typically within a
    single directory tree."""

    def __init__(self, root):
        super().__init__()
        self._root = root
        self.installable_fonts = AbstractMusicFontList()
        self.add_tree(root)

    def flag_for_install(self, installed):
        """Determine which fonts can be installed."""
        self.installable_fonts.clear()
        for family_name in self._families:
            repo_family = self.family(family_name)
            target_family = installed.family(family_name)
            if not target_family:
                repo_family.flag_all_for_install()
            else:
                repo_family.flag_for_install(target_family)
        for _, _, _, _, font in self.walk():
            if font.install:
                self.installable_fonts.add_file(font.file)

    def install_flagged(self, target):
        """Install all font files in the target repo that have
        been flagged for installation."""
        for _, _, type, _, font in self.installable_fonts.walk():
            target.install(type, font.file)

        target.item_model().populate(target)

    def root(self):
        return self._root


class InstalledMusicFonts(AbstractMusicFontList):
    """Manages the music fonts installed in a given LilyPond
    installation. Provides means to add/remove fonts if the
    file system permissions allow to do so."""

    def __init__(self, lilypond_info):
        super().__init__()
        self.lilypond_info = lilypond_info
        self.font_root = os.path.join(lilypond_info.datadir(), 'fonts')
        self.add_tree(self.font_root)

    def font_dir(self, type):
        """Return the font directory for the given type.
        SVG and WOFF share a directory."""
        last_segment = 'otf' if type == 'otf' else 'svg'
        return os.path.join(self.font_root, last_segment)

    def install(self, type, font_file, copy=False):
        """Install a font file in the type's directory.
        Raise an exception if this fails (typically
        lacking permissions)."""
        target = os.path.join(
            self.font_root,
            self.font_dir(type),
            os.path.basename(font_file)
        )
        if copy:
            try:
                copyfile(font_file, target)
            except OSError as e:
                raise MusicFontPermissionException(
                    _("Font installation failed:") + f"\n{e}")
        else:
            try:
                os.symlink(font_file, target)
            except NotImplementedError:
                # On Windows prior to Vista symlinks are not supported
                self.install(type, font_file, copy=True)
            except OSError as e:
                raise MusicFontPermissionException(
                    _("Font installation failed:") + f"\n{e}")
        self.add_file(target)

    def remove(self, indexes):
        """Remove one or more font family/ies from the LilyPond installation.
        If any of the fonts includes any real files (as opposed to links)
        abort without removing *anything* and raise an exception."""
        for index in indexes:
            family_name = index.data()
            family = self.family(family_name)
            links = []
            files = []
            for type, size, font in family.walk():
                file = Path(font.file)
                if file.is_symlink():
                    links.append(file)
                else:
                    files.append(str(file))
            if files:
                raise MusicFontFileRemoveException(_("\n".join(files)))
            try:
                for link in links:
                    link.unlink()
            except OSError as e:
                raise MusicFontPermissionException(
                    _("Font removal failed:") + f"\n{e}")
            self._families.pop(family_name, None)
        self.item_model().populate(self)


class MusicFontsModel(QStandardItemModel):
    """Data model to maintain the list of available music fonts."""

    def populate(self, fonts):
        """Populate the data model from the fonts dictionary."""

        def check_type(font, type):
            size_result = QStandardItem()
            sizes = font.missing_sizes(type)
            if sizes:
                if len(sizes) == 8:
                    size_result.setCheckState(False)
                else:
                    size_result.setCheckState(Qt.PartiallyChecked)
                    size_result.setText(_("Missing:") + " {}".format(
                        ", ".join(sizes)))
            else:
                size_result.setCheckState(Qt.Checked)

            has_brace = Qt.Checked if font.has_brace(type) else Qt.Unchecked
            brace_result = QStandardItem()
            brace_result.setCheckState(has_brace)
            return [size_result, brace_result]

        self.reset()
        textfonts._installed_notation_fonts = installed = []
        for family_name in fonts.families():
            installed.append(family_name.lower())
            font = fonts.family(family_name)
            result = [QStandardItem(family_name)]
            result.extend(check_type(font, 'otf'))
            result.extend(check_type(font, 'svg'))
            result.extend(check_type(font, 'woff'))
            self.invisibleRootItem().appendRow(result)

    def reset(self):
        self.clear()
        self.setColumnCount(7)
        self.setHeaderData(0, Qt.Orientation.Horizontal, _("Font"))
        self.setHeaderData(1, Qt.Orientation.Horizontal, _("OpenType"))
        self.setHeaderData(2, Qt.Orientation.Horizontal, _("(Brace)"))
        self.setHeaderData(3, Qt.Orientation.Horizontal, _("SVG"))
        self.setHeaderData(4, Qt.Orientation.Horizontal, _("(Brace)"))
        self.setHeaderData(5, Qt.Orientation.Horizontal, _("WOFF"))
        self.setHeaderData(6, Qt.Orientation.Horizontal, _("(Brace)"))
