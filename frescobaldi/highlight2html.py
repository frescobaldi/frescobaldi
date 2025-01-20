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


import lydocument
import textformats
import ly.document
import ly.colorize


def html_text(text, mode=None, scheme='editor', inline=True, number_lines=False, full_html=True,
    wrap_tag="pre", wrap_attrib="id", wrap_attrib_name="document"):
    """Converts the text to HTML using the specified or guessed mode."""
    c = ly.document.Cursor(ly.document.Document(text, mode))
    return html(c, scheme, inline, number_lines, full_html, wrap_tag, wrap_attrib, wrap_attrib_name)

def html_inline(cursor, scheme='editor', inline=True, number_lines=False,
        full_html=True, wrap_tag="pre", wrap_attrib="id", wrap_attrib_name="document"):
    """Return an (by default) inline-styled HTML document for the cursor's selection."""
    c = lydocument.cursor(cursor)
    return html(c, scheme, inline, number_lines, full_html, wrap_tag, wrap_attrib, wrap_attrib_name)

def html_document(document, scheme='editor', inline=False, number_lines=False, full_html=True,
        wrap_tag="pre", wrap_attrib="id", wrap_attrib_name="document"):
    """Return a (by default) css-styled HTML document for the full document."""
    c = lydocument.Cursor(lydocument.Document(document))
    return html(c, scheme, inline, number_lines, full_html, wrap_tag, wrap_attrib, wrap_attrib_name)

def html(cursor, scheme='editor', inline=False, number_lines=False, full_html=True,
        wrap_tag="pre", wrap_attrib="id", wrap_attrib_name="document"):
    """Return a HTML document with the syntax-highlighted region.

    The tokens are marked with <span> tags. The cursor is a
    ly.document.Cursor instance. The specified text formats scheme is used
    (by default 'editor'). If inline is True, the span tags have inline
    style attributes. If inline is False, the span tags have class
    attributes and a stylesheet is included.

    Set number_lines to True to add line numbers.

    """
    data = textformats.formatData(scheme)       # the current highlighting scheme
    w = ly.colorize.HtmlWriter()
    w.set_wrapper_tag(wrap_tag)
    w.set_wrapper_attribute(wrap_attrib)
    w.document_id = wrap_attrib_name
    w.inline_style = inline
    w.number_lines = number_lines
    w.full_html = full_html
    w.fgcolor = data.baseColors['text'].name()
    w.bgcolor = data.baseColors['background'].name()
    w.css_scheme = data.css_scheme()
    return w.html(cursor)
