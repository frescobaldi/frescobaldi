# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2012 - 2014 by Wilbert Berendsen
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
Provides code folding.

The sidebar/ manages the visibility of the folding area.

"""


import cursortools
import tokeniter
import ly.lex
import widgets.folding


line_painter = widgets.folding.LinePainter()


class Folder(widgets.folding.Folder):
    def fold_events(self, block):
        """Provides folding information by looking at indent/dedent tokens."""
        for t in tokeniter.tokens(block):
            if isinstance(t, (ly.lex.Indent, ly.lex.BlockCommentStart)):
                yield widgets.folding.START
            elif isinstance(t, (ly.lex.Dedent, ly.lex.BlockCommentEnd)):
                yield widgets.folding.STOP

    def mark(self, block, state=None):
        if state is None:
            try:
                return block.userData().folded
            except AttributeError:
                return False
        elif state:
            cursortools.data(block).folded = state
        else:
            try:
                del block.userData().folded
            except AttributeError:
                pass


class FoldingArea(widgets.folding.FoldingArea):
    Folder = Folder



