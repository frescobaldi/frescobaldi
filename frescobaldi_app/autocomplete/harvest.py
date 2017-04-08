# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Harvest strings from document for autocompletion purposes.
"""


import itertools
import re

import documentinfo
import fileinfo
import tokeniter
import ly.lex.lilypond
import ly.lex.scheme


def get_docinfo(cursor):
    """Return a ly DocInfo instance for the cursor's document up to its position."""
    dinfo = documentinfo.info(cursor.document())
    return dinfo.lydocinfo().range(0, cursor.position())


def names(cursor):
    """Harvests names from assignments until the cursor."""
    return get_docinfo(cursor).definitions()


def markup_commands(cursor):
    """Harvest markup command definitions until the cursor."""
    return get_docinfo(cursor).markup_definitions()


def schemewords(document):
    """Harvests all schemewords from the document."""
    for t in tokeniter.all_tokens(document):
        if type(t) is ly.lex.scheme.Word:
            yield t


def include_identifiers(cursor):
    """Harvests identifier definitions from included files."""
    dinfo = documentinfo.info(cursor.document())
    files = fileinfo.includefiles(get_docinfo(cursor), dinfo.includepath())
    return itertools.chain.from_iterable(fileinfo.docinfo(f).definitions()
                                         for f in files)


def include_markup_commands(cursor):
    """Harvest markup command definitions from included files."""
    dinfo = documentinfo.info(cursor.document())
    files = fileinfo.includefiles(get_docinfo(cursor), dinfo.includepath())
    return itertools.chain.from_iterable(fileinfo.docinfo(f).markup_definitions()
                                         for f in files)


_words = re.compile(r'\w{5,}|\w{2,}(?:[:-]\w+)+').finditer
_word_types = (
    ly.lex.String, ly.lex.Comment, ly.lex.Unparsed,
    ly.lex.lilypond.MarkupWord, ly.lex.lilypond.LyricText)

def words(document):
    """Harvests words from strings, lyrics, markup and comments."""
    for t in tokeniter.all_tokens(document):
        if isinstance(t, _word_types):
            for m in _words(t):
                yield m.group()

