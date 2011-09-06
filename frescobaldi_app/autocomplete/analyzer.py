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

import ly.lex as lx
import ly.lex.lilypond as lp
import ly.lex.scheme as scm
import ly.words
import tokeniter

from . import completiondata
from . import documentdata


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
        self.cursor = cursor
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
            print '{0} "{1}"'.format(t.__class__, t)
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

    def tokenclasses(self):
        """Returns the list of classes of the tokens."""
        return list(map(type, self.tokens))


# decorator to map functions to parser class(es)
_states = {}
def state(*parserClasses):
    def decorator(f):
        for c in parserClasses:
            _states[c] = f
    return decorator


# global toplevel
@state(lp.LilyPondParserGlobal)
def test(self):
    if not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    return completiondata.lilypond_toplevel
    # maybe: check if behind \version or \language


# \book {
@state(lp.LilyPondParserBook)
def test(self):
    if not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    return completiondata.lilypond_book


# \bookpart {
@state(lp.LilyPondParserBookPart)
def test(self):
    if not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    return completiondata.lilypond_bookpart


# \score {
@state(lp.LilyPondParserScore)
def test(self):
    if not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    return completiondata.lilypond_score


# general music
@state(lp.LilyPondParserMusic, lp.LilyPondParserNoteMode)
def test(self):
    tokenclasses = self.tokenclasses()
    # at end of scheme word?
    if isinstance(self.last, scm.Word):
        if ('\\tweak' in self.tokens[-5:-4]
            and self.text[:self.lastpos].endswith("#'")):
            # complete \tweak property
            self.column = self.lastpos - 2
            return completiondata.lilypond_all_grob_properties
        # complete scheme word
        self.column = self.lastpos
        return documentdata.doc(self.cursor.document()).schemewords()
    # complete mode argument of '\\key'
    if '\\key' in self.tokens[-5:-2] and lp.Note in tokenclasses[-3:]:
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_modes
    # fall back: generic music commands
    if not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    return completiondata.lilypond_commands


# \markup
@state(lp.MarkupParser)
def test(self):
    if self.last.startswith('\\'):
        if (self.last[1:] not in ly.words.markupcommands
            and self.last != '\\markup'):
            self.column = self.lastpos
        else:
            return completiondata.lilypond_markup_commands
    else:
        m = re.search(r'\w+$', self.last)
        if m:
            self.column = self.lastpos + m.start()
    return documentdata.doc(self.cursor.document()).markup()
    

# \header {
@state(lp.LilyPondParserHeader)
def test(self):
    if '=' in self.tokens[-3:] or self.last.startswith('\\'):
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last[:1].isalpha():
        self.column = self.lastpos
    return completiondata.lilypond_header_variables


# \paper {
@state(lp.LilyPondParserPaper)
def test(self):
    if '=' in self.tokens[-3:] or self.last.startswith('\\'):
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last[:1].isalpha():
        self.column = self.lastpos
    return completiondata.lilypond_paper_variables
    

# \layout {
@state(lp.LilyPondParserLayout)
def test(self):
    if self.last and not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    return completiondata.lilypond_layout_variables
    

# \layout { \context {
@state(lp.LilyPondParserContext)
def test(self):
    return test_context_with(self) or completiondata.lilypond_context_contents
    

# \with {
@state(lp.LilyPondParserWith)
def test(self):
    return test_context_with(self) or completiondata.lilypond_with_contents
    

# shared analyzer for \context { } and \with { }
def test_context_with(self):
    if '\\remove' in self.tokens[-3:-1] or '\\consists' in self.tokens[-3:-1]:
        if not isinstance(self.last, lx.Space):
            self.column = self.lastpos
        return completiondata.lilypond_engravers
    if '=' in self.tokens[-4:]:
        if isinstance(self.last, scm.Word):
            self.column = self.lastpos
            return documentdata.doc(self.cursor.document()).schemewords()
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last and not isinstance(self.last, lx.Space):
        self.column = self.lastpos
    

# \new or \context in music
@state(lp.LilyPondParserNewContext)
def test(self):
    if self.last[:1].isalpha():
        self.column = self.lastpos
        preceding = self.tokens[-3:]
    else:
        preceding = self.tokens[-2:]
    if '\\new' in preceding or '\\context' in preceding:
        return completiondata.lilypond_contexts


