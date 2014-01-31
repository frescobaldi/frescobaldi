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
Colorize a string as HTML.
"""

from __future__ import unicode_literals

__all__ = ['colorize']


def colorize(text, mode=None):
    """Converts the text to HTML using the specified or guessed mode."""
    import textformats
    import ly.document
    import ly.colorize
    c = ly.document.Cursor(ly.document.Document(text, mode))
    data = textformats.formatData('editor')     # the current highlighting scheme
    mapping = ly.colorize.css_mapping()         # map the token class to hl class
    formatter = ly.colorize.css_style_attribute_formatter(data.css_scheme()) # inline html
    body = '<pre style="color: {0}; background: {1}">{2}</pre>\n'.format(
        data.baseColors['text'].name(),
        data.baseColors['background'].name(),
        ly.colorize.html(c, mapping, formatter))
    return ly.colorize.format_html_document(body)

