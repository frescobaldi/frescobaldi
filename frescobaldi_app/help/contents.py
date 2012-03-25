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
from colorize import colorize

import info


class nohelp(page):
    """Shown when no help is found."""
    def title():
        return _("No Help")
    
    def body():
        return _("No help has been found on this topic.")


class contents(page):
    """Main help contents."""
    def title():
        return _("Frescobaldi Manual")
    
    def body():
        text = _("""\
<p>
Frescobaldi is a light-weight, but powerful editor for LilyPond music files.
This manual is written by {author} and documents {appname} version {version}.
</p>
""").format(author=info.maintainer, appname=info.appname, version=info.version)
        # L10N: Translate this sentence and fill in your own name to have it appear in the About Dialog.
        translator = _("Translated by Your Name.")
        if translator != "Translated by Your Name.":
            text += "<p>{0}</p>".format(translator)
        text += _("""\
<h3>How to get help inside Frescobaldi</h3>

<p>
In many dialogs there are Help buttons or you can press the {key_help} key.
Many user interface items also have "What's This" information which can be
revealed by pressing {key_whatsthis} or by selecting {menu_whatsthis}.
</p>
""").format(key_help = shortcut(QKeySequence.HelpContents),
            key_whatsthis = shortcut(QKeySequence.WhatsThis),
            menu_whatsthis = menu(_("Help"), _("What's This")))
        return text
    
    def children():
        import scorewiz.dialog
        import preferences.prefshelp
        return (
            introduction,
            starting,
            scorewiz.dialog.scorewiz_help,
            tools,
            editor,
            preferences.prefshelp.preferences_dialog,
            troubleshooting,
            about,
            toc,
        )


class introduction(page):
    def title():
        return _("Introduction")
    
    def body():
        return _("""\
<p>
<a href="http://lilypond.org/">LilyPond</a>
is an open-source music engraving program, producing very high-quality sheet
music printouts from fairly simple text input files.
Input files can be created using virtually any text editor, which LilyPond 
can then compile and output beautiful engraving, by default but not restricted to, PDF.
</p>

<p>
Frescobaldi is an application to make editing LilyPond music scores
faster and easier. You will still need to learn LilyPond's input language
but if you read the {getting_started} section of this User Guide, you'll pickup
some LilyPond basics to get you started.
</p>

<p>
Once you have grasped the basics, the next step would be to use the LilyPond 
Learning Manual from 
<a href="http://lilypond.org/doc/">LilyPond's excellent online documentation</a>.
</p>""").format(getting_started=starting.link())



class starting(page):
    def title():
        return _("Getting Started")
    
    def body(cls):
        d = dict(
            example = colorize(r"""\relative c'' {
  \time 7/4
  c2 bes4 a2 g a bes4 a( g) f2
}
\addlyrics {
  Join us now and share the soft -- ware!
}"""),
            key_engrave = shortcut(action("engrave", "engrave_preview")),
            key_jump = shortcut(action("musicview", "music_jump_to_cursor")),
            key_copy_image = shortcut(action("musicview", "music_copy_image")),
            key_error = shortcut(action("logtool", "log_next_error")),
            menu_engrave = menu(_("LilyPond"), _("Engrave (publish)")),
            menu_preferences_lilypond = menu(
                _("menu title", "Edit"),
                _("Preferences"),
                _("LilyPond Preferences")),
            menu_clear_error_marks = menu(
                _("menu title", "View"),
                _("Clear Error Marks")),
            menu_copy_image = menu(
                _("menu title", "Edit"),
                _("Copy to Image...")),
        )
        return _("""\
<p>
The default screen of Frescobaldi shows a text document on the left and an
empty Music View window on the right.
</p>

<p>
Now, in the text view, enter some LilyPond code, like this:
</p>

{example}

<p>
Then click the Lily toolbar button or press {key_engrave}.
LilyPond will start to processes your file and the PDF will be displayed 
in the Music View on the right. If LilyPond encounters any errors or 
warnings they will be displayed in the LilyPond Log at the bottom of the screen.
</p>

<p><img src="getting_started1.png"></p>

<p>
The Music View has many possibilities:
<p>

<ul>
<li>
Hovering over notes and other music objects will highlight them in the text
on the left window; clicking on them will place a cursor to the left of the
object also in the left window.
</li>

<li>
Use the Ctrl key and your mouse wheel to zoom in and out. Zooming will center 
around the mouse pointer.
</li>

<li>
Ctrl-left-click-and-hold the mouse to magnify a small section of the Music View
without zooming in the whole view.
</li>

<li>
Selecting text in the main text window will highlight corresponding notes in the 
Music View; press {key_jump} to explicitly center and highlight a note or other objects
in the Music View.
</li>

<li>
Shift-drag a selection and then press {key_copy_image} or {menu_copy_image}
to copy the selected music as a raster image to the clipboard, a file or
another application.
</li>
</ul>

<p>
When your music score is complete, run LilyPond once more but with
clickable notes turned off: menu {menu_engrave}. This significantly
reduces the size of the PDF.
</p>

<p>
If LilyPond does not start at all, check if you have installed LilyPond
correctly and that the lilypond command is in your system's PATH environment
variable. If needed, provide the exact path to your LilyPond executable under
{menu_preferences_lilypond}.
</p>

<p>
If LilyPond encounters any warnings or errors in your document they will show up in the 
LilyPond Log window at the bottom of the screen. Frescobaldi will then highlight 
these lines in the text view where the errors are. Clicking the error in 
the Log Window or pressing {key_error} immediately brings the text cursor to the 
offending line in your text view. Pressing {key_error} again will move to the 
next error message, and so on. LilyPond will remove any previous error line 
highlights the next time it is run but you can also remove any error line markings 
manually with the option {menu_clear_error_marks}.
</p>
""").format(**d)


