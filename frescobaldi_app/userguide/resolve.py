# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
These functions return values for python format variables in user guide pages.

Some generic functions are called by several pages, but there are also some
special, auto-generated parts of text that are used in a specific user
guide page.

"""


import appinfo


def appname():
    return appinfo.appname

def version():
    return appinfo.version

def author():
    return appinfo.maintainer

def manual_translated_by():
    # L10N: Translate this sentence and fill in your own name to have it appear in the About Dialog.
    translator = _("Translated by Your Name.")
    if translator != "Translated by Your Name.":
        return translator
    return ''

def table_of_contents():
    """Return the body of the table of contents page."""
    from .util import cache, format_link
    from simplemarkdown import html_escape
    html = ['<ul>']
    seen = set()
    def addpage(page):
        if page not in seen:
            seen.add(page)
            html.append("<li>" + format_link(page) + "</li>\n")
            children = cache.children(page)
            if children:
                html.append('<ul>')
                for p in children:
                    addpage(p)
                html.append('</ul>\n')
    for page in cache.children('index'):
        addpage(page)
    html.append('</ul>\n')
    return ''.join(html)

def snippet_editor_expander():
    """Return the auto-generated list of docstrings of the snippet variables."""
    from snippet import expand
    text = []
    text.append("<dl>")
    text.extend(map("<dt><code>${0[0]}</code></dt><dd>{0[1]}</dd>".format,
                    expand.documentation(expand.Expander)))
    text.append("</dl>")
    return ''.join(text)

