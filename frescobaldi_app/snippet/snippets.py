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


import itertools

import app

# builtin snippets
from .builtin import builtin_snippets


def settings():
    return app.settings("snippets")


def names():
    """Yields the names of available builtin snippets."""
    s = settings()
    return set(filter(lambda name: not s.value(name+"/deleted"),
                      itertools.chain(builtin_snippets, s.childGroups())))


def title(name):
    """Returns the title of the specified snippet or the empty string."""
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


