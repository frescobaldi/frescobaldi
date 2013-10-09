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
The help contents.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QKeySequence

from .helpimpl import action, page, shortcut, menu
from .html import p, ol, ul, li
from colorize import colorize

import info


class engraving(page):
    def title():
        return _("Engraving Scores")
    
    def body():
        return p(
          _("There are three modes Frescobaldi can compile scores in: "
            "<em>Preview</em>, <em>Publication</em> and <em>Custom</em>."),
          _("<em>Preview</em> mode is useful while working on a score because it "
            "provides two-way point-and-click navigation as well as a number of "
            "modes for debugging layout issues.<br />"
            "<em>Publication</em> mode is used for producing the final PDF "
            "intended to be shared.<br />"
            "<em>Custom</em> mode allows you to specify the used LilyPond "
            "command in detail."),
          _("If you have set up different LilyPond versions and told Frescobaldi "
            "in the <em>LilyPond</em> page of the <em>Preferences</em> dialog "
            "it will try to determine the LilyPond version from the document "
            "and use the version that matches best."),
        )
    
    def children():
        return (
            eng_preview, 
            eng_publication, 
            eng_custom
        )


class eng_preview(page):
    def title():
        return _("Engrave (Preview)")
        
    def body():
        return p(
          _("When working on a score you will usually engrave your "
            "score in <em>Preview Mode</em> ({preview_shortcut}). This will enable "
            "Frescobaldi's two-way point-and-click features and will "
            "give you access to a number of \"Debug Modes\". "
            "These will display or highlight various layout aspects and will "
            "help you fine-tuning your scores.").format(preview_shortcut = shortcut(action("engrave", "engrave_preview"))),
          _("The Debug Modes are accessible through the \"Preview Options\" "
            "dockable panel which is accessible through {menu_panel}."
            "The Debug Modes are initially disabled "
            "but remember their state throughout Frescobaldi sessions.<br />"
            "If you use these features regularly it is recommendable "
            "to have the panel constantly open because you will probably "
            "switch Debug Modes quite often.").format(menu_panel = menu(_("Tools"), _("Preview Options"))),
          _("Compiling in Preview Mode will introduce a <code>-ddebug-layout</code> "
            "command line variable to be present. You can check for this with something "
            "like <code>#(if (ly:get-option \'debug-layout))</code> in your input or "
            "library files. This way you can write code that is only run when the score "
            "is compiled in Preview Mode."), 
          _("The appearance of the Debug Modes is defined by Scheme variables and can "
            "partially be configured following the directions in {preview_config}.").format(
                preview_config = eng_preview_conf.link()), 
          _("The following Debug Modes are currently implemented:")
        ) + ul(''.join("<li><p><b>{0}</b><br />{1}</p></li>\n".format(name, text)
                for name, text in (
                #L10N: Please translate the mode names the same way as in the panel UI
             (_("Display Control Points"),
              _("Slurs, Ties and other similar objects are drawn in LilyPond "
                "as third-order Bezier curves, which means that their shape "
                "is controlled by four \"control-points\" (first and last ones "
                "tell where the curve ends are placed, and the middle ones affect "
                "the curvature). Changing the shape of these objects involves "
                "moving these control-points around, and it's helpful to see "
                "where they actually are.<br />"
                "This Debug Mode will display the inner control-points "
                "as red crosses and connects them to the outer (starting) "
                "points with thin lines.")),
             (_("Color \\voiceXXX"),
              _("This mode highlights voices that have been explicitly set with "
                "one of the <code>\\voiceXXX</code> commands. This is useful "
                "when dealing with polyphony issues.")),
             (_("Color explicit directions"),
              _("This mode colors items whose directions have been explicitly set "
                "with either the predefined commands <code>\\xxxUp</code> etc. "
                "or the directional operators <code>^</code> and <code>_</code>.<br />"
                "Please note how this mode and the previous are related:<br />"
                "When the condition for one of the the modes is reverted using "
                "commands like <code>\\oneVoice</code> or <code>\\xxxNeutral</code> "
                "colors are reverted to black and may also revert the highlighting "
                "of the other Debug Mode.<br />"
                "In <code>c \\voiceTwo d \\stemUp e \\stemNeutral d \\oneVoice</code> "
                "the \'d\' may already be reverted.<br />"
                "If the score is engraved with LilyPond version 2.17.6 or later "
                "the situation is somewhat improved through the use of the "
                "<code>\\temporary</code> directive.<br />"
                "In short: If you use both Modes at the same time please expect "
                "inconsistencies.")),
             (_("Display Grob Anchors"),
              _("In LilyPond, all graphical objects have an anchor (a reference point). "
                "What is a reference point?  It's a special point that defines the "
                "object's position.  Think about geometry: if you have to define where a "
                "figure is placed on a plane, you'll usually say something like "
                "\"the lower left corner of this square has coordinates (0, 2)\" or \"the "
                "center of this circle is at (-1, 3)\". \"Lower left corner\" and \"center\" "
                "would be the reference points for square and circle.<br />"
                "This Mode displays a red dot for each grob's anchor point.")),
             (_("Display Grob Names"),
              _("This mode prints a grob's name next to it.<br />"
                "The main purpose of this Debug Mode is to retrieve information about "
                "Grob names, which may come in handy if you don\'t know where to "
                "look up available properties.<br />"
                "Please note that displaying grob anchors and displaying grob "
                "names is mutually exclusive because both functions override the "
                "grob's stencil. "
                "When both modes are active, only the grob anchors are displayed.<br />"
                "Please also note that this mode is quite intrusive and may affect the "
                "layout. It is mainly useful for learning about grob names and will especially "
                "become usable once it can be activated for single grobs."
                )),
             (_("Display Skylines"),
              _("LilyPond uses \"Skylines\" to calculate the vertical dimensions "
                "of its graphical objects in order to prevent collisions. "
                "This mode draws lines representing the skylines and is useful when "
                "dealing with issues of vertical spacing.")),
             (_("Debug Paper Columns"),
              _("LilyPond organises the horizontal spacing in \"paper columns\". "
                "This mode prints a lot of spacing information about these entities.")),
             (_("Annotate Spacing"),
              _("LilyPond has a built-in function that prints lots of information "
                "about distances on the paper, which is very useful when debugging "
                "the page layout.")),
             (_("Include Custom File"),
              _("This mode offers the opportunity to add one\'s own Debug Modes "
                "by including a custom file. This file will be included at program "
                "startup and may contain any LilyPond code you would like to have "
                "executed whenever you are engraving in Preview Mode. "
                "This file will be parsed before any of the other Debug Modes "
                "so you may use it to configure them.<br />"
                "The given string will be literally included in an <code>\\include</code> "
                "directive, so you are responsible yourself that LilyPond can find it.")),
            )))

    def children():
        return (eng_preview_conf, 
                )

