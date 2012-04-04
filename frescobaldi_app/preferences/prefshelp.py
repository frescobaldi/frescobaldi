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

import help.contents
from help.html import p


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
        return p(
          _("Under <em>{general_preferences}</em>, you can choose in "
            "which language Frescobaldi's user interface is translated, "
            "which user interface style you want to use, "
            "and whether you want to use the built-in Tango iconset or to use "
            "the system-wide configured icon set.").format(
            general_preferences=_("General Preferences")),
          _("Language and style take effect immediately, but the new iconset "
            "is visible after Frescobaldi has been restarted."),
          _("Under <em>{startup}</em> you can configure which session "
            "to load if Frescobaldi is started without a filename. "
            "You can choose whether to start with one empty document, with the "
            "last used session, or with a specific session. "
            "See also {link}.").format(
            startup=_("Session to load if Frescobaldi is started without arguments"),
            link=help.contents.sessions.link()),
          _("Under <em>{saving}</em>, you can choose what to do when "
            "a document is saved, such as remembering the cursor position and "
            "marked lines, or leaving a backup copy of the document (with a ~ "
            "appended). "
            "Also, you can specify a default folder in which you keep your "
            "LilyPond documents.").format(
            saving=_("When saving documents")),
        )


class preferences_lilypond(help.page):
    def title():
        return _("LilyPond Preferences")
    
    def body():
        return p(
          _("Here you can configure how LilyPond is run when you engrave your "
            "document."),
          _("If you have multiple versions of LilyPond installed you can "
            "specify them here, and configure Frescobaldi to automatically "
            "choose the right one, based on the version number that is set in "
            "the document ({more_info}).").format(
            more_info=preferences_lilypond_autoversion.link(_("more info"))),
          _("You can also configure how LilyPond is run. See the tooltips of "
            "the settings for more information."),
          _("Finally, you can specify a list of paths where the LilyPond "
            "<code>\include</code> command looks for files."),
        )


class preferences_lilypond_autoversion(help.page):
    def title():
        return _("Automatically choose LilyPond version from document")
    
    def body():
        return _(
        # same as whatsthis in lilypond.py
        "<p>If this setting is enabled, the document is searched for a "
        "LilyPond <code>\\version</code> command or a <code>version</code> "
        "document variable.</p>\n"
        "<p>The LilyPond version command looks like:</p>\n"
        "<pre>\\version \"2.14.0\"</pre>\n"
        "<p>The document variable looks like:</p>\n"
        "<pre>-*- version: 2.14.0;</pre>\n"
        "<p>somewhere (in a comments section) in the first or last 5 lines "
        "of the document. "
        "This way the LilyPond version to use can also be specified in non-LilyPond "
        "documents like HTML, LaTeX, etc.</p>\n"
        "<p>If the document specifies a version, the oldest suitable LilyPond version "
        "is chosen. Otherwise, the default version is chosen.</p>\n")
    
    def seealso():
        return (help.contents.document_variables,)


class preferences_midi(help.page):
    def title():
        return _("MIDI Settings")
    
    def body():
        return p(
          _("Here you can configure Frescobaldi's MIDI settings."),
          ' '.join((
          _("You can specify the MIDI port name to play to."),
          _("If there are no port names visible in the drop-down box, "
            "it may be necessary to connect a hardware MIDI synthesizer to "
            "your computer, or to start a software synthesizer program such "
            "as TiMidity or Fluidsynth."),
          _("On Linux, the synthesizer should be available as an ALSA MIDI "
            "device."))),
          _("If you have a device with multiple ports, you can specify the "
            "first letters of the name, to have Frescobaldi automatically pick "
            "the first available one."),
          _("And finally, when using a software synthesizer it is recommended "
            "to enable the option <em>{close_unused}</em>.").format(
                close_unused=_("Close unused MIDI output")),
        ) + _( # keep this text in sync with the whatsthis in midi.py
        "<p>If checked, Frescobaldi will close MIDI output ports that are not "
        "used for one minute.</p>\n"
        "<p>This could free up system resources that a software MIDI synthesizer "
        "might be using, thus saving battery power.</p>\n"
        "<p>A side effect is that if you pause a MIDI file for a long time "
        "the instruments are reset to the default piano (instrument 0). "
        "In that case, playing the file from the beginning sets up the "
        "instruments again.</p>\n")


class preferences_helpers(help.page):
    def title():
        return _("Helper Applications")
    
    def body():
        return p(
          _("In this page you can enter commands to open different file types. "
            "<code>$f</code> is replaced with the filename, "
            "<code>$u</code> with the URL. "
            "Leave a field empty to use the operating system default "
            "application."),
          _("For the e-mail setting, the command should accept a "
            "<code>mailto:</code> url. "
            "For the command prompt, the command should open a console window. "
            "A <code>$f</code> value is replaced with the directory of the "
            "current document."),
        )


class preferences_paths(help.page):
    def title():
        return _("Paths")
    
    def body():
        return p(
          _("Here, directories can be added that contain "
            "<code>hyph_*.dic</code> files, where the <code>*</code> "
            "stands for different language codes."),
          _("These hyphenation dictionaries are used by Frescobaldi to break "
            "lyrics text into syllabes."),
        )


class preferences_documentation(help.page):
    def title():
        return _("LilyPond Documentation")
    
    def body():
        return _(
        # same text as whatsthis in documentation.py
        "<p>Here you can add local paths or URLs pointing to LilyPond "
        "documentation. A local path should point to the directory where "
        "either the \"{documentation}\" directory lives, or the whole "
        "\"share/doc/lilypond/html/offline-root\" path.</p>\n"
        "<p>If those can't be found, documentation is looked for in all "
        "subdirectories of the given path, one level deep. This makes it "
        "possible to put multiple versions of LilyPond documentation in "
        "different subdirectories and have Frescobaldi automatically find "
        "them.</p>").format(documentation="Documentation")


class preferences_shortcuts(help.page):
    def title():
        return _("Keyboard Shortcuts")
    
    def body():
        link = '<a href="help:{0}">{1}</a>'.format
        return p(
          _("Here you can add keyboard shortcuts to all commands available. "
            "Also the {snippets} or {quickinsert} buttons that have keyboard "
            "shortcuts are listed here.").format(
                snippets=link("snippet_help", _("Snippets")),
                quickinsert=link("quickinsert_help", _("Quick Insert"))),
          _("To change a keyboard shortcut, highlight an action in the list "
            "and click the Edit button, or double-click an action. "
            "In the dialog that appears, you can enter up to four shortcuts "
            "for the action by clicking the button and typing the shortcut. "),
          _("You can define a new scheme by using the New button."),
        )


class preferences_fontscolors(help.page):
    def title():
        return _("Fonts & Colors")
    
    def body():
        return p(
          _("Here you can set the editor font (a monospace font is "
            "recommended) and all colors."),
          _("The first item lets you set the colors for the text editor "
            "backgroud, foreground, selection background, the current line, "
            "line markings, the paper color in the Music View, etcetera."),
          _("The second item lets you set color and other attributes of the "
            "general highlighting styles, e.g. keyword, variable, value, "
            "comment, etcetera."),
          _("The other items contain the types of text the syntax highlighter "
            "recognizes for every particular document type Frescobaldi "
            "supports. Some of these types inherit a general style. "
            "It is possible to set the attributes bold, italic, underline and "
            "the foreground, background and underline color."),
          _("You can define a new scheme by using the New button."),
        )


class preferences_tools(help.page):
    def title():
        return _("Tools")
    
    def body():
        return p(_("Here you can change the settings for various tools."))



