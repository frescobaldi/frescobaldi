# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2015 - 2015 by Wilbert Berendsen
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
lasptyqu -- The only module in Frescobaldi with an incomprehensible name.

LAnguage-SPecific TYpographical QUotes.

This modules contains 'secondary' and "primary" opening and closing quotes for many
different languages.

Primary quotes are like double quotes in ASCII, and secondary quotes are like
single quotes.

A set of quotes (primary and secondary, left and right) is defined by
a named tuple(primary, secondary). Both the primary and secondary attributes
are also a named tuple(left, right). Use e.g. q.primary.left to get the left
primary quote of a quote set.

The quotes itself are simply unicode strings.

"""


import collections


QuoteSet = collections.namedtuple("QuoteSet", "primary secondary")
Quotes = collections.namedtuple("Quotes", "left right")

_quotes = {}

_quotes["C"] = \
_quotes["en"] = \
_quotes["nl"] = \
_quotes["tr"] = \
QuoteSet(
    primary=Quotes(left="\u201C", right="\u201D"),
    secondary=Quotes(left="\u2018", right="\u2019"),
)

_quotes["es"] = \
_quotes["fr"] = \
_quotes["gl"] = \
_quotes["it"] = \
QuoteSet(
    primary=Quotes(left="\u00AB", right="\u00BB"),
    secondary=Quotes(left="\u2039", right="\u203A"),
)

_quotes["de"] = \
QuoteSet(
    primary=Quotes(left="\u201E", right="\u201C"),
    secondary=Quotes(left="\u201A", right="\u2018"),
)

_quotes["pl"] = \
QuoteSet(
    primary=Quotes(left="\u201E", right="\u201D"),
    secondary=Quotes(left="\u00AB", right="\u00BB"),
)

_quotes["ru"] = \
_quotes["uk"] = \
QuoteSet(
    primary=Quotes(left="\u00AB", right="\u00BB"),
    secondary=Quotes(left="\u201E", right="\u201C"),
)

_quotes["pt_BR"] = \
QuoteSet(
    primary=Quotes(left="\u00AB", right="\u00BB"),
    secondary=Quotes(left="\u201C", right="\u201D"),
)

_quotes["zh"] = \
_quotes["ja"] = \
QuoteSet(
    primary=Quotes(left="\u300E", right="\u300F"),
    secondary=Quotes(left="\u300C", right="\u300D"),
)


def available():
    """Return the list of language codes quotes are defined for."""
    return sorted(_quotes)

def quote_set(primary_left, primary_right, secondary_left, secondary_right):
    """Return a QuoteSet object for the specified four quote character strings.

    This function is not needed normally, but should you ever want to create
    a custom QuoteSet object and access the attributes in the same way as with
    the predefined quote sets, this function can be used.

    """
    return QuoteSet(
        primary=Quotes(primary_left, primary_right),
        secondary=Quotes(secondary_left, secondary_right),
    )

def quotes(language="C"):
    """Return a quotes set for the specified language (default C).

    May return None, in case there are no quotes defined for the language.

    """
    try:
        return _quotes[language]
    except KeyError:
        if '_' in language:
            try:
                return _quotes[language.split("_")[0]]
            except KeyError:
                pass

def default():
    """Return quotes("C")."""
    return _quotes["C"]

def preferred():
    """Return the quotes desired by the Frescobaldi user.

    Always returns a quote set.
    Only this function depends on Qt and Frescobaldi.

    """

    from PyQt5.QtCore import QSettings
    import po.setup

    s = QSettings()
    s.beginGroup("typographical_quotes")
    language = s.value("language", "current", str)

    default = _quotes["C"]
    if language == "current":
        language = po.setup.current()
    elif language == "custom":
        return QuoteSet(
            primary = Quotes(
                left = s.value("primary_left", default.primary.left, str),
                right = s.value("primary_right", default.primary.right, str),
            ),
            secondary = Quotes(
                left = s.value("secondary_left", default.secondary.left, str),
                right = s.value("secondary_right", default.secondary.right, str),
            )
        )
    return quotes(language) or default


