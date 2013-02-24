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
Export syntax-highlighted text as HTML.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QTextFormat

import ly.lex
import highlighter
import textformats
import tokeniter


def textformat2css(f):
    """Convert a QTextFormat to a dict of CSS style declarations."""
    d = {}
    if f.hasProperty(QTextFormat.ForegroundBrush):
        d['color'] = f.foreground().color().name()
    if f.hasProperty(QTextFormat.BackgroundBrush):
        d['background'] = f.background().color().name()
    if f.hasProperty(QTextFormat.FontWeight):
        d['font-weight'] = format(f.fontWeight() * 8)
    if f.fontItalic():
        d['font-style'] = 'italic'
    if f.hasProperty(QTextFormat.TextUnderlineStyle):
        d['text-decoration'] = 'underline'
        if f.hasProperty(QTextFormat.TextUnderlineColor):
            d['text-decoration-color'] = f.underlineColor().name()
    return d


def escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class HtmlHighlighter(object):
    """Convert highlighted text or tokens to HTML."""
    def __init__(self, data=None):
        """Initialize the HtmlHighlighter with a TextFormatData instance.
        
        If none is given, the textformats.textFormat('editor') is used.
        
        """
        self.setFormatData(data or textformats.formatData('editor'))
    
    def setFormatData(self, data):
        """Sets a TextFormatData instance for this HTML highlighter."""
        self._data = data
        self._formats = f = {} # maps css class to css declarations
        self._classes = c = {} # maps token class to css class
        for cls, fmt in highlighter.mapping(data).items():
            name = cls.__module__.split('.')[-1] + '-' + cls.__name__
            c[cls] = name
            f[name] = textformat2css(fmt)

    def css_data(self):
        """Yield css stubs for all the styles."""
        yield 'body', {
            'color': self._data.baseColors['text'].name(),
            'background': self._data.baseColors['background'].name(),
            'font-family': '"{0}"'.format(self._data.font.family()),
            'font-size': format(self._data.font.pointSizeF()),
        }
        for c in sorted(self._formats):
            yield '.' + c, self._formats[c]

    @classmethod
    def format_css_items(self, items, separator=" "):
        """Formats css items as text using the separator string.
        
        By default a space is used, but you could also use e.g. "\n  ".
        
        """
        return separator.join(
            "{0}: {1};".format(k, v)
            for k, v in items.items())

    def stylesheet(self):
        """Returns the stylesheet for all the styles."""
        return "\n".join(
            '{0} {{\n  {1}\n}}\n'.format(
            selector, self.format_css_items(items, '\n  '))
            for selector, items in self.css_data())

    def html_for_token(self, token, cls=None):
        """Return a piece of HTML for the specified token.
        
        The specified class is used, or the token's class.
        
        """
        if cls is None:
            cls = type(token)
        try:
            css = self._classes[cls]
        except KeyError:
            for c in cls.__mro__[highlighter._token_mro_slice]:
                try:
                    css = self._classes[c]
                    break
                except KeyError:
                    pass
            else:
                return escape(token)
            self._classes[cls] = css
        return '<span class="{0}">{1}</span>'.format(css, escape(token))
            
    def html_document(self, doc):
        """Returns HTML for the specified Document."""
        return self.html_wrapper(
            "".join(self.html_for_token(t)
                    for t in tokeniter.all_tokens(doc)))
    
    def html_cursor(self, cursor):
        """Return HTML for the cursor's selection."""
        
