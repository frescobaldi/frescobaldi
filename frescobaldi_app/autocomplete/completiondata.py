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
import ly.grob


# helper functions
def command(item):
    """Prepends '\\' to item."""
    return '\\' + item

def variable(item):
    """Appends ' = ' to item."""
    return item + " = "

def cmd_or_var(item):
    """Appends ' = ' to item if it does not start with '\\'."""
    return item if item.startswith('\\') else item + " = "

def make_cmds(words):
    """Returns generator prepending '\\' to every word."""
    return ('\\' + w for w in words)


# some groups of basic commands

# markup (toplevel, book and bookpart)
markup = (
    'markup',
    'markuplines',
    'pageBreak',
    'noPageBreak',
)

# these can occur (almost) everywhere
everywhere = (
    'language',
    'pointAndClickOn',
    'pointAndClickOff',
    'include',
)

# commands that change input mode, can introduce a music expression
inputmodes = (
    'chords',
    'chordmode {',
    'drums',
    'drummode {',
    'figures',
    'figuremode {',
    'lyrics',
    'lyricmode {',
    'addlyrics {',
)

# commands that only occur at the global file level
toplevel = (
    'version',
    'sourcefileline',
    'sourcefilename',
)

# other commands that can start a music expression
start_music = (
    'repeat',
    'alternative',
    'relative',
    'transpose',
    'partcombine',
    'keepWithTag #\'',
    'removeWithTag #\'',
    'tag #\'',
    'new',
    'context',
    'with',
)

# tweak commands may be assigned, in toplevel
tweaks = (
    'once',
    'override',
    'set',
    'unset',
    'tweak #\'',
)

# modes book, bookpart and score
modes = (
    'book {',
    'bookpart {',
    'score {',
)

# blocks: paper, header, layout
blocks = (
    'paper {',
    'header {',
    'layout {',
)

# commands that are used in context definitions
cmds_context = (
    'override',
    'consists',
    'remove',
    'RemoveEmptyStaves',
    'accepts',
    'alias',
    'defaultchild',
    'denies',
    'name',
)

# in \with { } a smaller set
cmds_with = cmds_context[:3]


lilypond_commands = listmodel.ListModel(
    sorted(ly.words.lilypond_keywords + ly.words.lilypond_music_commands),
    display = command)

lilypond_markup = listmodel.ListModel(['\\markup'])

lilypond_markup_commands = listmodel.ListModel(
    sorted(ly.words.markupcommands),
    display = command)

lilypond_header_variables = listmodel.ListModel(
    sorted(ly.words.headervariables), edit = variable)

lilypond_paper_variables = listmodel.ListModel(
    sorted(ly.words.papervariables), edit = variable)

lilypond_layout_variables = listmodel.ListModel(
    ['\\context {',] + sorted(ly.words.layoutvariables),
    edit = cmd_or_var)

lilypond_contexts = listmodel.ListModel(sorted(ly.words.contexts))

lilypond_grobs = listmodel.ListModel(sorted(ly.words.grobs))

lilypond_contexts_and_grobs = listmodel.ListModel(
    sorted(ly.words.contexts) + sorted(ly.words.grobs))

lilypond_context_contents = listmodel.ListModel(sorted(itertools.chain(
    make_cmds(ly.words.contexts),
    ly.words.contextproperties,
    make_cmds(cmds_context),
    )), edit = cmd_or_var)

lilypond_with_contents = listmodel.ListModel(sorted(itertools.chain(
    ly.words.contextproperties,
    make_cmds(cmds_with),
    )), edit = cmd_or_var)

lilypond_toplevel = listmodel.ListModel(sorted(
    toplevel + everywhere + inputmodes + markup + start_music + tweaks
    + modes + blocks
    ), display = command)

lilypond_book = listmodel.ListModel(sorted(
    everywhere + inputmodes + markup + start_music
    + modes[1:] + blocks + (
    'bookOutputName',
    'bookOutputSuffix',
    )), display = command)

lilypond_bookpart = listmodel.ListModel(sorted(
    everywhere + inputmodes + markup + start_music + modes[2:] + blocks
    ), display = command)
    
lilypond_score = listmodel.ListModel(sorted(
    everywhere + inputmodes + start_music + blocks[1:] + (
    'midi {',
    )), display = command)

lilypond_engravers = listmodel.ListModel(ly.words.engravers)
    
def lilypond_grob_properties(grob):
    return listmodel.ListModel(ly.grob.properties(grob),
        display = lambda item: "#'" + item)


