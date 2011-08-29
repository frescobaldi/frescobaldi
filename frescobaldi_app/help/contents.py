# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from .helpimpl import page
from colorize import colorize


class nohelp(page):
    """Shown when no help is found."""
    def title():
        return _("No Help")
    
    def body():
        return _("No help has been found on this topic.")


class contents(page):
    """Main help contents."""
    def title():
        return _("Help contents")
    
    def children():
        import scorewiz.dialog
        return (
            introduction,
            starting,
            scorewiz.dialog.scorewiz_help,
            
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
Those text files can be created with any text editor, and LilyPond then loads
the text file and outputs a beautiful engraving, by default in PDF format.
</p>

<p>
Frescobaldi is an application designed to make editing LilyPond music scores
faster and easier. You still will need to learn the LilyPond input language.
If you read the {getting_started} section of this User Guide, you'll also pickup
some LilyPond basics.
</p>

<p>
Then you can continue to learn using the Learning Manual from 
<a href="http://lilypond.org/doc/">LilyPond's excellent online documentation</a>.
</p>""").format(getting_started=starting.link())



class starting(page):
    def title():
        return _("Getting Started")
    
    def body(cls):
        return "<p>bla di bla</p>" + colorize(
r"""\relative c' {
  c d e f g
  \override NoteHead #'stencil = ##f
}""")



