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

import functools
import itertools

import app
from .builtin import templates


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
        _names = set(filter(lambda name: s.value(name+"/deleted"),
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
    t = text(name)
    lines = t.splitlines()
    if len(lines) < 2:
        return t
    usable = lambda line: line and not (line.startswith('-*- ') or line.isspace())
    first, last = 0, len(lines) - 1
    while not usable(lines[first]):
        first += 1
    while last > first and not usable(lines[last]):
        last -= 1
    if last == first:
        return lines[first]
    else:
        return lines[first] + " ... " + lines[last]


