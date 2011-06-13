# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Templates are basically pieces of text that can be inserted in a text document.
While inserting, special strings, e.g. like {BLABLA} can be expanded.

Built-in templates are in the builtin module, user defined templates are stored
in QSettings.

A template is adressed by a string name, and consists of a text and a title
If there is no title, the text is shown as a title, abridged to one line.

Built-in templates have translated titles.

"""

from __future__ import unicode_literals

import random
import re
import functools
import itertools

import app
from .builtin import templates


# match variables in a '-*- ' line
_variables_re = re.compile(br'\s*?([a-z]+(?:-[a-z]+)*)(?::[ \t]*(.*?))?;')


_names = None   # here is the names list stored
_caches = []    # a list of caches that memoize stuff


def memoize(f):
    """Decorator memoizing stuff for a name until reload is called."""
    cache = {}
    _caches.append(cache)
    @functools.wraps(f)
    def func(name):
        try:
            result = cache[name]
        except KeyError:
            result = cache[name] = f(name)
        return result
    return func


def settings():
    return app.settings("templates")


def names():
    """Returns the set of the names of available templates."""
    global _names
    if _names is None:
        s = settings()
        _names = set(filter(lambda name: not s.value(name+"/deleted"),
                            itertools.chain(templates, s.childGroups())))
    return _names


def reload():
    """Call this when you wrote new templates to the config."""
    global _names
    _names = None
    for cache in _caches:
        cache.clear()


app.languageChanged.connect(reload) # because titles must be translated again


@memoize
def title(name):
    """Returns the title of the specified template or the empty string."""
    s = settings()
    title = s.value(name+"/title")
    if title:
        return title
    try:
        t = templates[name]
    except KeyError:
        pass
    else:
        if t.title:
            return t.title()   # call to translate
    # no title found, send shorttext instead
    return shorttext(name)


@memoize
def text(name):
    """Returns the full template text for the name, or the empty string."""
    text = settings().value(name+"/text")
    if text:
        return text
    try:
        t = templates[name]
    except KeyError:
        return ""
    return t.text


@memoize
def shorttext(name):
    """Returns the abridged text, in most cases usable for display or matching."""
    lines = get(name)[0].splitlines()
    start, end  = 0, len(lines) - 1
    while not lines[start] or lines[start].isspace():
        start += 1
    while end > start and (not lines[end] or lines[end].isspace()):
        end -= 1
    if end == start:
        return lines[start]
    else:
        return lines[start] + " ... " + lines[end]


@memoize
def get(name):
    """Returns a tuple (text, variables) for the specified name.
    
    Equivalent to parse(text(name)). See parse().
    
    """
    return parse(text(name))


def parse(text):
    """Parses a piece of text and returns a tuple (text, variables).
    
    text is the template text, with lines starting with '-*- ' removed.
    variables is a dictionary containing variables read from lines starting
    with '-*- '.
    
    The syntax is as follows:
    
    -*- name: value; name1: value2; (etc)
    
    Names without value are also possible:
    
    -*- name;
    
    In that case the value is set to True.
    
    """
    lines = text.split('\n')
    start = 0
    while start < len(lines) and lines[start].startswith('-*- '):
        start += 1
    t = '\n'.join(lines[start:])
    d = dict(m.groups(True) for l in lines[:start] for m in _variables_re.finditer(l))
    return t, d


def name(names=None):
    """Returns a name to be used for a new template.
    
    If names is specified, it should be a list of strings for which
    the newly returned name is unique.
    
    You must test for uniqueness yourself if you do not give a list of names.
    
    """
    while True:
        u = "n{0:06.0f}".format(random.random()*1000000)
        if not names or u not in names:
            break
    return u


def namegen(names=None):
    """Yields unique names.
    
    If names is specified, it should be a list of strings for which
    the newly returned names are unique.
    
    You must test for uniqueness yourself if you do not give a list of names.
    
    """
    names = list(names) if names is not None else []
    while True:
        n = name(names)
        names.append(n)
        yield n


def save(name, text, title=None):
    """Stores a template."""
    try:
        t = templates[name]
    except KeyError:
        # not builtin
        pass
    else:
        # builtin
        if not title or title == t.title():
            title = None
        if text == t.text:
            text = None
    s = settings()
    if title or text:
        s.beginGroup(name)
        s.setValue("text", text) if text else s.remove("text")
        s.setValue("title", title) if title else s.remove("title")
    else:
        # the template exactly matches the builtin, no saving needed
        s.remove(name)


def delete(name):
    """Deletes a template. For builtins, name/deleted is set to true."""
    s = settings()
    s.remove(name)
    if name in templates:
        s.setValue(name+"/deleted", True)


def deleted():
    """Returns the set of names of builtin templates that are deleted."""
    s = settings()
    return set(filter(lambda name: s.value(name+"/deleted"), templates))


def restore(name):
    """Undeletes or restores the named builtin template to its original state."""
    if name in templates:
        settings().remove(name)


