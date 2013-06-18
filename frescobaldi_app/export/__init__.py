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
    def __init__(self):
        # the following properties will be read from the Settings
        
        # What to export
        self.source = "selection"       # alternatives: "selection"
                                        #               "document"
                                        #               "css"
        
        # Where to export to
        self.dest = "clipboard"         # alternatives: "clipboard"
                                        #               "file"
        # filename only applicable when dest = "file"
        self.filename = ""
        
        # How to insert formatting
          # 'css' isn't applicaple to 'formatted text' output
        self.style = "external"              # alternatives: "css"
                                        #               "inline"
                                        #               "external"
        self.external_css = "lilypond.css"
        
        # Which output format do we generate
        self.format = "html"            # alternatives: "html"
                                        #               "formatted" (rich text)
                                        #               "pdf" (not yet implemented)
                                        #               "odt" (not yet implemented
                                        #                      for ODT we'd have to distinguish
                                        #                      between inline and css styling too)
        # Are we exporting just the content or a full document
          # not applicable for PDF or ODT
        self.document = "full"          # alternatives: "full"
                                        #               "body"
        
        
    def autosave(self):
        #TODO: return flag from Settings
        return True
        
    def save(self):
        #TODO: save current properties to Settings
        pass
        

# load settings from Settings (initially)
# keep settings during session
# allow saving settings to Settings

options = ExportOptions()

