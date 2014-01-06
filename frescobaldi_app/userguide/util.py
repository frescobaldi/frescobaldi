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
Utility functions for the user guide.
"""

from __future__ import unicode_literals

import re

import app
import simplemarkdown

from .page import Page


class Formatter(object):
    """Format a full userguide page HTML."""
    def html(self, name):
        """Return a full userguide page HTML."""
        page = Page(name)
        from info import appname, version
        
        parents = cache.parents(name) if name != 'index' else []
        children = cache.children(name)
        
        qt_detail = '<qt type=detail>' if page.is_popup() else ''
        title = page.title()
        nav_up = ''
        if parents and not page.is_popup():
            pp = parents
            links = []
            while pp:
                p = pp[0]
                links.append(p)
                pp = cache.parents(p)
            nav_up = '<p>{0} {1}</p>'.format(
                _("Up:"),
                ' &#8594; '.join(map(self.format_link, reversed(links))))
        body = self.markexternal(page.body())
        nav_children, nav_next, nav_seealso = '', '', ''
        if children:
            nav_children = '<p>{0}</p>\n<ul>{1}</ul>'.format(
                _("In this chapter:"),
                '\n'.join('<li>{0}</li>'.format(self.format_link(c))
                for c in children))
        else:
            html = []
            for p in parents:
                c = cache.children(p)
                i = c.index(name)
                if i < len(c) - 1:
                    html.append('<div>{0} {1}</div>'.format(
                        _("Next:"), self.format_link(c[i+1])))
            nav_next = '\n'.join(html)
        if page.seealso():
            nav_seealso = "<p>{0} {1}</p>".format(
                _("See also:"),
                ', '.join(map(self.format_link, page.seealso())))
        return self._html_template().format(**locals())

    def format_link(self, name):
        """Make a clickable link to the page."""
        return format_link(name)
    
    def markexternal(self, text):
        """Marks http(s)/ftp(s) links as external with an arrow."""
        return markexternal(text)
    
    def _html_template(self):
        """Return the userguide html template to render the html().
        
        The default implementation returns _userguide_html_template.
        
        """
        return _userguide_html_template


def format_link(name):
    """Make a clickable link to the page."""
    title = simplemarkdown.html_escape(cache.title(name))
    return '<a href="{0}">{1}</a>'.format(name, title)

def markexternal(text):
    """Marks http(s)/ftp(s) links as external with an arrow."""
    pat = re.compile(r'''<a\s+.*?href\s*=\s*(['"])(ht|f)tps?.*?\1[^>]*>''', re.I)
    return pat.sub(r'\g<0>&#11008;', text)


_userguide_html_template = '''\
{qt_detail}<html>
<head>
<style type="text/css">
body {{
  margin: 10px;
}}
</style>
<title>{title}</title>
</head>
<body>
{nav_up}
{body}
{nav_children}
{nav_next}
{nav_seealso}
<br/><hr width=80%/>
<address><center>{appname} {version}</center></address>
</body>
</html>
'''


class Cache(object):
    """Cache certain information about pages.
    
    Just one instance of this is created and put in the cache global.
    
    """
    def __init__(self):
        self._title = {}
        self._children = {}
        app.languageChanged.connect(lambda: self._title.clear(), -999)
    
    def title(self, name):
        """Return the title of the named page."""
        try:
            t = self._title[name]
        except KeyError:
            t = self._title[name] = Page(name).title()
        return t
    
    def children(self, name):
        """Return the list of children of the named page."""
        try:
            c = self._children[name]
        except KeyError:
            c = self._children[name] = Page(name).children()
        return c
        
    def parents(self, name):
        """Return the list of parents (zero or more) of the named page."""
        try:
            self._parents
        except AttributeError:
            self._parents = {}
            self._compute_parents()
        try:
            return self._parents[name]
        except KeyError:
            return []
    
    def _compute_parents(self):
        def _compute(n1):
            for n in self.children(n1):
                self._parents.setdefault(n, []).append(n1)
                _compute(n)
        _compute('index')


# one global Cache instance
cache = Cache()

