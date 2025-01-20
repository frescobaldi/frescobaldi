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

r"""
Reformat the selection or the whole document, only adjusting whitespace.

What it does:

- remove trailing whitespace
- newline after all { or << in lilypond mode, unless terminated on same line
- same way newline before >> or }
- remove indent for commented lines with more than two comment characters
- never removes existing newlines
- Html, scheme, strings, etc are left alone

What it also could do, but not yet:

- newline before and after many non-postfix commands, such as \set, \override
- at least one blank line between multiline top-level blocks (unless comment)
- wordwrap lines longer than 79 characters

"""


import indent
import lydocument
import ly.reformat


def reformat(cursor):
    """Reformat the selection or the whole document."""
    i = indent.indenter(cursor.document())
    c = lydocument.cursor(cursor, select_all=True)
    ly.reformat.reformat(c, i)


def remove_trailing_whitespace(cursor):
    """Remove trailing whitespace from all lines in the selection.

    If there is no selection, the whole document is used.

    """
    ly.reformat.remove_trailing_whitespace(lydocument.cursor(cursor, select_all=True))


