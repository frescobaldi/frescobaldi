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
        self.model = None
        
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
            print '{0} {1}'.format(t.__class__, repr(t))
        print '========parser:', state.parser().__class__
        
        parser = state.parser()
        
        # Map the parser class to a group of tests to return the model.
        # Try the tests until a model is returned.
        try:
            tests = _tests[parser.__class__]
        except KeyError:
            return
        else:
            for function in tests:
                model = function(self)
                if model:
                    self.model = model
                    return

    def tokenclasses(self):
        """Returns the list of classes of the tokens."""
        return list(map(type, self.tokens))

    def backuntil(self, *classes):
        """Moves self.column back until a token of *classes is encountered."""
        for t in self.tokens[::-1]:
            if isinstance(t, classes):
                break
            self.column = t.pos


# Test functions that return a model or None
# self is the Analyzer instance.
def toplevel(self):
    """LilyPond toplevel document contents."""
    self.backuntil(lx.Space)
    return completiondata.lilypond_toplevel
    # maybe: check if behind \version or \language

def book(self):
    """\\book {"""
    self.backuntil(lx.Space)
    return completiondata.lilypond_book
    
def bookpart(self):
    """\\bookpart {"""
    self.backuntil(lx.Space)
    return completiondata.lilypond_bookpart

def score(self):
    """\\score {"""
    self.backuntil(lx.Space)
    return completiondata.lilypond_score

def tweak(self):
    """complete property after \\tweak"""
    if '\\tweak' in self.tokens:
        tokenclasses = self.tokenclasses()
        test = [lp.Command, lx.Space, lp.SchemeStart, scm.Quote, scm.Word]
        if tokenclasses[-3:] == test[:-2] and self.tokens[-3] == '\\tweak':
            self.column -= 1
            return completiondata.lilypond_all_grob_properties
        elif tokenclasses[-4:] == test[:-1] and self.tokens[-4] == '\\tweak':
            self.column -= 2
            return completiondata.lilypond_all_grob_properties
        elif tokenclasses[-5:] == test and self.tokens[-5] == '\\tweak':
            self.column = self.lastpos - 2
            return completiondata.lilypond_all_grob_properties

def key(self):
    """complete mode argument of '\\key'"""
    tokenclasses = self.tokenclasses()
    if '\\key' in self.tokens[-5:-2] and lp.Note in tokenclasses[-3:]:
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_modes

def clef(self):
    """complete \\clef names"""
    if '\\clef' in self.tokens[-4:-1]:
        self.backuntil(lx.Space, lp.StringQuotedStart)
        return completiondata.lilypond_clefs
        
def repeat(self):
    """complete \\repeat types"""
    if '\\repeat' in self.tokens[-4:-1]:
        self.backuntil(lx.Space, lp.StringQuotedStart)
        return completiondata.lilypond_repeat_types
        
def general_music(self):
    """fall back: generic music commands and user-defined commands."""
    if self.last.startswith('\\'):
        self.column = self.lastpos
    return documentdata.doc(self.cursor.document()).musiccommands(self.cursor)

def scheme_word(self):
    """Complete scheme word from scheme functions, etc."""
    if isinstance(self.last, scm.Word):
        self.column = self.lastpos
        return documentdata.doc(self.cursor.document()).schemewords()
    
def markup(self):
    """\\markup {"""
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
    
def header(self):
    """\\header {"""
    if '=' in self.tokens[-3:] or self.last.startswith('\\'):
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last[:1].isalpha():
        self.column = self.lastpos
    return completiondata.lilypond_header_variables

def paper(self):
    """\\paper {"""
    if '=' in self.tokens[-3:] or self.last.startswith('\\'):
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup
    if self.last[:1].isalpha():
        self.column = self.lastpos
    return completiondata.lilypond_paper_variables
    
def layout(self):
    """\\layout {"""
    self.backuntil(lx.Space)
    return completiondata.lilypond_layout_variables

def engraver(self):
    """Complete engraver names."""
    cmd_in = lambda tokens: '\\remove' in tokens or '\\consists' in tokens
    if isinstance(self.state.parser(), lp.ParseString):
        if not cmd_in(self.tokens[-5:-2]):
            return
        if self.last != '"':
            if '"' not in self.tokens[-2:-1]:
                return
            self.column = self.lastpos
        return completiondata.lilypond_engravers
    if cmd_in(self.tokens[-3:-1]):
        self.backuntil(lx.Space)
        return completiondata.lilypond_engravers
    
def context_variable_set(self):
    if '=' in self.tokens[-4:]:
        if isinstance(self.last, scm.Word):
            self.column = self.lastpos
            return documentdata.doc(self.cursor.document()).schemewords()
        if self.last.startswith('\\'):
            self.column = self.lastpos
        return completiondata.lilypond_markup

def context(self):
    self.backuntil(lx.Space)
    return completiondata.lilypond_context_contents

