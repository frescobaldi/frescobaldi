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

import textformats
import lydocument
import ly.colorize

def html_inline(cursor, scheme='editor'):
    c = lydocument.cursor(cursor)
    data = textformats.formatData(scheme)       # the current highlighting scheme
    mapping = ly.colorize.css_mapping()         # map the token class to hl class
    formatter = ly.colorize.css_style_attribute_formatter(data.css_scheme()) # inline html
    body = '<pre style="color: {0}; background: {1}">{2}</pre>\n'.format(
        data.baseColors['text'].name(),
        data.baseColors['background'].name(),
        ly.colorize.html(c, mapping, formatter))
    return ly.colorize.format_html_document(body)

def html_document(document, scheme='editor'):
    c = lydocument.Cursor(lydocument.Document(document))
    data = textformats.formatData(scheme)       # the current highlighting scheme
    mapping = ly.colorize.css_mapping()         # map the token class to hl class
    formatter = ly.colorize.format_css_span_class # css-styled html
    css = 'pre {{\n  color: {0};\n  background: {1}\n}}\n\n{2}'.format(
        data.baseColors['text'].name(),
        data.baseColors['background'].name(),
        ly.colorize.format_stylesheet(data.css_scheme()))
    body = '<pre>{0}</pre>\n'.format(ly.colorize.html(c, mapping, formatter))
    return ly.colorize.format_html_document(body, stylesheet=css)

