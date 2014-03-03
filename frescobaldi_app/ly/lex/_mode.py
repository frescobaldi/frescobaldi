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

"""
Registry for the different modes used by the tokenizer.


There are two items in this module:

1. the modes dictionary.

   This maps a mode name to a function returning the base parser class for
   that mode.  (This way the corresponding module only needs to be imported
   when the mode is really needed.)
   
2. the guessMode function.

   This tries to guess the type of the given text and returns a mode name.
   
   
You can easily add more modes in separate modules and mention them here,

Don't use this module directly!  modes and guessMode are imported in the main
tokenize module.

"""

from __future__ import unicode_literals

__all__ = ['modes', 'guessMode']


def _modes():
    """Returns a dictionary mapping a mode name to a function.
    
    The function should return the initial Parser instance for that mode.
    
    """
    
    def lilypond():
        from . import lilypond
        return lilypond.ParseGlobal
    
    def scheme():
        from . import scheme
        return scheme.ParseScheme
        
    def docbook():
        from . import docbook
        return docbook.ParseDocBook
        
    def latex():
        from . import latex
        return latex.ParseLaTeX
        
    def texinfo():
        from . import texinfo
        return texinfo.ParseTexinfo
        
    def html():
        from . import html
        return html.ParseHTML
        
    # more modes can be added here
    return locals()
    

# dictionary mapping mode name to a function returning initial parser instance
# for that mode. Can also be used to test the existence of a mode
modes = _modes()
del _modes


def guessMode(text):
    """Tries to guess the type of the input text, using a quite fast heuristic.
    
    Returns one of the strings also present as key in the modes dictionary.
    
    """
    text = text.lstrip()
    if text.startswith(('%', '\\')):
        if '\\version' in text or '\\relative' in text or '\\score' in text:
            return "lilypond"
        if "\\documentclass" in text or "\\begin{document}" in text:
            return "latex"
        return "lilypond"
    if text.startswith("<<"):
        return "lilypond"
    if text.startswith("<"):
        if 'DOCTYPE book' in text or "<programlisting" in text:
            return "docbook"
        else:
            return "html"
    if text.startswith(("#!", ";", "(")):
        return "scheme"
    if text.startswith('@'):
        return "texinfo"
    return "lilypond"



# dictionary mapping mode name to a default extension for a file of that mode.
extensions = {
    'lilypond': '.ly',
    'html':     '.html',
    'scheme':   '.scm',
    'latex':    '.lytex',
    'texinfo':  '.texi',
    'docbook':  '.docbook',
}

