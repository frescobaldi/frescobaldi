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
Colorize a string as HTML using a ly.lex State and highlightformats.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QTextFormat

import ly.lex
import highlight2html
import textformats


__all__ = ['colorize']


def colorize(text, state=None):
    """Converts the text to HTML using the specified or guessed state."""
    if state is None:
        state = ly.lex.guessState(text)
    data = textformats.formatData('editor')
    h = highlight2html.HtmlHighlighter(data, inline_style=True)
    
    result = [
        '<pre style="color: {0}; background: {1}; font-family: {2}">'.format(
        data.baseColors['text'].name(),
        data.baseColors['background'].name(),
        data.font.family())]
    
    result.extend(map(h.html_for_token, state.tokens(text)))
    result.append('</pre>')
    return ''.join(result)


