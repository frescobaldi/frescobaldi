# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
Page, a page from the Frescobaldi User Manual.
"""

from __future__ import unicode_literals

import re

from PyQt4.QtGui import QKeySequence

import simplemarkdown

from . import read
from . import resolve


class Page(object):
    def __init__(self, name=None):
        self._attrs = {}
        self._title = None
        self._body = None
        self._name = None
        if name:
            self.load(name)
    
    def load(self, name):
        """Parse and translate the named document."""
        self._name = name
        doc, attrs = read.document(name)
        self.parse_text(doc, attrs)
        
    def parse_text(self, text, attrs=None):
        """Parse and translate the document."""
        self._attrs = attrs or {}
        t = self._tree = simplemarkdown.Tree()
        read.Parser().parse(text, t)
    
    def is_popup(self):
        """Return True if the helppage should be displayed as a popup."""
        try:
            return 'popup' in self._attrs['PROPERTIES']
        except KeyError:
            return False
    
    def title(self):
        """Return the title"""
        if self._title is None:
            self._title = "No Title"
            for heading in self._tree.find('heading'):
                self._title = self._tree.text(heading)
                break
        return self._title
    
    def body(self):
        """Return the HTML body."""
        if self._body is None:
            output = HtmlOutput()
            output.resolver = Resolver(self._attrs.get('VARS'))
            self._tree.copy(output)
            html = output.html()
            # remove empty paragraphs (could result from optional text)
            html = html.replace('<p></p>', '')
            self._body = html
        return self._body
        
    def children(self):
        """Return the list of names of child documents."""
        return self._attrs.get("SUBDOCS") or []
    
    def seealso(self):
        """Return the list of names of "see also" documents."""
        return self._attrs.get("SEEALSO") or []
    
    _template = '''\
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


    def html(self):
        """Return the full userguide page HTML."""
        from info import appname, version
        
        def format_link(name):
            title = simplemarkdown.html_escape(Page(name).title())
            return '<a href="{0}">{1}</a>'.format(name, title)
        
        parents = []
        if self._name:
            pass # TODO get the parents
        
        qt_detail = '<qt type=detail>' if self.is_popup() else ''
        title = self.title()
        nav_up = ''
        if parents and not self.is_popup():
            nav_up = '<p>{0} {1}</p>'.format(
                _("Up:"),
                ' '.join(map(format_link, parents)))
        body = self.markexternal(self.body())
        nav_children, nav_next, nav_seealso = '', '', ''
        if self.children():
            nav_children = '\n'.join(
                '<div>{0}</div>'.format(format_link(p))
                for p in self.children())
        elif self._name:
            html = []
            for p in parents:
                i = p.children().index(page)
                if i < len(p.children()) - 1:
                    html.append('<div>{0} {1}</div>'.format(
                        _("Next:"), p.children()[i+1].link()))
            nav_next = '\n'.join(html)
        if self.seealso():
            html = []
            html.append("<p>{0}</p>".format(_("See also:")))
            html.extend('<div>{0}</div>'.format(format_link(p))
                        for p in self.seealso())
            nav_seealso = '\n'.join(html)
        return self._template.format(**locals())

    def markexternal(self, text):
        """Marks http(s)/ftp(s) links as external with an arrow."""
        pat = re.compile(r'''<a\s+.*?href\s*=\s*(['"])(ht|f)tps?.*?\1[^>]*>''', re.I)
        return pat.sub(r'\g<0>&#11008;', text)


class HtmlOutput(simplemarkdown.HtmlOutput):
    """Colorizes LilyPond source and replaces {variables}.
    
    Put a Resolver instance in the resolver attribute before populating
    the output.
    
    """
    def code_start(self, code, specifier=None):
        if specifier == "lilypond":
            import colorize
            self._html.append(colorize.colorize(code))
        else:
            self.tag('code')
            self.tag('pre')
            self.text(code)
    
    def code_end(self, code, specifier=None):
        if specifier != "lilypond":
            self.tag('/pre')
            self.tag('/code')
        self.nl()
    
    def inline_text_start(self, text):
        text = self.html_escape(text)
        text = self.resolver.format(text)   # replace {variables} ...
        self._html.append(text)


class Resolver(object):
    """Resolves variables in help documents."""
    
    _rx = re.compile(r"\{([a-z]+(_[a-z]+)*)\}", re.UNICODE)
    
    def __init__(self, variables=None):
        """Initialize with a list of variables from the #VARS section.
        
        Every item is simply a line, where the first word is the name,
        the second the type and the rest is the contents.
        
        """
        self._variables = d = {}
        if variables:
            for v in variables:
                try:
                    name, type, text = v.split(None, 2)
                except ValueError:
                    continue
                d[name] = (type, text)
    
    def format(self, text):
        """Replaces all {variable} items in the text."""
        return self._rx.sub(self.replace, text)
        
    def replace(self, matchObj):
        """Return the replace string for the match.
        
        For a match like {blabla}, self.resolve('blabla') is called, and if
        the result is not None, '{blabla}' is replaced with the result.
        
        """
        result = self.resolve(matchObj.group(1))
        return matchObj.group() if result is None else result
    
    def resolve(self, name):
        """Try to find the value for the named variable.
        
        First, the #VARS section is searched. If that yields no result,
        the named function in the resolve module is called. If that yields
        no result either, None is returned.
        
        """
        
        try:
            typ, text = self._variables[name]
        except KeyError:
            try:
                return getattr(resolve, name)()
            except AttributeError:
                return
        try:
            method = getattr(self, 'handle_' + typ.lower())
        except AttributeError:
            method = self.handle_text
        return method(text)

    def handle_md(self, text):
        """Convert inline markdown to HTML."""
        return simplemarkdown.html_inline(text)

    def handle_html(self, text):
        """Return text as is, it may contain HTML."""
        return text
    
    def handle_text(self, text):
        """Return text escaped, it will not be represented as HTML."""
        return simplemarkdown.html_escape(text)

    def handle_url(self, text):
        """Return a clickable url."""
        url = text
        if text.startswith('http://'):
            text = text[7:]
        if text.endswith('/'):
            text = text[:-1]
        url = simplemarkdown.html_escape(url).replace('"', '&quot;')
        text = simplemarkdown.html_escape(text)
        return '<a href="{0}">{1}</a>'.format(url, text)

    def handle_help(self, text):
        """Return a link to the specified help page, with the title."""
        try:
            title = Page(text).title()
        except (OSError, IOError):
            title = text
        url = text
        return '<a href="{0}">{1}</a>'.format(url, title)

    def handle_shortcut(self, text):
        """Return the keystroke currently defined for the action."""
        collection_name, action_name = text.split(None, 1)
        import actioncollectionmanager
        mgr = actioncollectionmanager.ActionCollectionManager.instances()[0]
        seq = mgr.action(collection_name, action_name).shortcut()
        key = seq.toString(QKeySequence.NativeText) or _("(no key defined)")
        return '<span class="shortcut">{0}</span>'.format(simplemarkdown.html_escape(key))

    def handle_image(self, filename):
        url = simplemarkdown.html_escape(filename).replace('"', '&quot;')
        return '<img src="{0}" alt="{0}"/>'.format(url)


