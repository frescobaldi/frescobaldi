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
The help implementation.

A help page (or 'page') is a class, not an instance. Help pages
are never instantiated.

You should define the title() and body() methods and may define children()
and seealso().

"""

from __future__ import unicode_literals

import re

from PyQt4.QtGui import QAction, QShortcut, QKeySequence


all_pages = {}


class helpmeta(type):
    """Metaclass for the page base class.
    
    Does the following things to the page class:
    - automatically add the page to the all_pages dictionary
    - adds the 'name' attribute and set it to the class name
    - makes the four methods 'title', 'body', 'children' and 'seealso'
      a classmethod if they require one or more arguments, and a staticmethod
      if they require no argument.
    
    """
    def __new__(cls, name, bases, d):
        for n in ('title', 'body', 'children', 'seealso'):
            if n in d:
                if d[n].func_code.co_argcount > 0:
                    d[n] = classmethod(d[n])
                else:
                    d[n] = staticmethod(d[n])
        d['name'] = name
        page = type.__new__(cls, name, bases, d)
        all_pages[name] = page
        return page


class page(object):
    """Base class for help items.
    
    classes based on help are never instantiated; the class is simply used as a
    data container. Some methods should be defined, which are used as classmethod
    if they have an argument, or as staticmethod when they accept no arguments.
    
    The methods may return translated text, when the application changes
    language, the methods are called again.
    
    Set the popup class attribute to True to make the help topic a popup.
    """
    popup = False
    
    @classmethod
    def link(cls):
        return '<a href="help:{0}">{1}</a>'.format(cls.name, cls.title())
    
    def title():
        return ""
    
    def body():
        return ""
    
    def children():
        return ()
    
    def seealso():
        return ()


# This syntax to make 'page' use the metaclass works in both Python2 and 3
page = helpmeta(page.__name__, page.__bases__, dict(page.__dict__))


def html(name):
    """Returns the HTML for the named help item."""
    from . import contents
    import info
    page = all_pages.get(name, contents.nohelp)
    html = []
    html.append('<html><head><title>{0}</title></head><body>'.format(page.title()))
    if page.popup:
        # make this a popup (see QTextBrowser docs)
        html.insert(0, '<qt type=detail>')
        up = () # dont list ancestor pages in popup
    else:
        # show the title(s) of the pages that have us as child
        up = [p for p in all_pages.values() if page in p.children()]
        if up:
            html.append('<p>'+ _("Up:"))
            html.extend(' ' + p.link() for p in up)
            html.append('</p>')
    # body
    html.append('<h2>{0}</h2>'.format(page.title()))
    html.append(markexternal(page.body()))
    # link to child docs
    if page.children():
        html.extend('<div>{0}</div>'.format(p.link()) for p in page.children())
    elif up:
        # give a Next: link if there is a sibling page left
        for p in up:
            i = p.children().index(page)
            if i < len(p.children()) - 1:
                html.append('<div>{0} {1}</div>'.format(
                    _("Next:"), p.children()[i+1].link()))
    # link to "see also" docs
    if page.seealso():
        html.append("<p>{0}</p>".format(_("See also:")))
        html.extend('<div>{0}</div>'.format(p.link()) for p in page.seealso())
    # nice footer
    html.append('<br/><hr width=80%/>')
    html.append('<address><center>{0} {1}</center></address>'.format(info.appname, info.version))
    html.append('</body></html>')
    return ''.join(html)


def markexternal(text):
    """Marks http(s)/ftp(s) links as external with an arrow."""
    pat = re.compile(r'''<a\s+.*?href\s*=\s*(['"])(ht|f)tps?.*?\1[^>]*>''', re.I)
    return pat.sub(r'\g<0>&#11008;', text)


def shortcut(item):
    """Returns a suitable text for the keyboard shortcut of the given item.
    
    Item may be a QAction, a QShortcut, a QKeySequence or a
    QKeySequence.StandardKey.
    
    The text is meant to be used in the help docs.
    
    """
    if isinstance(item, QAction):
        seq = item.shortcut()
    elif isinstance(item, QShortcut):
        seq = item.key()
    elif isinstance(item, QKeySequence.StandardKey):
        seq = QKeySequence(item)
    else:
        seq = item
    return seq.toString(QKeySequence.NativeText) or _("(no key defined)")


def menu(*titles):
    """Returns a nicely formatted list describing a menu option.
    
    e.g.
    
    menu('Edit', 'Preferences')
    
    yields something like:
    
    '<em>Edit-&gt;Preferences</em>'
    
    """
    return '<em>{0}</em>'.format('&#8594;'.join(titles))


