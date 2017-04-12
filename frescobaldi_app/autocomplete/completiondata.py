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
All completions data.
"""


import itertools

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

import listmodel
import ly.words
import ly.data
import ly.pitch

from . import util


# some groups of basic lilypond commands

# markup (toplevel, book and bookpart)
markup = (
    'markup',
    'markuplines',
    'markuplist',
    'pageBreak',
    'noPageBreak',
    'noPageTurn',
)

# these can occur (almost) everywhere
everywhere = (
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
    'defineBarLine',
    'language',
    'version',
    'sourcefileline',
    'sourcefilename',
)

# other commands that can start a music expression
start_music = (
    'repeat',
    'alternative {',
    'relative',
    'transpose',
    'partcombine',
    'keepWithTag #\'',
    'removeWithTag #\'',
    'new',
    'context',
    'with',
)

# tweak commands may be assigned, in toplevel
tweaks = (
    'once',
    'override',
    'revert',
    'set',
    'unset',
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


# variables that make sense to be set at toplevel
toplevel_variables = (
    'pipeSymbol',
    'showFirstLength',
    'showLastLength',
)


# stuff inside \score {}
score = sorted(
    everywhere + inputmodes + start_music + blocks[1:] + (
    'midi {',
))


# stuff inside \bookpart {}
bookpart = sorted(
    everywhere + inputmodes + markup + start_music + modes[2:] + blocks
)


# stuff inside \book {}
book = sorted(
    everywhere + inputmodes + markup + start_music
    + modes[1:] + blocks + (
    'bookOutputName',
    'bookOutputSuffix',
))


lilypond_markup = listmodel.ListModel(['\\markup'])

lilypond_markup_commands = listmodel.ListModel(
    sorted(ly.words.markupcommands),
    display = util.command)

lilypond_header_variables = listmodel.ListModel(
    sorted(ly.words.headervariables, key=lambda i: i[:3]), edit = util.variable)

lilypond_paper_variables = listmodel.ListModel(
    sorted(ly.words.papervariables), edit = util.variable)

lilypond_layout_variables = listmodel.ListModel([
        '\\context {',
        '\\override',
        '\\set',
        '\\hide',
        '\\omit',
        '\\accidentalStyle',
        ] + sorted(ly.words.layoutvariables),
    edit = util.cmd_or_var)

lilypond_midi_variables = listmodel.ListModel(
    ['\\context {', '\\override', '\\set', '\\tempo',] +
    sorted(ly.words.midivariables),
    edit = util.cmd_or_var)

lilypond_contexts = listmodel.ListModel(sorted(ly.words.contexts))

lilypond_grobs = listmodel.ListModel(ly.data.grobs())

lilypond_contexts_and_grobs = listmodel.ListModel(
    sorted(ly.words.contexts) + ly.data.grobs())

lilypond_context_properties = listmodel.ListModel(
    ly.data.context_properties())

lilypond_contexts_and_properties = listmodel.ListModel(
    sorted(ly.words.contexts) + ly.data.context_properties())

lilypond_context_contents = listmodel.ListModel(sorted(itertools.chain(
    util.make_cmds(ly.words.contexts),
    ly.data.context_properties(),
    util.make_cmds(cmds_context),
    )), edit = util.cmd_or_var)

lilypond_with_contents = listmodel.ListModel(sorted(itertools.chain(
    ly.data.context_properties(),
    util.make_cmds(cmds_with),
    )), edit = util.cmd_or_var)

lilypond_toplevel = listmodel.ListModel(sorted(itertools.chain(util.make_cmds(
    toplevel + everywhere + inputmodes + markup + start_music + tweaks
    + modes + blocks
    ), toplevel_variables)), edit = util.cmd_or_var)

lilypond_book = listmodel.ListModel(book, display = util.command)

lilypond_bookpart = listmodel.ListModel(bookpart, display = util.command)

lilypond_score = listmodel.ListModel(score, display = util.command)

lilypond_engravers = listmodel.ListModel(ly.data.engravers())

def lilypond_grob_properties(grob, hash_quote=True):
    display = (lambda item: "#'" + item) if hash_quote else (lambda item: item)
    return listmodel.ListModel(ly.data.grob_properties(grob),
        display = display)

lilypond_all_grob_properties = listmodel.ListModel(ly.data.all_grob_properties(),
    display = lambda item: "#'" + item)

lilypond_all_grob_properties_and_grob_names = listmodel.ListModel(
    ly.data.all_grob_properties() + ly.data.grobs())

lilypond_markup_properties = listmodel.ListModel(
    sorted(set(sum(map(ly.data.grob_interface_properties, (
        # see lilypond docs about \markup \override
        'font-interface',
        'text-interface',
        'instrument-specific-markup-interface',
    )), []))))

lilypond_modes = listmodel.ListModel(ly.words.modes, display = util.command)

lilypond_clefs = listmodel.ListModel(ly.words.clefs_plain)

lilypond_accidental_styles = listmodel.ListModel(ly.words.accidentalstyles)

lilypond_accidental_styles_contexts = listmodel.ListModel(
    ly.words.contexts + ly.words.accidentalstyles)

lilypond_repeat_types = listmodel.ListModel(ly.words.repeat_types)

music_glyphs = listmodel.ListModel(ly.data.music_glyphs())

midi_instruments = listmodel.ListModel(ly.words.midi_instruments)

language_names = listmodel.ListModel(sorted(ly.pitch.pitchInfo))

def font_names():
    model = listmodel.ListModel(sorted(QFontDatabase().families()))
    model.setRoleFunction(Qt.FontRole, QFont)
    return model