class tools(page):
    def title():
        return _("Other Tools")
    
    def body():
        return _("""\
<p>Some other important tools are listed here.</p>
""")
    
    def children():
        import quickinsert.widget
        import snippet.widget
        import pitch.pitch
        import rhythm.rhythm
        import hyphendialog
        return (
            quickinsert.widget.quickinsert_help,
            snippet.widget.snippet_help,
            pitch.pitch.pitch_help,
            rhythm.rhythm.rhythm_help,
            hyphendialog.lyrics_help,
        )


class about(page):
    def title():
        return _("About Frescobaldi")
    
    def body():
        return _("""\
<p>
Frescobaldi is named after
<a href="http://en.wikipedia.org/wiki/Girolamo_Frescobaldi">Girolamo
Frescobaldi (1583 &#8211; 1643)</a>, an Italian organist and composer.
</p>

<p>
Frescobaldi's homepage is at
<a href="http://www.frescobaldi.org/">www.frescobaldi.org</a>
and there is a mailinglist at
<a href="mailto:frescobaldi@googlegroups.com">frescobaldi@googlegroups.com</a>
(<a href="http://groups.google.com/group/frescobaldi">more info</a>).
</p>
""")
    def children():
        return (
            credits,
            contributing,
            history,
        )


class credits(page):
    def title():
        return _("Credits")

    def body():
        text = []
        text.append(
            _("Frescobaldi's main author is {author}.").format(author=info.maintainer))
        import about
        text.extend(about.credits())
        return '\n'.join(map('<p>{0}</p>'.format, text))


class contributing(page):
    def title():
        return _("Contributing")
    
    def body():
        return _("""\
<p>
Frescobaldi is a <a href="http://www.gnu.org/philosophy/free-sw.html">Free
Software</a> project to create a user friendly LilyPond music score editor.
The goal is to make Frescobaldi available on all major platforms.
</p>

<p>
Frescobaldi is developed in a public GitHub repository at {url}.
There you can browse or checkout the source code and report bugs and wishes.
</p>

<p>
You can contribute by simply using Frescobaldi and reporting bugs and suggestions.
Translations are also very welcome. How to create new translations is described
in the file README-translations in the source distribution of Frescobaldi.
If you want to add functionality you can find information about the source code
structure in the file README-development.
</p>
""").format(url='<a href="http://github.com/wbsoft/frescobaldi">'
                'github.com/wbsoft/frescobaldi</a>')


