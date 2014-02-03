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
Export syntax-highlighted text as HTML.
"""

from __future__ import unicode_literals

import lydocument
import textformats
import ly.document
import ly.colorize


def html_text(text, mode=None, scheme='editor'):
    """Converts the text to HTML using the specified or guessed mode."""
    c = ly.document.Cursor(ly.document.Document(text, mode))
    return html(c, scheme, True)

def html_inline(cursor, scheme='editor'):
    c = lydocument.cursor(cursor)
    return html(c, scheme, True)

def html_document(document, scheme='editor'):
    c = lydocument.Cursor(lydocument.Document(document))
    return html(c, scheme)

def html(cursor, scheme='editor', inline=False):
    """Return a HTML document with the syntax-highlighted region.
    
    The tokens are marked with <span> tags. The cursor is a 
    ly.document.Cursor instance. The specified text formats scheme is used 
    (by default 'editor'). If inline is True, the span tags have inline 
    style attributes. If inline is False, the span tags have class 
    attributes and a stylesheet is included.
    
    """
    data = textformats.formatData(scheme)       # the current highlighting scheme
    fgcolor = data.baseColors['text'].name()
    bgcolor = data.baseColors['background'].name()
    mapper = ly.colorize.css_mapper()           # map the token class to hl class
    if inline:
        formatter = ly.colorize.css_style_attribute_formatter(data.css_scheme())
        css = None
        body = '<pre style="color: {0}; background: {1}">{2}</pre>\n'.format(
            fgcolor, bgcolor, ly.colorize.html(cursor, mapper, formatter))
    else:
        formatter = ly.colorize.format_css_span_class # css-styled html
        css = 'pre {{\n  color: {0};\n  background: {1}\n}}\n\n{2}'.format(
            fgcolor, bgcolor, ly.colorize.format_stylesheet(data.css_scheme()))
        body = '<pre>{0}</pre>\n'.format(ly.colorize.html(cursor, mapper, formatter))
    return ly.colorize.format_html_document(body, stylesheet=css)


