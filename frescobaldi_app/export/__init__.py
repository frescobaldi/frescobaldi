# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2012 by Wilbert Berendsen
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
Export formatted LilyPond source code.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings, Qt


class ExportOptions:
    """
    Manage options used for exporting source code.
    Is aware of loading/saving from Preferences.
    
    Settings are managed in the ExportDialog instance and not 
    in the Preferences Dialog.
    This is because one needs the settings when executing the task.
    Settings can be explicitely or automatically saved throughout sessions
    """
    def __init__(self):
        # the following properties will be read from the Settings
        self._options = {}
        
        # filename only applicable when dest = "file"
        # won't be stored in Settings
        self._options["filename"] = ""
        # default filename: suggest document's filename with appropriate extension
        #self._options["default_filename"] = True
        # default filename for css export file.
        # Not saved in Settings but suggestion influenced by default_filename
        self._options["external_css"] = "lilypond.css"
        
        self.load_settings()
        
    def autosave(self):
        """Save export options to Settings if autosave preference is set"""
        if QSettings().value("export/autosave_settings", True, bool):
            self.save()
    
    def changed(self):
        """Determine if settings are different from the Settings"""
        s = QSettings()
        s.beginGroup("export")
        for key in self._options:
            if self._options[key] != s.value(key, type=type(self._options[key])):
                return True
        return False
    
    def get(self, name):
        return self._options[name]
        
    def load_settings(self):
        s = QSettings()
        s.beginGroup("export")
        # What to export
        # possible values: selection, document, css
        self._options["source"] = s.value("source", "selection")
        # Where to export to
        # possible values: clipboard, file
        self._options["dest"] = s.value("dest", "clipboard")
        # How to insert formatting
        # possible values: external, css, inline
        # 'css' isn't applicaple to 'formatted text' output
        # 'external' is only applicable to 'html' output
        self._options["style"] = s.value("style", "css")
        # Which output format do we generate
        # possible values: html, formatted (rich text), pdf, odt
        self._options["format"] = s.value("format", "html")
        # Are we exporting just the content or a full document
        # not applicable for PDF or ODT
        # possible values: full, body
        self._options["document"] = s.value("document", "full")
        
        for key in self._options:
            print key, self._options[key]
        
    def save(self):
        print "Enter save"
        if self.changed():
            s = QSettings()
            s.beginGroup("export")
            for key in self._options:
                s.setValue(key, self._options[key])
        
options = ExportOptions()