class history(page):
    def title():
        return _("History of Frescobaldi")

    def body():
        return _("""\
<p>
Frescobaldi has its roots in LilyKDE, which was a plugin for KDE3's editor Kate.
LilyKDE was written in Python and released in 2007 on Christmas.
</p>

<p>
When KDE developed version 4, it was not immediately possible to make Kate
plugins in Python. So LilyKDE became a standalone application, wrapping the
Kate texteditor part, and was renamed to Frescobaldi. It still used the Okular
KDE part to display PDF documents.
Frescobaldi 0.7 was the first public release, on Christmas 2008.
On Christmas 2009 version 1.0.0 was released and on Christmas 2010 version 1.2.0.
</p>

<p>
At that time it was decided to move away from the KDE4 libraries and just use
Python and Qt4 which are easily available on all major computing platforms.
Frescobaldi 2.0 is a complete rewrite from scratch. Its release date is
targeted at Christmas 2011.
</p>
""")


class editor(page):
    def title():
        return _("The editor")
    
    def body():
        return _("""\
<p>
In this part the features of the editor are discussed,
e.g. how to control auto-indenting, how to use search and replace,
etcetera.
</p>
""")
    def children():
        return (
            search_replace,
            document_variables,
            sessions,
        )


class search_replace(page):
    def title():
        return _("Search and replace")
    
    def body():
        d = dict(
            key_search = shortcut(action("main", "edit_find")),
            key_replace = shortcut(action("main", "edit_replace")),
            edit_menu = menu(_("Edit")),
        )
        return _("""\
<p>
In the menu {edit_menu} the commands Find ({key_search})
and Replace ({key_replace}) can be found, which open a small window at the
bottom of the view.
It is possible to search for plain text or regular expressions.
</p>

<p>
Regular expressions are advanced search texts that contain characters that can
match multiple characters in the document.
When replacing text, it is also possible to refer to parenthesized parts of the
search text.
</p>

<p>
In regular expression search mode, some characters have a special meaning:
</p>

<dl compact="compact">
<dt><code>*</code></dt>
<dd>matches the preceding character or group zero or more times</dd>
<dt><code>+</code></dt>
<dd>matches the preceding character or group one or more times</dd>
<dt><code>?</code></dt>
<dd>matches the preceding character or group zero or one time</dd>
<dt><code>[ ]</code></dt>
<dd>matches one of the contained characters</dd>
<dt><code>( )</code></dt>
<dd>group characters. This also saves the matched text in the group.
When replacing, you can use characters like <code>\\1</code>, <code>\\2</code>
etcetera, to write the text of the corresponding group in the replacement text.
</dd>
<dt><code>\\\\ \\n \\t \\s \\d \\w</code></dt>
<dd>match, respectively, a backslash, a newline, a tab, any whitespace
character, a digit, a generic word-like character.</dd>
</dl>

<p>
A full discussion on regular expressions can be found in the
<a href="http://docs.python.org/library/re.html#regular-expression-syntax">Python
documentation</a>.
</p>
""").format(**d)


class document_variables(page):
    def title():
        return _("Document variables")
    
    def body():
        text = []
        text.append('<p>')
        text.append(_("""\
Document variables are variables that influence the behaviour of Frescobaldi.
They can be written in the first five or last five lines of a document.
If a line contains '<b><code>-*-</code></b>', Frescobaldi searches the rest of
the lines for variable definitions like <code>name: value;</code>.
"""))
        text.append('</p>\n<p>')
        text.append(_("The following variables are recognized:"))
        text.append('</p>')
        text.append('<dl>')
        
        for name, arg, description in (
            ('mode', _("mode"),
                #L10N: do not translate the mode names lilypond, html, etc.
                _("Force mode to be one of lilypond, html, texinfo, latex, "
                  "docbook or scheme. Default: automatic mode recognition.")),
            ('master', _("filename"),
                _("Compiles another LilyPond document instead of the current.")),
            ('output', _("name"), ' '.join((
                _("Looks for output documents (PDF, MIDI, etc.) starting with "
                  "the specified name or comma-separated list of names."),
                _("If a name ends with a directory separator, output files are "
                  "looked for in the specified directory. "),
                _("All names are relative to the document's filename."),
                _("You can set this variable if you want to override the "
                  "automatic output file name determination (which can be time-"
                  "consuming, as Frescobaldi parses the document and all the "
                  "documents it includes, searching for the LilyPond commands "
                  "that specify the output name, such as "
                  "<code>\\bookOutputName</code>, etc)."),
                ))),
            ('coding', _("encoding"),
                _("Use another encoding than the default UTF-8.")),
            ('version', _("version"),
                _("Set the LilyPond version to use, can be used for "
                  "non-LilyPond documents.")),
            ('tab-width', _("number"),
                _("The width of a tab character, by default 8.")),
            ('indent-tabs', "yes/no",
                _("Whether to use tabs in indent, by default {no}.").format(
                no="<code>no</code>")),
            ('document-tabs', "yes/no",
                _("Whether to use tabs elsewhere in the document, "
                  "by default {yes}.").format(yes="<code>yes</code>")),
            ('indent-width', _("number"),
                _("The number of spaces each indent level uses, by default 2.")),
        ):
            text.append(
                '<dt><code>{0}</code>: <i>{1}</i><code>;</code></dt>'
                '<dd>{2}</dd>\n'
                .format(name, arg, description))
        text.append('</dl>\n')
        text.append('<p>')
        text.append(_("You can put document variables in comments."))
        text.append('</p>')
        return ''.join(text)


