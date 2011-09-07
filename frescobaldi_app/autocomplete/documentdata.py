# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 by Wilbert Berendsen
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
Completions data harvested from a Document.
"""

from __future__ import unicode_literals

import itertools

import listmodel
import plugin
import ly.words

from . import harvest
from . import util


def doc(document):
    """Returns the DocumentDataSource for the specified Document."""
    return DocumentDataSource.instance(document)


class DocumentDataSource(plugin.DocumentPlugin):
    @util.keep
    def words(self):
        """Returns the list of words in comments, markup etc."""
        return listmodel.ListModel(
            sorted(set(harvest.words(self.document()))))

    @util.keep
    def schemewords(self):
        """Scheme names, including those harvested from document."""
        schemewords = set(itertools.chain(
            ly.words.scheme_functions,
            ('LEFT', 'UP', 'RIGHT', 'DOWN'),
            (unicode(t)
                for t in harvest.schemewords(self.document())
                if len(t) > 2),
            ))
        return listmodel.ListModel(sorted(schemewords))

    @util.keep
    def markup(self):
        """Completes markup commands and normal text from the document."""
        return listmodel.ListModel(
            ['\\' + w for w in ly.words.markupcommands]
            + sorted(set(harvest.words(self.document()))))

    @util.keep
    def musiccommands(self, cursor):
        return listmodel.ListModel(sorted(set(itertools.chain(
            ly.words.lilypond_keywords,
            ly.words.lilypond_music_commands,
            harvest.names(cursor)))), display = util.command)



