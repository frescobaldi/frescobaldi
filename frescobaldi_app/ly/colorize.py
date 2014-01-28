# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Classes and functions to colorize (syntax-highlight) parsed source.
"""

from __future__ import unicode_literals
from __future__ import absolute_import

import ly.lex.lilypond
import ly.lex.scheme
import ly.lex.html
import ly.lex.texinfo
#import ly.lex.latex
#import ly.lex.docbook



# don't test all the Token base classes
_token_mro_slice = slice(1, -len(ly.lex.Token.__mro__))


class Mapping(dict):
    """Maps token classes to arbitrary values, which can be highlighting styles.
    
    Mapping behaves like a dict, you set items with a token class as key to an
    arbitrary value.
    
    But getting items can be done using a token. The token class's method 
    resolution order is walked up and the value for the first available 
    class found in the keys is returned. The class is also cached to speed 
    up requests for other tokens.
    
    """
    def __getitem__(self, token):
        cls = type(token)
        try:
            return dict.__getitem__(self, cls)
        except KeyError:
            for c in cls.__mro__[_token_mro_slice]:
                try:
                    value = dict.__getitem__(self, c)
                    break
                except KeyError:
                    pass
            else:
                value = None
            self[cls] = value
            return value


# A dictionary with default mapping from token class to style, per group.
default_mapping = {
    'lilypond': (
        (ly.lex.lilypond.Keyword, 'keyword'),
        (ly.lex.lilypond.Command, 'command'),
        (ly.lex.lilypond.Dynamic, 'dynamic'),
        (ly.lex.lilypond.MusicItem, 'pitch'),
        (ly.lex.lilypond.Skip, 'command'),
        (ly.lex.lilypond.Octave, 'octave'),
        (ly.lex.lilypond.Duration, 'duration'),
        (ly.lex.lilypond.OctaveCheck, 'check'),
        (ly.lex.lilypond.Direction, 'articulation'),
        (ly.lex.lilypond.Fingering, 'fingering'),
        (ly.lex.lilypond.StringNumber, 'stringnumber'),
        (ly.lex.lilypond.Articulation, 'articulation'),
        (ly.lex.lilypond.Slur, 'slur'),
        (ly.lex.lilypond.Chord, 'chord'),
        (ly.lex.lilypond.ChordItem, 'chord'),
        (ly.lex.lilypond.PipeSymbol, 'check'),
        (ly.lex.lilypond.Markup, 'markup'),
        (ly.lex.lilypond.LyricMode, 'lyricmode'),
        (ly.lex.lilypond.Lyric, 'lyrictext'),
        (ly.lex.lilypond.Repeat, 'repeat'),
        (ly.lex.lilypond.Specifier, 'specifier'),
        (ly.lex.lilypond.UserCommand, 'usercommand'),
        (ly.lex.lilypond.Delimiter, 'delimiter'),
        (ly.lex.lilypond.ContextName, 'context'),
        (ly.lex.lilypond.GrobName, 'grob'),
        (ly.lex.lilypond.ContextProperty, 'property'),
        (ly.lex.lilypond.Variable, 'variable'),
        (ly.lex.lilypond.UserVariable, 'uservariable'),
        (ly.lex.lilypond.Value, 'value'),
        (ly.lex.lilypond.String, 'string'),
        (ly.lex.lilypond.StringQuoteEscape, 'stringescape'),
        (ly.lex.lilypond.Comment, 'comment'),
        (ly.lex.lilypond.Error, 'error'),
        (ly.lex.lilypond.Repeat, 'repeat'),
        (ly.lex.lilypond.Tremolo, 'repeat'),
    ),
    'scheme': (
        (ly.lex.lilypond.SchemeStart, 'scheme'),
        (ly.lex.scheme.Scheme, 'scheme'),
        (ly.lex.scheme.String, 'string'),
        (ly.lex.scheme.Comment, 'comment'),
        (ly.lex.scheme.Number, 'number'),
        (ly.lex.scheme.LilyPond, 'lilypond'),
        (ly.lex.scheme.Keyword, 'keyword'),
        (ly.lex.scheme.Function, 'function'),
        (ly.lex.scheme.Variable, 'variable'),
        (ly.lex.scheme.Constant, 'constant'),
        (ly.lex.scheme.OpenParen, 'delimiter'),
        (ly.lex.scheme.CloseParen, 'delimiter'),
    ),
    'html': (
        (ly.lex.html.Tag, 'tag'),
        (ly.lex.html.AttrName, 'attribute'),
        (ly.lex.html.Value, 'value'),
        (ly.lex.html.String, 'string'),
        (ly.lex.html.EntityRef, 'entityref'),
        (ly.lex.html.Comment, 'comment'),
        (ly.lex.html.LilyPondTag, 'lilypondtag'),
    ),
    'texinfo': (
        (ly.lex.texinfo.Keyword, 'keyword'),
        (ly.lex.texinfo.Block, 'block'),
        (ly.lex.texinfo.Attribute, 'attribute'),
        (ly.lex.texinfo.EscapeChar, 'escapechar'),
        (ly.lex.texinfo.Verbatim, 'verbatim'),
        (ly.lex.texinfo.Comment, 'comment'),
    ),
} # end of mapping


def get_tokens(cursor):
    """Return the list of tokens for the cursor.
    
    Tokens that are partially inside the cursor's selection are re-created
    so that they fall exactly within the selection.
    
    This can be used to convert a highlighted part of a document to e.g. HTML.
    
    """
    tokens = list(ly.document.Source(cursor, None, ly.document.PARTIAL, True))
    if tokens:
        if cursor.end is not None and tokens[-1].end > cursor.end:
            t = tokens[-1]
            tokens[-1] = type(t)(t[:cursor.end - t.end], t.pos)
        if cursor.start > tokens[0].pos:
            t = tokens[0]
            tokens[0] = type(t)(t[cursor.start - t.pos:], cursor.start)
    return tokens


def map_tokens(cursor, mapping):
    """Yield a two-tuple(token, style) for every token.
    
    The style is what mapping[token] returns.
    Style may be None, which also happens with unparsed (not-tokenized) text.
    
    """
    text = cursor.document.plaintext()
    start = cursor.start
    tokens = get_tokens(cursor)
    t = None
    for t in tokens:
        if t.pos > start:
            yield text[start:t.pos], None
        yield t, mapping[t]
        start = t.end
    if t and cursor.end is not None and cursor.end > t.end:
        yield text[t.end:cursor.end]


def melt_mapped_tokens(mapped_tokens):
    """Melt adjacent tokens with the same mapping together."""
    prev_tokens = []
    prev_style = None
    for t, s in mapped_tokens:
        if s == prev_style:
            prev_tokens.append(t)
        else:
            if prev_tokens:
                yield ''.join(prev_tokens), prev_style
            prev_tokens = [t]
            prev_style = s
    if prev_tokens:
        yield ''.join(prev_tokens), prev_style


def css_mapping(groups=default_mapping):
    """Return a Mapping instance, mapping token classes to two CSS classes."""
    return Mapping((cls, (mode, style)) for mode, classes in groups.items()
                                        for cls, style in classes)


def html_escape(text):
    """Escape &, < and >."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def html(cursor, mapping, span=lambda s: 'class="{0} {1}"'.format(*s)):
    """Return a HTML string with the tokens wrapped in <span class=> elements.
    
    The span argument is a function returning an attribute for the <span> 
    tag for the specified style. By default, it returns a 'class="group 
    style"' string. You'll want to wrap the HTML inside <pre> tokens and add 
    a CSS stylesheet.
    
    """
    result = []
    for t, style in melt_mapped_tokens(map_tokens(cursor, mapping)):
        if style:
            result.append('<span {0}>'.format(span(style)))
            result.append(html_escape(t))
            result.append('</span>')
        else:
            result.append(html_escape(t))
    return ''.join(result)


