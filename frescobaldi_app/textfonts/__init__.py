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

import re

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


    def load_fonts(self, info, log_widget=None):
        """Run LilyPond to retrieve a list of available fonts.
        Afterwards process_results will parse the output and build
        info structures to be used later.
        If a log.Log widget is passed as second argument this will
        be connected to the Job to provide realtime feedback on the process."""
        self._reset_storage()
        self.run_lilypond(info)
        if log_widget:
            log_widget.connectJob(self.job)
        self.job.done.connect(self.process_results)


    def process_results(self):
        """Parse the job history list to dictionaries."""

        # Process job history into flat string list
        for line in self.job.history():
            lines = line[0].split('\n')
            for l in lines:
                self._log.append(l)

        # Parse entries
        last_family = None
        regexp = re.compile('(.*)\\-\\d*')
        for e in self._log:
            if e.startswith('family'):
                original_family = e[7:]
                basename = regexp.match(original_family)
                last_family = basename.groups()[0] if basename else original_family
                if not last_family in self._font_families.keys():
                    self._font_families[last_family] = {}
            elif last_family:
                self.update_family(last_family, e)
                last_family = None
            elif e.startswith('Config files:'):
                self._config_files.append(e[14:])
            elif e.startswith('Font dir:'):
                self._font_dirs.append(e[10:])
            elif e.startswith('Config dir:'):
                self._config_dirs.append(e[12:])

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
        j.command = [info.abscommand() or info.command] + ['-dshow-available-fonts']
        j.set_title(_("Available Fonts"))
        j.start()


    def update_family(self, family_name, input):
        """Parse a font face definition."""
        family = self._font_families[family_name]
        input = input.strip().split(':')
        # This is a safeguard against improper entries
        if len(input) == 2:
            series = input[0].split(',')[-1].replace('\\-', '-')
            if not series in family.keys():
                family[series] = []
            family[series].append(input[1][6:])


# This Fonts() object is stored on application level, not per MainWindow
available_fonts = Fonts()
