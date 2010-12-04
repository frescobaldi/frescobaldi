# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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
A package of modules dealing with LilyPond and the LilyPond format.
"""


def guessType(text):
    """Tries to guess the type of the input text.
    
    Returns one of the strings:
        lilypond
        scheme
        docbook
        latex
        texi
        html
    
    """
    text = text.lstrip()
    if text.startswith(('%', '\\')) and ("\\documentclass" in text or "\\section" in text):
        return "latex"
    elif text.startswith("<<"):
        return "lilypond"
    elif text.startswith("<"):
        if 'DOCTYPE book' in text or "<programlisting" in text:
            return "docbook"
        else:
            return "html"
    elif text.startswith(("#!", ";", "(")):
        return "scheme"
    elif text.startswith('@'):
        return "texi"
    else:
        return "lilypond"

