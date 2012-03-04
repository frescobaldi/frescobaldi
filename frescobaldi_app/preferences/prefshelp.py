# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Help for the Preferences Dialog.
"""

from __future__ import unicode_literals

import help


# html helpers
p = "<p>{0}</p>\n".format


class preferences_dialog(help.page):
    def title():
        return _("Preferences")
    
    def body():
        return p(_(
        "In the Preferences Dialog (under {menu}) you can configure many "
        "aspects of Frescobaldi and LilyPond.").format(
            menu = help.menu(_("Edit"), _("Preferences"))))

    def children():
        from . import pageorder
        return tuple(cls.help for cls in pageorder()
                              if cls.help is not preferences_dialog)


class preferences_general(help.page):
    def title():
        return _("General Preferences")
    
    def body():
        return 'general prefs'



class preferences_lilypond(help.page):
    def title():
        return _("LilyPond Preferences")
    
    def body():
        return '\n'.join((
        p(_("Here you can configure how LilyPond is run when you engrave your "
            "document.")),
        ))



class preferences_midi(help.page):
    def title():
        return _("MIDI Settings")
    
    def body():
        return 'midi-prefs'



class preferences_helpers(help.page):
    def title():
        return _("Helper Applications")
    
    def body():
        return 'helper-prefs'



class preferences_paths(help.page):
    def title():
        return _("Paths")
    
    def body():
        return 'paths-prefs'



class preferences_documentation(help.page):
    def title():
        return _("LilyPond Documentation")
    
    def body():
        return 'doc-prefs'




class preferences_shortcuts(help.page):
    def title():
        return _("Keyboard Shortcuts")
    
    def body():
        return 'shortcut-prefs'



class preferences_fontscolors(help.page):
    def title():
        return _("Fonts & Colors")
    
    def body():
        return 'fonts-colors-prefs'



class preferences_tools(help.page):
    def title():
        return _("Tools")
    
    def body():
        return 'tools-prefs'



