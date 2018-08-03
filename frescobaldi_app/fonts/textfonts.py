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

import os
import re

from PyQt5.QtCore import (
    QObject,
    QRegExp,
    QSortFilterProxyModel,
    Qt,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import(
    QFont,
    QFontDatabase,
    QStandardItem,
    QStandardItemModel,
)

import app
import job
import codecs
import signals
from widgets.lineedit import LineEdit


class TextFontsWidget(QWidget):
    """Display installed text fonts available for a given LilyPond version."""
    # Store the filter expression over the object's lifetime
    filter_re = ''

    def __init__(self, available_fonts, parent=None):
        super(TextFontsWidget, self).__init__(parent)
        self.lilypond_info = available_fonts.lilypond_info
        self.fonts = available_fonts.text_fonts()

        self.status_label = QLabel(self)
        self.tree_view = tv = QTreeView(self)
        tv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.filter_edit = LineEdit(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.tree_view)
        layout.addWidget(self.filter_edit)
        self.setLayout(layout)

        self.tree_view.setModel(self.fonts.model().proxy())
        self.filter_edit.textChanged.connect(self.update_filter)
        self.filter = QRegExp('', Qt.CaseInsensitive)
        app.translateUI(self)


    def translateUI(self):
        self.filter_edit.setPlaceholderText(
            _("Filter results (type any part of the font family name. "
            + "Regular Expressions supported.)"))

    def display_count(self):
        self.status_label.setText(
            _("{count} font families detected by {version}").format(
                count=self.tree_view.model().rowCount(),
                version=self.lilypond_info.prettyName()))

    def display_waiting(self):
        self.status_label.setText(_("Running LilyPond to list fonts ..."))

    def refresh_filter_edit(self):
        self.filter_edit.setText(TextFontsWidget.filter_re)

    def tree_model(self):
        return self.tree_view.model()

    def update_filter(self):
        """Filter font results"""
        TextFontsWidget.filter_re = re = self.filter_edit.text()
        self.filter.setPattern(re)
        self.fonts.model().proxy().setFilterRegExp(self.filter)


class MiscFontsInfoWidget(QWidget):
    """Display miscellaneous info about Fontconfig context."""
    def __init__(self, available_fonts, parent=None):
        super(MiscFontsInfoWidget, self).__init__(parent)
        self.tree_view = tv = QTreeView(self)
        tv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tv.setHeaderHidden(True)
        self.status_label = QLabel(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.tree_view)
        self.setLayout(layout)
        self.tree_view.setModel(available_fonts.text_fonts().misc_model())

        app.translateUI(self)

    def translateUI(self):
        self.status_label.setText(_("Fontconfig data:"))


class FontFilterProxyModel(QSortFilterProxyModel):
    """Custom proxy model that ignores child elements in filtering"""

    def filterAcceptsRow(self, row, parent):
        if parent.isValid():
            return True
        else:
            return super(FontFilterProxyModel, self).filterAcceptsRow(row, parent)


class FontTreeModel(QStandardItemModel):
    """Custom Item Model holding information about available
    fonts. Builds the tree upon first use and caches the results
    until invalidated.
    Uses a custom filter mechanism to never filter child elements."""
    def __init__(self, parent=None):
        super(FontTreeModel, self).__init__(parent)
        self._proxy = FontFilterProxyModel(self)
        self._proxy.setSourceModel(self)

    def populate(self, families):
        """Populate the data model to be displayed in the results"""

        def sample(sub_family, style):
            """Produce a styled font sample for a given weight/style.
            This is not completely reliable since the style aliases
            returned by LilyPond are somewhat inconsistent and don't
            always match a font style that PyQt can get."""
            item = QStandardItem(
                _('The quick brown fox jumps over the lazy dog'))
            font = QFont(sub_family)
            font.setStyleName(style)
            item.setFont(font)
            return item

        self.reset()
        family_names = sorted(families.keys(), key=lambda s: s.lower())
        root = self.invisibleRootItem()
        for name in family_names:
            family = families[name]
            sub_families = []
            for sub_family_name in sorted(family.keys()):
                sub_family = family[sub_family_name]
                if len(sub_family) == 1:
                    # Subfamily has only one entry, create single line
                    style = sub_family[0]
                    sub_families.append(
                        [QStandardItem('{} ({})'.format(
                            sub_family_name, style)),
                        sample(sub_family_name, style)])
                else:
                    # Subfamily has multiple entries, create
                    # container plus styled line for each style
                    sub_family_item = QStandardItem(sub_family_name)
                    sub_families.append(sub_family_item)
                    for style in sorted(sub_family):
                        sub_family_item.appendRow(
                            [QStandardItem(style),
                            sample(sub_family_name, style)])

            # Pull up subfamily as top-level entry if
            # - there is only one subfamily and
            # - it is a subfamily item with children
            if (len(sub_families) == 1
                and isinstance(sub_families[0], QStandardItem)
            ):
                root.appendRow(sub_families[0])
            else:
                family_item = QStandardItem(name)
                root.appendRow(family_item)
                for f in sub_families:
                    family_item.appendRow(f)

    def proxy(self):
        return self._proxy

    def reset(self):
        self.clear()
        self.setColumnCount(2)
        self.setHeaderData(0, Qt.Horizontal, _("Font"))
        self.setHeaderData(1, Qt.Horizontal, _("Sample"))


class MiscTreeModel(QStandardItemModel):
    """Custom tree model for miscellaneous fontconfig information.
    This model stores three top-level elements as individual fields
    and only then appends them to the root. So they are optionally
    available independently."""
    def __init__(self, parent=None):
        super(MiscTreeModel, self).__init__(parent)
        self.reset()

    def populate(self, config_files, config_dirs, font_dirs):
        """Sort entries and construct the overall model."""
        self.reset()
        for file in sorted(config_files, key=lambda s: s.lower()):
            self.config_files.appendRow(QStandardItem(file))
        for config_dir in sorted(config_dirs, key=lambda s: s.lower()):
            self.config_dirs.appendRow(QStandardItem(config_dir))
        for font_dir in sorted(font_dirs, key=lambda s: s.lower()):
            self.font_dirs.appendRow(QStandardItem(font_dir))

        misc_root = self.invisibleRootItem()
        misc_root.appendRow(self.config_files)
        misc_root.appendRow(self.config_dirs)
        misc_root.appendRow(self.font_dirs)

    def reset(self):
        self.clear()
        self.config_files = QStandardItem(_("Configuration Files"))
        self.config_dirs = QStandardItem(_("Configuration Directories"))
        self.font_dirs = QStandardItem(_("Searched Font Directories"))


class TextFonts(QObject):
    """Provide information about available text fonts. These are exactly the
    fonts that can be seen by LilyPond.
    This is only produced upon request but then stored permanently during the
    program's runtime.
    load_fonts() will run LilyPond to determine the list of fonts, optionally
    reporting to a log.Log widget if given.
    Since this is an asynchronous process GUI elements that want to use the
    results have to connect to the 'loaded' signal which is emitted after
    LilyPond has completed and the results been parsed.

    A Fonts() object is immediately available as fonts.available_fonts, and
    its is_loaded member can be requested to test if fonts have already been
    loaded.
    """

    loaded = signals.Signal()

    def __init__(self, lilypond_info):
        super(TextFonts, self).__init__()
        self.lilypond_info = lilypond_info
        self._tree_model = FontTreeModel(self)
        self._misc_model = MiscTreeModel(self)
        self.reset()
        self.job = None

    def reset(self):
        self._log = []
        self._tree_model.reset()
        self._misc_model.reset()
        # needs to be reset for the LilyPond-dependent fonts
        self.font_db = QFontDatabase()

        self._is_loaded = False

    def log(self):
        return self._log

    def acknowledge_lily_fonts(self):
        """Add the OpenType fonts in LilyPond's font directory
        to Qt's font database. This should be relevant (untested)
        when the fonts are not additionally installed as system fonts."""
        font_dir = os.path.join(self.lilypond_info.datadir(), 'fonts', 'otf')
        for lily_font in os.listdir(font_dir):
            self.font_db.addApplicationFont(
                os.path.join(font_dir, lily_font)
            )

    def add_style_to_family(self, families, family_name, input):
        """Parse a font face definition provided by LilyPond.
        There is some guesswork involved since there may be
        discrepancies between the fonts/styles reported by
        LilyPond and those available in QFontDatabase.
        To discuss this the function is heavily commented.
        See also
        http://lists.gnu.org/archive/html/lilypond-user/2018-07/msg00338.html
        """

        def un_camel(style):
            """
            Try to 'fix' a class of errors when LilyPond reports
            e.g. 'BoldItalic' instead of 'Bold Italic'.
            It is unclear if this actually fixes the source of the
            issue or just one arbitrary example.
            """
            # The following regular expression would be a 'proper'
            # un-camel-ing, but this seems not to be relevant.
            #un_cameled = re.sub('([^ ])([A-Z][a-z])', r'\1 \2', style)
            #return re.sub('([A-Za-z])([0-9])', r'\1 \2', un_cameled)
            return (
                "Bold Italic" if style == "BoldItalic"
                else style
            )

        if not family_name in families.keys():
            families[family_name] = {}
        family = families[family_name]
        input = input.strip().split(':')
        # This is a safeguard against improper entries
        if len(input) == 2:
            # The first segment has always one or two entries:
            # - The font family name
            # - The font subfamily name if it differs from the base name.
            # Therefore the series is always the *last* entry in the list.
            # We "unescape" hyphens because this escape is not necessary
            # for our purposes.
            sub_family = input[0].split(',')[-1].replace('\\-', '-')
            if not sub_family in family.keys():
                family[sub_family] = []
            qt_styles = self.font_db.styles(sub_family)
            lily_styles = input[1][6:].split(',')
            match = ''
            if not qt_styles:
                # In some cases Qt does *not* report available styles.
                # In these cases it seems correct to use the style reported
                # by LilyPond. In very rare cases it seems possible that
                # LilyPond reports multiple styles for such fonts, and for now
                # we have to simply ignore these cases so we take the first
                # or single style.
                match = un_camel(lily_styles[0])
            else:
                # Match LilyPond's reported styles with those reported by Qt.
                # We need to un-camel the LilyPond-reported style name, but
                # this may not be a final fix (see comment to un_camel()).
                # If no match is found we simply hope that the style
                # reported by LilyPond will do.
                for style in lily_styles:
                    style = un_camel(style)
                    if style in qt_styles:
                        match = style
                        break
                if not match:
                    match = un_camel(lily_styles[0])
            if not match in family[sub_family]:
                family[sub_family].append(match)
        else:
            pass
            # TODO: issue a warning?
            # In my examples *some* fonts were parsed improperly
            # and therefore skipped.
            # I *think* this happens at the stage of splitting the
            # LilyPond log into individual lines.
            #print("Error when parsing font entry:")
            #print(name)
            #print(input)

    def flatten_log(self):
        """Flatten job history into flat string list."""
        for line in self.job.history():
            # lines in Job.history() are tuples of text and type,
            # we're only interested in the text.
            lines = line[0].split('\n')
            for l in lines:
                self._log.append(l)

    def is_loaded(self):
        return self._is_loaded

    def load_fonts(self, log_widget=None):
        """Run LilyPond to retrieve a list of available fonts.
        Afterwards process_results() will parse the output and build
        info structures to be used later.
        If a log.Log widget is passed as second argument this will
        be connected to the Job to provide realtime feedback on the process.
        Any caller should connect to the 'loaded' signal because this
        is an asynchronous task that takes long to complete."""
        self.reset()
        self.acknowledge_lily_fonts()
        self.run_lilypond()
        if log_widget:
            log_widget.connectJob(self.job)

    def misc_model(self):
        return self._misc_model

    def model(self):
        return self._tree_model

    def parse_entries(self):
        """Parse the LilyPond log and push entries to the various
        lists and dictionaries. Parsing the actual font style
        definition is deferred to add_style_to_family()."""
        regexp = re.compile('(.*)\\-\\d*')
        families = {}
        config_files = []
        config_dirs = []
        font_dirs = []
        last_family = None
        for e in self._log:
            if e.startswith('family'):
                # NOTE: output of this process is always English,
                # so we can hardcode the splice indices
                original_family = e[7:]
                # filter size-indexed font families
                basename = regexp.match(original_family)
                last_family = basename.groups()[0] if basename else original_family
            elif last_family:
                # We're in the second line of a style definition
                self.add_style_to_family(families, last_family, e)
                last_family = None
            elif e.startswith('Config files:'):
                config_files.append(e[14:])
            elif e.startswith('Font dir:'):
                font_dirs.append(e[10:])
            elif e.startswith('Config dir:'):
                config_dirs.append(e[12:])

        return families, config_files, config_dirs, font_dirs

    def process_results(self):
        """Parse the job history list to dictionaries."""

        self.flatten_log()
        families, config_files, config_dirs, font_dirs = self.parse_entries()

        self._tree_model.populate(families)
        self._misc_model.populate(config_files, config_dirs, font_dirs)

        self._is_loaded = True
        self.job = None
        self.loaded.emit()

    def run_lilypond(self):
        """Run lilypond from info with the args list, and a job title."""
        info = self.lilypond_info
        j = self.job = job.Job()
        j.decode_errors = 'replace'
        j.decoder_stdout = j.decoder_stderr = codecs.getdecoder('utf-8')
        j.command = ([info.abscommand() or info.command]
            + ['-dshow-available-fonts'])
        j.set_title(_("Available Fonts"))
        j.done.connect(self.process_results)
        j.start()
