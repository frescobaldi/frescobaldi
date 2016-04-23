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
Analyze text to determine suitable completions.
"""


import re
import os

import ly.lex as lx
import ly.lex.lilypond as lp
import ly.lex.scheme as scm
import ly.words
import tokeniter

from . import completiondata
from . import documentdata


class Analyzer(object):
    """Analyzes text at some cursor position and gives suitable completions."""
    def analyze(self, cursor):
        """Do the analyzing work; set the attributes column and model."""
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

        parser = state.parser()

        # Map the parser class to a group of tests to return the model.
        # Try the tests until a model is returned.
        try:
            tests = self.tests[parser.__class__]
        except KeyError:
            return
        else:
            for function in tests:
                model = function(self)
                if model:
                    self.model = model
                    return

    def completions(self, cursor):
        """Analyzes text at cursor and returns a tuple (position, model).

        The position is an integer specifying the column in the line where the last
        text starts that should be completed.

        The model list the possible completions. If the model is None, there are no
        suitable completions.

        This function does its best to return extremely meaningful completions
        for the context the cursor is in.

        """
        self.analyze(cursor)
        return self.column, self.model

    def document_cursor(self):
        """Return the current QTextCursor, to harvest info from its document.

        By default this is simply the cursor given on analyze() or completions()
        but you can override this method to provide another cursor. This can
        be useful when the completion occurs in a small QTextDocument, which is
        in fact a part of the main document.

        """
        return self.cursor

    def tokenclasses(self):
        """Return the list of classes of the tokens."""
        return list(map(type, self.tokens))

    def backuntil(self, *classes):
        """Move self.column back until a token of *classes is encountered."""
        for t in self.tokens[::-1]:
            if isinstance(t, classes):
                break
            self.column = t.pos

    # Test functions that return a model or None
    def toplevel(self):
        """LilyPond toplevel document contents."""
        self.backuntil(lx.Space)
        return completiondata.lilypond_toplevel
        # maybe: check if behind \version or \language

    def book(self):
        """\\book {"""
        self.backuntil(lx.Space)
        cursor = self.document_cursor()
        return documentdata.doc(cursor.document()).bookcommands(cursor)

    def bookpart(self):
        """\\bookpart {"""
        self.backuntil(lx.Space)
        cursor = self.document_cursor()
        return documentdata.doc(cursor.document()).bookpartcommands(cursor)

    def score(self):
        """\\score {"""
        self.backuntil(lx.Space)
        cursor = self.document_cursor()
        return documentdata.doc(cursor.document()).scorecommands(cursor)

    def tweak(self):
        """complete property after \\tweak"""
        try:
            i = self.tokens.index('\\tweak')
        except ValueError:
            return
        tokens = self.tokens[i+1:]
        tokenclasses = self.tokenclasses()[i+1:]
        if tokenclasses == [lx.Space, lp.SchemeStart]:
            self.column -= 1
            return completiondata.lilypond_all_grob_properties
        elif tokenclasses == [lx.Space, lp.SchemeStart, scm.Quote]:
            self.column -= 2
            return completiondata.lilypond_all_grob_properties
        elif tokenclasses[:-1] == [lx.Space, lp.SchemeStart, scm.Quote]:
            self.column = self.lastpos - 2
            return completiondata.lilypond_all_grob_properties
        # 2.18-style [GrobName.]propertyname tweak
        if lp.GrobName in tokenclasses:
            self.backuntil(lx.Space, lp.DotPath)
            return completiondata.lilypond_grob_properties(tokens[1], False)
        if tokens:
            self.backuntil(lx.Space)
            return completiondata.lilypond_all_grob_properties_and_grob_names

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

    def language(self):
        """complete \\language "name" """
        if '\\language' in self.tokens[-4:-1]:
            self.backuntil(lp.StringQuotedStart)
            return completiondata.language_names

    def include(self):
        """complete \\include """
        if '\\include' in self.tokens[-4:-2]:
            self.backuntil(lp.StringQuotedStart)
            sep = '/' # Even on Windows, LilyPond uses the forward slash
            dir = self.last[:self.last.rfind(sep)] if sep in self.last else None
            cursor = self.document_cursor()
            return documentdata.doc(cursor.document()).includenames(cursor, dir)

    def general_music(self):
        """fall back: generic music commands and user-defined commands."""
        if self.last.startswith('\\'):
            self.column = self.lastpos
        cursor = self.document_cursor()
        return documentdata.doc(cursor.document()).musiccommands(cursor)

    def lyricmode(self):
        """Commands inside lyric mode."""
        if self.last.startswith('\\'):
            self.column = self.lastpos
        cursor = self.document_cursor()
        return documentdata.doc(cursor.document()).lyriccommands(cursor)

    def music_glyph(self):
        r"""Complete \markup \musicglyph names."""
        try:
            i = self.tokens.index('\\musicglyph', -5, -3)
        except ValueError:
            return
        for t, cls in zip(self.tokens[i:], (
            lp.MarkupCommand, lx.Space, lp.SchemeStart, scm.StringQuotedStart, scm.String)):
            if type(t) is not cls:
                return
        if i + 4 < len(self.tokens):
            self.column = self.tokens[i + 4].pos
        return completiondata.music_glyphs

    def midi_instrument(self):
        """Complete midiInstrument = #"... """
        try:
            i = self.tokens.index('midiInstrument', -7, -2)
        except ValueError:
            return
        if self.last != '"':
            self.column = self.lastpos
        return completiondata.midi_instruments

    def font_name(self):
        """Complete #'font-name = #"..."""
        try:
            i = self.tokens.index('font-name', -7, -3)
        except ValueError:
            return
        if self.last != '"':
            self.column = self.lastpos
        return completiondata.font_names()

    def scheme_word(self):
        """Complete scheme word from scheme functions, etc."""
        if isinstance(self.last, scm.Word):
            self.column = self.lastpos
            cursor = self.document_cursor()
            return documentdata.doc(cursor.document()).schemewords()

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
        cursor = self.document_cursor()
        return documentdata.doc(cursor.document()).markup(cursor)

    def markup_top(self):
        """\\markup ... in music or toplevel"""
        if self.last.startswith('\\') and isinstance(self.last,
            (ly.lex.lilypond.MarkupCommand, ly.lex.lilypond.MarkupUserCommand)):
            self.column = self.lastpos
            cursor = self.document_cursor()
            return documentdata.doc(cursor.document()).markup(cursor)

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

    def midi(self):
        """\\midi {"""
        self.backuntil(lx.Space)
        return completiondata.lilypond_midi_variables

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
                cursor = self.document_cursor()
                return documentdata.doc(cursor.document()).schemewords()
            if self.last.startswith('\\'):
                self.column = self.lastpos
            return completiondata.lilypond_markup

    def context(self):
        self.backuntil(lx.Space)
        return completiondata.lilypond_context_contents

    def with_(self):
        self.backuntil(lx.Space)
        return completiondata.lilypond_with_contents

    def translator(self):
        """complete context name after \\new, \\change or \\context in music"""
        for t in self.tokens[-2::-1]:
            if isinstance(t, lp.ContextName):
                return
            elif isinstance(t, lp.Translator):
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
            self.backuntil(lp.DotPath, lx.Space)
            if (isinstance(self.state.parsers()[1], (
                    lp.ParseWith,
                    lp.ParseContext,
                    ))
                or lp.DotPath in tokenclasses):
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
        self.backuntil(lp.DotPath, lx.Space)
        return completiondata.lilypond_grob_properties(self.tokens[i], False)

    def revert(self):
        """test for \\revert in general music expressions

        (because the revert parser drops out of invalid constructs, which happen
        during typing).

        """
        if '\\revert' in self.tokens:
            return self.override()

    def set_unset(self):
        """\\set and \\unset"""
        tokenclasses = self.tokenclasses()
        self.backuntil(lx.Space, lp.DotPath)
        if lp.ContextProperty in tokenclasses and isinstance(self.last, lx.Space):
            return # fall back to music?
        elif lp.DotPath in tokenclasses:
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
            cursor = self.document_cursor()
            return documentdata.doc(cursor.document()).schemewords()

    def accidental_style(self):
        """test for \accidentalStyle"""
        try:
            i = self.tokens.index("\\accidentalStyle")
        except ValueError:
            return
        self.backuntil(lx.Space, lp.DotPath)
        tokens = self.tokens[i+1:]
        tokenclasses = self.tokenclasses()[i+1:]
        try:
            i = tokenclasses.index(lp.AccidentalStyleSpecifier)
        except ValueError:
            pass
        else:
            if lx.Space in tokenclasses[i+1:]:
                return
        if lp.ContextName in tokenclasses:
            return completiondata.lilypond_accidental_styles
        return completiondata.lilypond_accidental_styles_contexts

    def hide_omit(self):
        r"""test for \omit and \hide"""
        indices = []
        for t in "\\omit", "\\hide":
            try:
                indices.append(self.tokens.index(t, -6))
            except ValueError:
                pass
        if not indices:
            return
        self.backuntil(lx.Space, lp.DotPath)
        i = max(indices)
        tokens = self.tokens[i+1:]
        tokenclasses = self.tokenclasses()[i+1:]
        if lp.GrobName not in tokenclasses[:-1]:
            if lp.ContextName in tokenclasses:
                return completiondata.lilypond_grobs
            return completiondata.lilypond_contexts_and_grobs


    # Mapping from Parsers to the lists of functions to run.
    tests = {
        lp.ParseGlobal: (
            markup_top,
            repeat,
            toplevel,
        ),
        lp.ParseBook: (
            markup_top,
            book,
        ),
        lp.ParseBookPart: (
            markup_top,
            bookpart,
        ),
        lp.ParseScore: (
            score,
        ),
        lp.ParseMusic: (
            markup_top,
            tweak,
            scheme_word,
            key,
            clef,
            repeat,
            accidental_style,
            hide_omit,
            revert,
            general_music,
        ),
        lp.ParseNoteMode: (
            markup_top,
            tweak,
            scheme_word,
            key,
            clef,
            repeat,
            accidental_style,
            hide_omit,
            revert,
            general_music,
        ),
        lp.ParseChordMode: (
            markup_top,
            tweak,
            scheme_word,
            key,
            clef,
            repeat,
            accidental_style,
            hide_omit,
            revert,
            general_music,
        ),
        lp.ParseDrumMode: (
            markup_top,
            tweak,
            scheme_word,
            key,
            clef,
            repeat,
            hide_omit,
            revert,
            general_music,
        ),
        lp.ParseFigureMode: (
            markup_top,
            tweak,
            scheme_word,
            key,
            clef,
            repeat,
            accidental_style,
            hide_omit,
            revert,
            general_music,
        ),
        lp.ParseMarkup: (
            markup,
        ),
        lp.ParseHeader: (
            markup_top,
            header,
        ),
        lp.ParsePaper: (
            paper,
        ),
        lp.ParseLayout: (
            accidental_style,
            hide_omit,
            layout,
        ),
        lp.ParseMidi: (
            midi,
        ),
        lp.ParseContext: (
            engraver,
            context_variable_set,
            context,
        ),
        lp.ParseWith: (
            markup_top,
            engraver,
            context_variable_set,
            with_,
        ),
        lp.ParseTranslator: (
            translator,
        ),
        lp.ExpectTranslatorId: (
            translator,
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
        lp.ParseTweak: (
            tweak,
        ),
        lp.ParseTweakGrobProperty: (
            tweak,
        ),
        lp.ParseString: (
            engraver,
            clef,
            repeat,
            midi_instrument,
            include,
            language,
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
        scm.ParseString: (
            music_glyph,
            midi_instrument,
            font_name,
        ),
        lp.ParseLyricMode: (
            markup_top,
            repeat,
            lyricmode,
        ),
        lp.ParseAccidentalStyle: (
            accidental_style,
        ),
        lp.ParseScriptAbbreviationOrFingering: (
            accidental_style,
        ),
        lp.ParseHideOmit: (
            hide_omit,
        ),
        lp.ParseGrobPropertyPath: (
            revert,
        ),
    }
