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
lasptygrqu -- The only module in Frescobaldi with an incomprehensible name.

LAnguage-SPecific TYpoGRaphical QUotes.

This modules contains 'single' and "double" opening and closing quotes for many
different languages.
"""

from __future__ import unicode_literals

import collections


QuoteSet = collections.namedtuple("QuoteSet", "single double")
Quotes = collections.namedtuple("Quotes", "left right")

_quotes = {}

_quotes["C"] = \
_quotes["en"] = \
_quotes["nl"] = \
_quotes["tr"] = \
QuoteSet(
    single=Quotes(left="\u2018", right="\u2019"),
    double=Quotes(left="\u201C", right="\u201D"),
)

_quotes["es"] = \
_quotes["fr"] = \
_quotes["gl"] = \
_quotes["it"] = \
QuoteSet(
    single=Quotes(left="\u2039", right="\u203A"),
    double=Quotes(left="\u00AB", right="\u00BB"),
)

_quotes["de"] = \
QuoteSet(
    single=Quotes(left="\u201A", right="\u2018"),
    double=Quotes(left="\u201E", right="\u201C"),
)

_quotes["pl"] = \
QuoteSet(
    single=Quotes(left="\u00AB", right="\u00BB"),
    double=Quotes(left="\u201E", right="\u201D"),
)

_quotes["ru"] = \
_quotes["uk" ] =\
QuoteSet(
    single=Quotes(left="\u201E", right="\u201C"),
    double=Quotes(left="\u00AB", right="\u00BB"),
)

_quotes["pt_BR"] = \
QuoteSet(
    single=Quotes(left="\u201C", right="\u201D"),
    double=Quotes(left="\u00AB", right="\u00BB"),
)

_quotes["zh"] = \
_quotes["ja"] = \
QuoteSet(
    single=Quotes(left="\u300C", right="\u300D"),
    double=Quotes(left="\u300E", right="\u300F"),
)