class sessions(page):
    def title():
        return _("Sessions")
    
    def body():
        p = '<p>{0}</p>'.format
        return '\n'.join((
        p(_("A session is basically a list of open files. At any time you can "
            "choose {menu_session_save} or {menu_session_new} and save the "
            "current list of open files to a named session.").format(
            menu_session_save=menu(_("Session"), _("Save")),
            menu_session_new=menu(_("Session"), _("New Session", "New")))),
        p(_("When you switch sessions, all current documents are closed first "
            "and then the documents of the other session are opened.")),
        p(_("Inside the session properties dialog, you can choose whether to "
            "always save the list of open documents to that session, or to "
            "only save on creation (or via {menu_session_save}). "
            "This can be useful if you want to keep the list of documents in "
            "session the same, even if you open or close documents while "
            "working.").format(
            menu_session_save=menu(_("Session"), _("Save")))),
        p(_("You can also specify a default directory for the session.")),
        ))
    
    def seealso():
        import preferences.prefshelp
        return (preferences.prefshelp.preferences_general,)


class troubleshooting(page):
    def title():
        return _("Troubleshooting")
    
    def body():
        p = '<p>{0}</p>'.format
        return p(_("Sometimes things don't go the way you would expect; "
                   "this section may give some solutions."))
    
    def children():
        return (
            ts_no_music_visible,
        )


class ts_no_music_visible(page):
    def title():
        return _("After engraving a score, the Music View does not show the music")
    
    def body():
        tag = '<{0}>{{0}}</{0}>'.format
        p = tag('p').format
        li = tag('li').format
        ol = tag('ol').format
        return ol('\n'.join((
        li('\n'.join((
            p(_("Does the <code>\\score</code> block have a layout section?")),
            p(_("If a <code>\\score</code> block has a <code>\\midi</code> "
                "section but no <code>\\layout</code> section, no PDF output "
                "is generated.")),
        ))),
        li('\n'.join((
            p(_("Do you use an exotic way to specify the output filename?")),
            p(_("Frescobaldi is able to determine the output file names by "
                "looking at the document's filename and the various LilyPond "
                "commands that specify the output filename or -suffix. "
                "Frescobaldi even searches <code>\\include</code> files for "
                "commands like <code>\\bookOutputName</code> and "
                "<code>\\bookOutputSuffix</code>.")),
            p(_("But if you use more complicated Scheme code in your document "
                "to specify the output filenames, Frescobaldi may not be able "
                "to correctly determine those filenames.")),
            p(_("In that case you can override the base name(s) using the "
                "{output} document variable.").format(output='<code>output</code>')),
            p(_("See also {link}.").format(link=document_variables.link())),
            ))),
        )))


class toc(page):
    def title():
        return _("Table of Contents")
    
    def body():
        html = ['<ul>']
        seen = set()
        def addpage(page):
            if page not in seen:
                seen.add(page)
                html.append('<li>')
                html.append(page.link())
                html.append('</li>')
                if page.children():
                    html.append('<ul>')
                    for p in page.children():
                        addpage(p)
                    html.append('</ul>\n')
        for page in contents.children():
            addpage(page)
        html.append('</ul>\n')
        return ''.join(html)