def with_(self):
    self.backuntil(lx.Space)
    return completiondata.lilypond_with_contents

def new_context(self):
    """complete context name after \\new, \\change or \\context in music"""
    for t in self.tokens[-2::-1]:
        if isinstance(t, lp.ContextName):
            return
        elif isinstance(t, lp.New):
            break
    self.backuntil(lx.Space)
    return completiondata.lilypond_contexts

def override(self):
    """\\override and \\revert"""
    tokenclasses = self.tokenclasses()
    try:
        # check if there is a GrobName in the last 5 tokens
        i = tokenclasses.index(lp.GrobName, -5)
    except ValueError:
        # not found, then complete Contexts and or Grobs
        # (only if we are in the override parser and there's no "=")
        if isinstance(self.state.parser(), scm.ParseScheme):
            return
        if lp.EqualSignSetOverride in tokenclasses:
            # TODO maybe return suitable values for the last property
            self.backuntil(lp.EqualSignSetOverride, lx.Space)
            return completiondata.lilypond_markup
        self.backuntil(lp.DotSetOverride, lx.Space)
        if (isinstance(self.state.parsers()[1], (
                lp.ParseWith,
                lp.ParseContext,
                ))
            or lp.DotSetOverride in tokenclasses):
            return completiondata.lilypond_grobs
        return completiondata.lilypond_contexts_and_grobs
    # yes, there is a GrobName at i
    count = len(self.tokens) - i - 1 # tokens after grobname
    if count == 0:
        self.column = self.lastpos
        return completiondata.lilypond_grobs
    elif count >= 2:
        # set the place of the scheme-start "#" as the column
        self.column = self.tokens[i+2].pos
    test = [lx.Space, lp.SchemeStart, scm.Quote, scm.Word]
    if tokenclasses[i+1:] == test[:count]:
        return completiondata.lilypond_grob_properties(self.tokens[i])

def set_unset(self):
    """\\set and \\unset"""
    tokenclasses = self.tokenclasses()
    self.backuntil(lx.Space, lp.DotSetOverride)
    if lp.EqualSignSetOverride in tokenclasses:
        # TODO maybe return suitable values for the context property
        for t in self.tokens[::-1]:
            if isinstance(t, (lp.EqualSignSetOverride, lx.Space)):
                break
            self.column = t.pos
        return completiondata.lilypond_markup
    elif lp.ContextProperty in tokenclasses and isinstance(self.last, lx.Space):
        return # fall back to music?
    elif lp.DotSetOverride in tokenclasses:
        return completiondata.lilypond_context_properties
    return completiondata.lilypond_contexts_and_properties

def markup_override(self):
    """test for \\markup \\override inside scheme"""
    try:
        i = self.tokens.index('\\override', -6, -4)
    except ValueError:
        return
    for t, cls in zip(self.tokens[i:], (
        lp.MarkupCommand, lx.Space, lp.SchemeStart, scm.Quote, scm.OpenParen)):
        if type(t) is not cls:
            return
    if len(self.tokens) > i + 5:
        self.column = self.lastpos
    return completiondata.lilypond_markup_properties

def scheme_other(self):
    """test for other scheme words"""
    if isinstance(self.last, (
        lp.SchemeStart,
        scm.OpenParen,
        scm.Word,
        )):
        if isinstance(self.last, scm.Word):
            self.column = self.lastpos
        return documentdata.doc(self.cursor.document()).schemewords()


# Mapping from Parsers to the lists of functions to run.
_tests = {
    lp.ParseGlobal: (
        repeat,
        toplevel,
    ),
    lp.ParseBook: (
        book,
    ),
    lp.ParseBookPart: (
        bookpart,
    ),
    lp.ParseScore: (
        score,
    ),
    lp.ParseMusic: (
        tweak,
        scheme_word,
        key,
        clef,
        repeat,
        general_music,
    ),
    lp.ParseNoteMode: (
        tweak,
        scheme_word,
        key,
        clef,
        repeat,
        general_music,
    ),
    lp.ParseMarkup: (
        markup,
    ),
    lp.ParseHeader: (
        header,
    ),
    lp.ParsePaper: (
        paper,
    ),
    lp.ParseLayout: (
        layout,
    ),
    lp.ParseContext: (
        engraver,
        context_variable_set,
        context,
    ),
    lp.ParseWith: (
        engraver,
        context_variable_set,
        with_,
    ),
    lp.ParseNewContext: (
        new_context,
    ),
    lp.ParseOverride: (
        override,
    ),
    lp.ParseRevert: (
        override,
    ),
    lp.ParseSet: (
        set_unset,
    ),
    lp.ParseUnset: (
        set_unset,
    ),
    lp.ParseString: (
        engraver,
        clef,
        repeat,
    ),
    lp.ParseClef: (
        clef,
    ),
    lp.ParseRepeat: (
        repeat,
    ),
    scm.ParseScheme: (
        override,
        tweak,
        markup_override,
        scheme_other,
    ),
}