# \override
@state(lp.LilyPondParserOverride, lp.LilyPondParserRevert)
def test(self):
    if self.last in ('\\override', '\\revert'):
        return
    
    tokenclasses = self.tokenclasses()
    grob = lp.GrobName in tokenclasses
    prop = grob and lp.SchemeStart in tokenclasses
    equalSign = prop and lp.EqualSignSetOverride in tokenclasses

    if self.last[:1].isalpha():
        self.column = self.lastpos
    if equalSign:
        # TODO maybe return suitable values for the last property
        return completiondata.lilypond_markup
    if grob:
        if tokenclasses[-1] is lp.GrobName:
            return completiondata.lilypond_grobs
        elif lp.GrobName in tokenclasses[-2:-1]:
            # return properties for the grob
            return completiondata.lilypond_grob_properties(self.tokens[-2])
        elif tokenclasses[-5:] == [
            lp.GrobName, lx.Space, lp.SchemeStart, scm.Quote, scm.Word]:
            self.column = self.lastpos - 2
            return completiondata.lilypond_grob_properties(self.tokens[-5])
    if (isinstance(self.state.parsers()[1], (
            lp.LilyPondParserWith,
            lp.LilyPondParserContext,
            ))
        or lp.DotSetOverride in tokenclasses):
        return completiondata.lilypond_grobs
    return completiondata.lilypond_contexts_and_grobs


# \set
@state(lp.LilyPondParserSet, lp.LilyPondParserUnset)
def test(self):
    tokenclasses = self.tokenclasses()
    if not isinstance(self.last, (lx.Space, lp.DotSetOverride)):
        self.column = self.lastpos
    if lp.EqualSignSetOverride in tokenclasses:
        # TODO maybe return suitable values for the context property
        return completiondata.lilypond_markup
    elif lp.ContextProperty in tokenclasses and isinstance(self.last, lx.Space):
        return # fall back to music?
    elif lp.DotSetOverride in tokenclasses:
        return completiondata.lilypond_context_properties
    return completiondata.lilypond_contexts_and_properties


# string in lilypond
@state(lp.StringParser)
def test(self):
    if '"' not in self.tokens[-2:]:
        return
    elif self.last != '"':
        self.column = self.lastpos
    if '\\remove' in self.tokens or '\\consists' in self.tokens:
        return completiondata.lilypond_engravers
    

# scheme, various stuff
@state(scm.SchemeParser)
def test(self):
    tokenclasses = self.tokenclasses()
    
    # test for properties after a grob name in \override or \revert
    test = [lp.GrobName, lx.Space, lp.SchemeStart, scm.Quote]
    if tokenclasses[-3:] == test[:-1]:
        self.column -= 1
        return completiondata.lilypond_grob_properties(self.tokens[-3])
    elif tokenclasses[-4:] == test:
        self.column -= 2
        return completiondata.lilypond_grob_properties(self.tokens[-4])
    
    # test for property after \tweak
    if '\\tweak' in self.tokens:
        test = [lp.Command, lx.Space, lp.SchemeStart, scm.Quote]
        if tokenclasses[-3:] == test[:-1]:
            self.column -= 1
            return completiondata.lilypond_all_grob_properties
        elif tokenclasses[-4:] == test:
            self.column -= 2
            return completiondata.lilypond_all_grob_properties
    
    # test for \markup \override
    if '\\override' in self.tokens:
        if isinstance(self.last, scm.Word):
            clss = tokenclasses[:-1]
            column = self.lastpos
        else:
            clss = tokenclasses
            column = self.column
        if clss[-5:] == [
            lp.MarkupCommand,
            lx.Space,
            lp.SchemeStart,
            scm.Quote,
            scm.OpenParen]:
            self.column = column
            return completiondata.lilypond_markup_properties
    
    # test for other scheme words
    if isinstance(self.last, (
        lp.SchemeStart,
        scm.OpenParen,
        scm.Word,
        )):
        if isinstance(self.last, scm.Word):
            self.column = self.lastpos
        return documentdata.doc(self.cursor.document()).schemewords()





del test, state


