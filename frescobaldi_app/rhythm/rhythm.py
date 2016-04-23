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
Implementation of the tools to edit durations of selected music.

Durations are represented simply by lists of ly.lex.lilypond.Duration tokens.
"""


import itertools

import icons
import inputdialog
import lydocument
import ly.rhythm


_clipboard = [] # clipboard for rhythm copy and paste

_history = set() # earlier rhythms typed in apply dialog


def rhythm_double(cursor):
    ly.rhythm.rhythm_double(lydocument.cursor(cursor))

def rhythm_halve(cursor):
    ly.rhythm.rhythm_halve(lydocument.cursor(cursor))

def rhythm_dot(cursor):
    ly.rhythm.rhythm_dot(lydocument.cursor(cursor))

def rhythm_undot(cursor):
    ly.rhythm.rhythm_undot(lydocument.cursor(cursor))

def rhythm_remove_scaling(cursor):
    ly.rhythm.rhythm_remove_scaling(lydocument.cursor(cursor))

def rhythm_remove_fraction_scaling(cursor):
    ly.rhythm.rhythm_remove_fraction_scaling(lydocument.cursor(cursor))

def rhythm_remove(cursor):
    ly.rhythm.rhythm_remove(lydocument.cursor(cursor))

def rhythm_implicit(cursor):
    ly.rhythm.rhythm_implicit(lydocument.cursor(cursor))

def rhythm_implicit_per_line(cursor):
    ly.rhythm.rhythm_implicit_per_line(lydocument.cursor(cursor))

def rhythm_explicit(cursor):
    ly.rhythm.rhythm_explicit(lydocument.cursor(cursor))

def rhythm_apply(cursor, mainwindow):
    durs = inputdialog.getText(mainwindow,
        _("Apply Rhythm"), _("Enter a rhythm:"),
        complete = sorted(_history),
        regexp = r'([0-9./* ]|\\breve|\\longa|\\maxima)+',
        help = "rhythm", icon = icons.get('tools-rhythm'))
    if not durs:
        return # user cancelled dialog
    durations = durs.split()
    if durations:
        _history.add(durs.strip())
        ly.rhythm.rhythm_overwrite(lydocument.cursor(cursor), durations)

def rhythm_copy(cursor):
    _clipboard[:] = ly.rhythm.rhythm_extract(lydocument.cursor(cursor))

def rhythm_paste(cursor):
    ly.rhythm.rhythm_overwrite(lydocument.cursor(cursor), _clipboard)

