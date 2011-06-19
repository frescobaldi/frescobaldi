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
Acessing the snippets data.
"""

from __future__ import unicode_literals


import functools
import itertools
import random
import re

import app

# cache parsed snippets
_cache = {}

# match variables in a '-*- ' line
_variables_re = re.compile(br'\s*?([a-z]+(?:-[a-z]+)*)(?::[ \t]*(.*?))?;')

# builtin snippets
from .builtin import builtin_snippets


def memoize(f):
    """Decorator memoizing stuff for a name."""
    @functools.wraps(f)
    def func(name):
        try:
            result = _cache[name][f]
        except KeyError:
            result = _cache.setdefault(name, {})[f] = f(name)
        return result
    return func


def unmemoize(f):
    """Decorator forgetting memoized information for a name."""
    @functools.wraps(f)
    def func(name, *args, **kwargs):
        try:
            del _cache[name]
        except KeyError:
            pass
        return f(name, *args, **kwargs)
    return func


def settings():
    return app.settings("snippets")


def names():
    """Yields the names of available builtin snippets."""
    s = settings()
    return set(filter(lambda name: not s.value(name+"/deleted"),
                      itertools.chain(builtin_snippets, s.childGroups())))


def title(name, fallback=True):
    """Returns the title of the specified snippet or the empty string.
    
    If fallback, returns a shortened display of the text if no title is
    available.
    
    """
    s = settings()
    title = s.value(name+"/title")
    if title:
        return title
    try:
        t = builtin_snippets[name]
    except KeyError:
        pass
    else:
        if t.title:
            return t.title()   # call to translate
    if fallback:
        # no title found, send shorttext instead
        return shorttext(name)


def text(name):
    """Returns the full snippet text for the name, or the empty string."""
    text = settings().value(name+"/text")
    if text:
        return text
    try:
        t = builtin_snippets[name]
    except KeyError:
        return ""
    return t.text


@memoize
def shorttext(name):
    """Returns the abridged text, in most cases usable for display or matching."""
    lines = get(name)[0].splitlines()
    if not lines:
        return ''
    start, end  = 0, len(lines) - 1
    while start < end and (not lines[start] or lines[start].isspace()):
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


@unmemoize
def delete(name):
    """Deletes a snippet. For builtins, name/deleted is set to true."""
    s = settings()
    s.remove(name)
    if name in builtin_snippets:
        s.setValue(name+"/deleted", True)


def name(names):
    """Returns a name to be used for a new snippet..
    
    names is a list of strings for which the newly returned name will be unique.
    
    """
    while True:
        u = "n{0:06.0f}".format(random.random()*1000000)
        if u not in names:
            break
    return u


@unmemoize
def save(name, text, title=None):
    """Stores a snippet."""
    try:
        t = builtin_snippets[name]
    except KeyError:
        # not builtin
        pass
    else:
        # builtin
        if not title or (t.title and title == t.title()):
            title = None
        if text == t.text:
            text = None
    s = settings()
    if title or text:
        s.beginGroup(name)
        s.setValue("text", text) if text else s.remove("text")
        s.setValue("title", title) if title else s.remove("title")
    else:
        # the snippet exactly matches the builtin, no saving needed
        s.remove(name)


