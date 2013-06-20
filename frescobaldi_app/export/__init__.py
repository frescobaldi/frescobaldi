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
        
    def assign(self, other):
        """assign the properties of another ExportOptions instance."""
        if not isinstance(other, ExportOptions):
            raise ValueError
        for key in self._options:
            self._options[key] = other._options[key]
    
    def autosave(self):
        """Save export options to Settings if autosave preference is set"""
        if self._options["autosave_settings"]:
            self.save()
    
    def changed(self):
        """Determine if settings are different from the Settings"""
        s = QSettings()
        s.beginGroup("export")
        for key in self._options:
            if not s.value(key):
                # option isn't present in Settings
                return True
            # workaround for Boolean return bug in Qt
            if type(self._options[key]) == bool:
                svalue = s.value(key, type=bool)
            elif type(self._options[key]) == int:
                svalue = int(s.value(key))
            else:
                svalue = s.value(key)
            if self._options[key] != svalue:
                return True
        return False
    
    def load_settings(self):
        s = QSettings()
        s.beginGroup("export")
        # What to export
        # possible values: selection, document, css
        self._options["source"] = s.value("source", "selection")
        # Where to export to
        # possible values: clipboard, file, printer
        self._options["dest"] = s.value("dest", "clipboard")
        # How to insert formatting
        # possible values: external, css, inline
        # 'css' isn't applicaple to 'formatted text' output
        # 'external' is only applicable to 'html' output
        self._options["style"] = s.value("style", "css")
        # Which output format do we generate
        # possible values: html, formatted (rich text)
        self._options["format"] = s.value("format", "html")
        # Which file type to we create
        # possible values: html, pdf, odt
        self._options["filetype"] = s.value("filetype", "html")
        # Are we exporting just the content or a full document
        # not applicable for PDF or ODT
        # possible values: full, body
        self._options["document"] = s.value("document", "full")
        # Print document title
        self._options["print_title"] = s.value("print_title", True, bool)
        # Prepend line numbers
        self._options["linenumbers"] = s.value("linenumbers", True, bool)
        # Autosave options
        # If set to True settings are remembered automatically,
        # otherwise one has to explicitely save them
        self._options["autosave_settings"] = s.value("autosave_settings",  True, bool)
        # Layout options (Printer/PDF export)
        self._options["orientation"] = s.value("orientation", "portrait")
        self._options["color"] = s.value("color", "color")
        self._options["margintop"] = s.value("margintop", 20, int)
        self._options["marginbottom"] = s.value("marginbottom", 20, int)
        self._options["marginleft"] = s.value("marginleft", 20, int)
        self._options["marginright"] = s.value("marginright", 20, int)
        
                
    def save(self):
        if self.changed():
            s = QSettings()
            s.beginGroup("export")
            for key in self._options:
                s.setValue(key, self._options[key])
                
    def set(self, key, value, dlg = None):
        self._options[key] = value
                
    def value(self, name):
        return self._options[name]
        
options = ExportOptions()

