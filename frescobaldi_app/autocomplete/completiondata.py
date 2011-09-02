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
All completions data.
"""

from __future__ import unicode_literals

import itertools

import listmodel
import ly.words




lilypond_commands = listmodel.ListModel(
    sorted(ly.words.lilypond_keywords + ly.words.lilypond_music_commands),
    display = lambda item: '\\' + item)

lilypond_markup = listmodel.ListModel(['\\markup'])

lilypond_markup_commands = listmodel.ListModel(
    sorted(ly.words.markupcommands),
    display = lambda item: '\\' + item)

lilypond_header_variables = listmodel.ListModel(
    sorted(ly.words.headervariables), edit = lambda item: item + " = ")

lilypond_paper_variables = listmodel.ListModel(
    sorted(ly.words.papervariables), edit = lambda item: item + " = ")

lilypond_layout_variables = listmodel.ListModel(
    ['\\context',] + sorted(ly.words.layoutvariables),
    edit = lambda item: item if item[0] == '\\' else item + " = ")

lilypond_contexts = listmodel.ListModel(sorted(ly.words.contexts))

lilypond_context_contents = listmodel.ListModel(sorted(itertools.chain(
    ('\\' + w for w in ly.words.contexts),
    ly.words.contextproperties,
    ('\\override',),
    )), edit = lambda item: item if item[0] == '\\' else item + " = ")

lilypond_with_contents = listmodel.ListModel(sorted(itertools.chain(
    ly.words.contextproperties,
    ('\\override',),
    )), edit = lambda item: item if item[0] == '\\' else item + " = ")


