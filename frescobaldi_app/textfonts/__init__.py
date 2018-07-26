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
Handle everything around (available) text fonts.
NOTE: "available" refers to the fonts that are available to LilyPond,
which may be different than for arbitrary programs and can canonically
be determined by running `lilypond -dshow-available-fonts`.
"""

import re
import os

from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QAction

import actioncollection
import actioncollectionmanager
import plugin
import job
import codecs
import signals

def textfonts(mainwindow):
    return TextFonts.instance(mainwindow)


class TextFonts(plugin.MainWindowPlugin):

    def __init__(self, mainwindow):
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.textfonts_show_available_fonts.triggered.connect(self.showAvailableFonts)

    def showAvailableFonts(self):
        """Menu action Show Available Fonts."""
        from engrave import command
        info = command.info(self.mainwindow().currentDocument())
        from . import availablefontsdialog
        availablefontsdialog.show_available_fonts(self.mainwindow(), info)


class Actions(actioncollection.ActionCollection):
    name = "textfonts"

    def createActions(self, parent=None):
        self.textfonts_show_available_fonts = QAction(parent)

    def translateUI(self):
        self.textfonts_show_available_fonts.setText(_("Show Available &Fonts..."))


class Fonts(object):
    """Provide information about available text fonts. These are exactly the
    fonts that can be seen by LilyPond.
    This is only produced upon request but then stored permanently during the
    program's runtime.
    load_fonts() will run LilyPond to determine the list of fonts, optionally
    reporting to a log.Log widget if given.
    Since this is an asynchronous process GUI elements that want to use the
    results have to connect to the 'loaded' signal which is emitted after
    LilyPond has completed and the results been parsed.

    A Fonts() object is immediately available as textfonts.available_fonts, and
    its is_loaded member can be requested to test if fonts have already been
    loaded.
    """

    loaded = signals.Signal()

    def __init__(self):
        self._reset_storage()
        self.job = None

    def _reset_storage(self):
        self._font_families = {}
        self._family_names = []
        self._log = []
        self._config_files = []
        self._config_dirs = []
        self._font_dirs = []
        # needs to be reset for the LilyPond-dependent fonts
        self.font_db = QFontDatabase()

        self.is_loaded = False


    def config_dirs(self):
        return self._config_dirs

    def config_files(self):
        return self._config_files

    def family_names(self):
        return self._family_names

    def font_dirs(self):
        return self._font_dirs

    def font_families(self):
        return self._font_families

    def log(self):
        return self._log


    def acknowledge_lily_fonts(self, info):
        """Add the OpenType fonts in LilyPond's font directory
        to Qt's font database. This should be relevant (untested)
        when the fonts are not additionally installed as system fonts."""
        font_dir = os.path.join(info.datadir(), 'fonts', 'otf')
        for lily_font in os.listdir(font_dir):
            self.font_db.addApplicationFont(
                os.path.join(font_dir, lily_font)
            )

    def add_style_to_family(self, family_name, input):
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

        if not family_name in self._font_families.keys():
            self._font_families[family_name] = {}
        family = self._font_families[family_name]
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

    def load_fonts(self, info, log_widget=None):
        """Run LilyPond to retrieve a list of available fonts.
        Afterwards process_results() will parse the output and build
        info structures to be used later.
        If a log.Log widget is passed as second argument this will
        be connected to the Job to provide realtime feedback on the process.
        Any caller should connect to the 'loaded' signal because this
        is an asynchronous task that takes long to complete."""
        self._reset_storage()
        self.acknowledge_lily_fonts(info)
        self.run_lilypond(info)
        if log_widget:
            log_widget.connectJob(self.job)
        self.job.done.connect(self.process_results)

    def parse_entries(self):
        """Parse the LilyPond log and push entries to the various
        lists and dictionaries. Parsing the actual font style
        definition is deferred to add_style_to_family()."""
        regexp = re.compile('(.*)\\-\\d*')
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
                self.add_style_to_family(last_family, e)
                last_family = None
            elif e.startswith('Config files:'):
                self._config_files.append(e[14:])
            elif e.startswith('Font dir:'):
                self._font_dirs.append(e[10:])
            elif e.startswith('Config dir:'):
                self._config_dirs.append(e[12:])

    def process_results(self):
        """Parse the job history list to dictionaries."""

        self.flatten_log()
        self.parse_entries()

        # Store sorted reference lists.
        self._family_names = sorted(
            self._font_families.keys(), key=lambda s: s.lower())
        self._config_files = sorted(
            self._config_files, key=lambda s: s.lower())
        self._config_dirs = sorted(
            self._config_dirs, key=lambda s: s.lower())
        self._font_dirs = sorted(
            self._font_dirs, key=lambda s: s.lower())

        self.is_loaded = True
        self.job = None
        self.loaded.emit()


    def run_lilypond(self, info):
        """Run lilypond from info with the args list, and a job title."""
        j = self.job = job.Job()
        j.decode_errors = 'replace'
        j.decoder_stdout = j.decoder_stderr = codecs.getdecoder('utf-8')
        j.command = ([info.abscommand() or info.command]
            + ['-dshow-available-fonts'])
        j.set_title(_("Available Fonts"))
        j.start()


# This Fonts() object is stored on application level, not per MainWindow
available_fonts = Fonts()
