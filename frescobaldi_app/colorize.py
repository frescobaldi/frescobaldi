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
import highlighter
import textformats


__all__ = ['colorize']


def colorize(text, state=None):
    """Converts the text to HTML using the specified or guessed state."""
    if state is None:
        state = ly.lex.guessState(text)
    result = []
    h = highlighter.highlightFormats()
    d = textformats.formatData('editor')
    result.append('<pre style="color: {0}; background: {1}; '
        'font-family: &quot;{2}&quot;; font-size: {3}pt;">'.format(
        d.baseColors['text'].name(), d.baseColors['background'].name(),
        d.font.family(), d.font.pointSizeF()))
    for t in state.tokens(text):
        f = h.format(t)
        if f:
            s = style(f)
            if s:
                result.append('<span style="{0}">{1}</span>'.format(s, escape(t)))
                continue
        result.append(escape(t))
    result.append('</pre>')
    return ''.join(result)

    
def escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def style(f):
    s = []
    if f.hasProperty(QTextFormat.ForegroundBrush):
        s.append('color: {0};'.format(f.foreground().color().name()))
    if f.hasProperty(QTextFormat.BackgroundBrush):
        s.append('color: {0};'.format(f.background().color().name()))
    if f.hasProperty(QTextFormat.FontWeight):
        s.append('font-weight: {0};'.format(f.fontWeight() * 8))
    if f.fontItalic():
        s.append('font-style: italic;')
    return ' '.join(s)


