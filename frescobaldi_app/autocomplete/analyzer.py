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
Analyze text to determine suitable completions.
"""

from __future__ import unicode_literals

import re

import ly.lex.lilypond
import ly.lex.scheme
import ly.words
import tokeniter

from . import completiondata

__all__ = ['completions']


def completions(cursor):
    """Analyzes text at cursor and returns a tuple (position, model).
    
    The position is an integer specifying the column in the line where the last
    text starts that should be completed.
    
    The model list the possible completions. If the model is None, there are no
    suitable completions.
    
    This function does its best to return extremely meaningful completions
    for the context the cursor is in.
    
    """
    analyzer = Analyzer(cursor)
    return analyzer.column, analyzer.model


class Analyzer(object):
    """This does the analyzing work; sets the attributes column and model."""
    def __init__(self, cursor):
        block = cursor.block()
        self.column = column = cursor.position() - block.position()
        self.text = text = block.text()[:column]
        
        # make a list of tokens exactly ending at the cursor position
        # and let state follow
        state = self.state = tokeniter.state(block)
        tokens = self.tokens = []
        for t in tokeniter.tokens(cursor.block()):
            if t.end > column:
                # cut off the last token and run the parser on it
                tokens.extend(state.tokens(text, t.pos))
                break
            tokens.append(t)
            state.follow(t)
            if t.end == column:
                break
        
        self.last = tokens[-1] if tokens else ''
        self.lastpos = self.last.pos if self.last else column
        
        # DEBUG
        print '================================'
        for t in tokens:
            print '{0} "{1}"'.format(t.__class__.__name__, t)
        print '========parser:', state.parser().__class__
        
        parser = state.parser()
        
        # First, directly map the parser class to a function to return the model
        try:
            function = _states[parser.__class__]
        except KeyError:
            self.model = None
        else:
            self.model = function(self)
            if self.model:
                return
        
        # TODO: try more
        
        # TEMP!!! only complete backslashed commands
        m = re.search(r'\\[a-z]?[A-Za-z]*$', text)
        if m:
            self.column = m.start()
            self.model = completiondata.lilypond_commands


# decorator to map functions to parser class
_states = {}
def state(parserClass):
    def decorator(f):
        _states[parserClass] = f
    return decorator


# markup
@state(ly.lex.lilypond.MarkupParser)
def test(self):
    if (self.last.startswith('\\')
        and self.last[1:] not in ly.words.markupcommands
        and self.last != '\\markup'):
        self.column = self.lastpos
    return completiondata.lilypond_markup_commands
    

# \header {
@state(ly.lex.lilypond.LilyPondParserHeader)
def test(self):
    if '=' in self.tokens[-3:] or self.last.startswith('\\'):
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last[:1].isalpha():
        self.column = self.lastpos
    return completiondata.lilypond_header_variables


# \paper {
@state(ly.lex.lilypond.LilyPondParserPaper)
def test(self):
    if '=' in self.tokens[-3:] or self.last.startswith('\\'):
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last[:1].isalpha():
        self.column = self.lastpos
    return completiondata.lilypond_paper_variables
    

# \layout {
@state(ly.lex.lilypond.LilyPondParserLayout)
def test(self):
    if self.last and not isinstance(self.last, ly.lex.Space):
        self.column = self.lastpos
    return completiondata.lilypond_layout_variables
    

# \layout { \context {
@state(ly.lex.lilypond.LilyPondParserContext)
def test(self):
    if '=' in self.tokens[-3:]:
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last and not isinstance(self.last, ly.lex.Space):
        self.column = self.lastpos
    return completiondata.lilypond_context_contents
    

# \with {
@state(ly.lex.lilypond.LilyPondParserWith)
def test(self):
    if '=' in self.tokens[-3:]:
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last and not isinstance(self.last, ly.lex.Space):
        self.column = lastpos
    return completiondata.lilypond_with_contents
    

# \new or \context in music
@state(ly.lex.lilypond.LilyPondParserNewContext)
def test(self):
    if self.last[:1].isalpha():
        self.column = self.lastpos
        preceding = self.tokens[-3:]
    else:
        preceding = self.tokens[-2:]
    if '\\new' in preceding or '\\context' in preceding:
        return completiondata.lilypond_contexts


# \override
@state(ly.lex.lilypond.LilyPondParserOverride)
def test(self):
    if self.last == '\\override':
        return
    
    tokenclasses = list(map(type, self.tokens))
    grob = ly.lex.lilypond.GrobName in tokenclasses
    prop = grob and ly.lex.lilypond.SchemeStart in tokenclasses
    equalSign = prop and ly.lex.lilypond.EqualSignSetOverride in tokenclasses

    if self.last[:1].isalpha():
        self.column = self.lastpos
    if equalSign:
        # TODO maybe return suitable values for the last property
        return completiondata.lilypond_markup
    if prop:
        return # TODO: maybe drop back at properties
    if grob:
        if tokenclasses[-1] is ly.lex.lilypond.GrobName:
            return completiondata.lilypond_grobs
        else:
            return # TODO: return properties for the grob
    
    if (isinstance(self.state.parsers()[1], (
            ly.lex.lilypond.LilyPondParserWith,
            ly.lex.lilypond.LilyPondParserContext,
            ))
        or ly.lex.lilypond.DotSetOverride in tokenclasses):
        return completiondata.lilypond_grobs
    return completiondata.lilypond_contexts_and_grobs




del test, state