class eng_preview_conf(page):
    def title():
        return _("Preview Mode Configuration")
    
    def body():
                
            
        def var_desc(desc_item):
            """Format config variable description item"""
            sep = ': ' if desc_item[2] != '' else ' '
            items = desc_item + tuple(sep)
            return (
                "<b><code>{0} </code></b><em>({1}){3}</em>{2}<br />".format(*items))
            
        def var_descriptions(descs):
            """
               Format a list of description items so no markup has
               to be in the translatable string.
               'descs' is a list of tuples, each tuple consisting of
               - variable name
               - default value (as string)
               - description, wrapped in a _() translatable string
            """
            lines = []
            for item in descs:
                lines.append(var_desc(item))
            return ''.join(lines).rstrip('<br />')
        
        return p(
         _("The appearance of the individual Debug Modes is defined through "
           "the use of configuration variables. Depending on the implementation "
           "of the mode you may modify its appearance by redefining these variables in your "
           "input files. But if you are interested in a more general solution "
           "you can make use of the <code>custom-file</code> Debug Mode. "
           "As this custom file is read in before the different debug modes "
           "you can use it to define any of the variables <em>before</em> "
           "the Debug Modes are parsed."), 
         _("The modes use the following configuration variables:")
         ) + ul(''.join("<li><p><b>{0}</b><br />{1}</p></li>\n".format(name, text)
                for name, text in (
                #L10N: Please translate the mode names the same way as in the panel UI
             (_("Display Control Points"),
             _("Variables can be redefined in input files.") + "<br />" +
             var_descriptions([
                ("debug-control-points-color", 
                    "red", 
                    ""), 
                ("debug-control-points-line-thickness", 
                    "0.05", 
                    ""), 
                ("debug-control-points-cross-thickness", 
                   "0.1", 
                   ""), 
                ("debug-control-points-cross-size", 
                    "0.7", 
                    "")])), 
             (_("Color \\voiceXXX"),
             _("These Variables currently can't be redefined in input files.") + "<br />" +
             var_descriptions([
                ("debug-voice-one-color", 
                    "darkred", 
                    ""), 
                ("debug-voice-two-color", 
                    "darkblue", 
                    ""), 
                ("debug-voice-three-color", 
                    "darkgreen", 
                    ""), 
                ("debug-voice-four-color", 
                    "darkmagenta", 
                    "")])), 
             (_("Color explicit directions"),
             _("These Variables can be redefined in input files.") + "<br />" +
             var_descriptions([
                ("debug-direction-up-color", 
                    "blue", 
                    ""), 
                ("debug-direction-down-color", 
                    "blue", 
                    ""), 
                ("debug-direction-grob-list", 
                    "all-grob-descriptions", 
                    _("Defines for which grobs the explicit direction through "
                    "operators is monitored. "
                    "By default all grobs are watched, but alternatively one "
                    "can provide a list of grobs such as e.g. "
                    "<code>#(define debug-direction-grob-list "
                    "\'(DynamicText Script))</code>"))])), 
             (_("Display Grob Anchors"),
             _("These Variables can be redefined in input files.") + "<br />" +
             var_descriptions([
                ("debug-grob-anchors-dotcolor", 
                    "red", 
                    ""), 
                ("debug-grob-anchors-grob-list", 
                    "all-grob-descriptions", 
                    _("Defines for which grobs the anchor points will be "
                    "displayed. By default all grobs are watched, but "
                    "alternatively one can provide a list of grobs such as e.g. "
                    "<code>#(define debug-grob-anchors-grob-list "
                    "\'(Script NoteHead))</code>"))])), 
             (_("Display Grob Names"),
             _("These Variables can be redefined in input files.") + "<br />" +
             var_descriptions([
                ("debug-grob-names-color", 
                    "darkcyan", 
                    ""), 
                ("debug-grob-names-grob-list", 
                    "all-grob-descriptions", 
                    _("Defines for which grobs the names will be "
                    "displayed. By default all grobs are watched, but "
                    "alternatively one can provide a list of grobs such as e.g. "
                    "<code>#(define debug-grob-names-grob-list "
                    "\'(Script NoteHead))</code>"))]))) 
            )) + p(
            _("The remaining modes are built-in to LilyPond and "
              "don't have any configuration options."))


class eng_publication(page):
    def title():
        return _("Engrave (Publication)")
    
    def body():
        return p(
          _("When engraving a score in Publication mode the point-and-click "
            "information isn't generated. This will prevent a reader of the "
            "resulting PDF document from navigating to the corresponding "
            "line in the input file, but it will also significantly decrease "
            "the file size."),
          _("You should also note that the point-and-click links contain "
            "hard-coded path information of your systen, which may be "
            "considered a security issue."),
        )



class eng_custom(page):
    def title():
        return _("Engrave (Custom)")
    
    def body():
        return p(
          _("The <em>Engrave (Custom)</em> dialog gives you detailed access "
            "to all aspects of the LilyPond command."),
          _("More documentation to come ..."),
        )


