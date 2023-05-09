# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2011 - 2015 by Wilbert Berendsen
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
Implementation of tools to edit rests of selected music.

All functions except a ly.document.Cursor with the selected range.

"""

from __future__ import unicode_literals

import ly.document
import ly.lex.lilypond

def replace_rest(cursor, replace_token):
    """Replace full rests (r) with optional token. """
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for token in source:
            if isinstance(token, ly.lex.lilypond.Rest):
                if token == 'r':
                    d[token.pos:token.end] = replace_token

def replace_fmrest(cursor, replace_token):
    """Replace full measure rests (R) with optional token. """
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for token in source:
            if isinstance(token, ly.lex.lilypond.Rest):
                if token == 'R':
                    d[token.pos:token.end] = replace_token

def replace_spacer(cursor, replace_token):
    """Replace spacer rests (s) with optional token. """
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for token in source:
            if isinstance(token, ly.lex.lilypond.Spacer):
                d[token.pos:token.end] = replace_token

def replace_restcomm(cursor, replace_token):
    r"""Replace rests by rest command (\rest) with optional token. """

    def get_comm_rests(source):
        r"""Catch all rests by rest command (\rest) from source."""
        rest_tokens = None
        for token in source:
            if isinstance(token, ly.lex.lilypond.Note):
                rest_tokens = [token]
                continue
            if rest_tokens and isinstance(token, ly.lex.Space):
                rest_tokens.append(token)
                continue
            if rest_tokens and isinstance(token, ly.lex.lilypond.Command):
                if token == '\\rest':
                    rest_tokens.append(token)
                    yield rest_tokens
                    rest_tokens = None
                    
    source = ly.document.Source(cursor, True, tokens_with_position=True)
    with cursor.document as d:
        for rt in get_comm_rests(source):
            note = rt[0]
            space = rt[-2]
            comm = rt[-1]
            d[note.pos:note.end] = replace_token
            del d[space.pos:space.end]
            del d[comm.pos:comm.end]

