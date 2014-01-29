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


# A dictionary with default mapping from token class to style and default style, per group.
default_mapping = {
    'lilypond': (
        (ly.lex.lilypond.Keyword, 'keyword', 'keyword'),
        (ly.lex.lilypond.Command, 'command', 'function'),
        (ly.lex.lilypond.Dynamic, 'dynamic', None),
        (ly.lex.lilypond.MusicItem, 'pitch', None),
        (ly.lex.lilypond.Skip, 'command', 'function'),
        (ly.lex.lilypond.Octave, 'octave', None),
        (ly.lex.lilypond.Duration, 'duration', None),
        (ly.lex.lilypond.OctaveCheck, 'check', None),
        (ly.lex.lilypond.Direction, 'articulation', None),
        (ly.lex.lilypond.Fingering, 'fingering', None),
        (ly.lex.lilypond.StringNumber, 'stringnumber', None),
        (ly.lex.lilypond.Articulation, 'articulation', None),
        (ly.lex.lilypond.Slur, 'slur', None),
        (ly.lex.lilypond.Chord, 'chord', None),
        (ly.lex.lilypond.ChordItem, 'chord', None),
        (ly.lex.lilypond.PipeSymbol, 'check', None),
        (ly.lex.lilypond.Markup, 'markup', 'function'),
        (ly.lex.lilypond.LyricMode, 'lyricmode', 'function'),
        (ly.lex.lilypond.Lyric, 'lyrictext', None),
        (ly.lex.lilypond.Repeat, 'repeat', 'function'),
        (ly.lex.lilypond.Specifier, 'specifier', 'variable'),
        (ly.lex.lilypond.UserCommand, 'usercommand', 'variable'),
        (ly.lex.lilypond.Delimiter, 'delimiter', 'keyword'),
        (ly.lex.lilypond.ContextName, 'context', None),
        (ly.lex.lilypond.GrobName, 'grob', None),
        (ly.lex.lilypond.ContextProperty, 'property', 'variable'),
        (ly.lex.lilypond.Variable, 'variable', 'variable'),
        (ly.lex.lilypond.UserVariable, 'uservariable', None),
        (ly.lex.lilypond.Value, 'value', 'value'),
        (ly.lex.lilypond.String, 'string', 'string'),
        (ly.lex.lilypond.StringQuoteEscape, 'stringescape', 'escape'),
        (ly.lex.lilypond.Comment, 'comment', 'comment'),
        (ly.lex.lilypond.Error, 'error', 'error'),
        (ly.lex.lilypond.Repeat, 'repeat', None),
        (ly.lex.lilypond.Tremolo, 'repeat', None),
    ),
    'scheme': (
        (ly.lex.lilypond.SchemeStart, 'scheme', None),
        (ly.lex.scheme.Scheme, 'scheme', None),
        (ly.lex.scheme.String, 'string', 'string'),
        (ly.lex.scheme.Comment, 'comment', 'comment'),
        (ly.lex.scheme.Number, 'number', 'value'),
        (ly.lex.scheme.LilyPond, 'lilypond', None),
        (ly.lex.scheme.Keyword, 'keyword', 'keyword'),
        (ly.lex.scheme.Function, 'function', 'function'),
        (ly.lex.scheme.Variable, 'variable', 'variable'),
        (ly.lex.scheme.Constant, 'constant', 'variable'),
        (ly.lex.scheme.OpenParen, 'delimiter', None),
        (ly.lex.scheme.CloseParen, 'delimiter', None),
    ),
    'html': (
        (ly.lex.html.Tag, 'tag', 'keyword'),
        (ly.lex.html.AttrName, 'attribute', 'variable'),
        (ly.lex.html.Value, 'value', 'value'),
        (ly.lex.html.String, 'string', 'string'),
        (ly.lex.html.EntityRef, 'entityref', 'escape'),
        (ly.lex.html.Comment, 'comment', 'comment'),
        (ly.lex.html.LilyPondTag, 'lilypondtag', 'function'),
    ),
    'texinfo': (
        (ly.lex.texinfo.Keyword, 'keyword', 'keyword'),
        (ly.lex.texinfo.Block, 'block', 'function'),
        (ly.lex.texinfo.Attribute, 'attribute', 'variable'),
        (ly.lex.texinfo.EscapeChar, 'escapechar', 'escape'),
        (ly.lex.texinfo.Verbatim, 'verbatim', 'string'),
        (ly.lex.texinfo.Comment, 'comment', 'comment'),
    ),
} # end of mapping


default_css_styles = {
    # the base styles
    None: {
        'keyword': {
            'font-weight': 'bold',
        },
        'function': {
            'font-weight': 'bold',
            'color': '#0000c0',
        },
        'variable': {
            'color': '#0000ff',
        },
        'value': {
            'color': '#808000',
        },
        'string': {
            'color': '#c00000',
        },
        'escape': {
            'color': '#008080',
        },
        'comment': {
            'color': '#808080',
            'font-style': 'italic',
        },
        'error': {
            'color': '#ff0000',
            'text-decoration': 'underline',
            'text-decoration-color': '#ff0000',
        },
    },
    'lilypond': {
        'duration': {
            'color': '#008080',
        },
        'markup': {
            'color': '#008000',
            'font-weight': 'normal',
        },
        'lyricmode': {
            'color': '#006000',
        },
        'lyrictext': {
            'color': '#006000',
        },
        'grob': {
            'color': '#c000c0',
        },
        'context': {
            'font-weight': 'bold',
        },
        'slur': {
            'font-weight': 'bold',
        },
        'articulation': {
            'font-weight': 'bold',
            'color': '#ff8000',
        },
        'dynamic': {
            'font-weight': 'bold',
            'color': '#ff8000',
        },
        'fingering': {
            'color': '#ff8000',
        },
        'stringnumber': {
            'color': '#ff8000',
        },
    },
    'scheme': {
    },
    'html': {
    },
    'texinfo': {
    },
} # end of default_css_styles


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
    return Mapping((cls, (mode, style, base)) for mode, classes in groups.items()
                                        for cls, style, base in classes)


def format_css_span_class(style):
    """Return a string like 'class="mode style base"' for the specified style."""
    mode, style, base = style
    c = mode + '-' + style
    if base:
        c += ' ' + base
    return 'class="{0}"'.format(c)


class css_style_attribute_formatter(object):
    """Return the inline style attribute for a specified style."""
    def __init__(self, css_styles=default_css_styles):
        self.styles = css_styles
    
    def __call__(self, style):
        mode, style, base = style
        d = (self.styles[None].get(base) if base else None) or {}
        d.update((self.styles.get(mode) or {}).get(style) or {})
        if d:
            css_item = lambda a: '{0}: {1};'.format(*a)
            return 'style="{0}"'.format(' '.join(map(css_item, sorted(d.items()))))


def format_stylesheet(css_styles=default_css_styles):
    """Return a formatted stylesheet for the stylesheet styles dictionary."""
    sheet = []
    css_group = lambda s, g: '{0} {{\n  {1}\n}}\n'.format(s, '\n  '.join(g))
    css_item = lambda a: '{0}: {1};'.format(*a)
    key = lambda i: '' if i[0] is None else i[0]
    for mode, styles in sorted(css_styles.items(), key=key):
        if styles:
            sheet.append('/* {0} */'.format(
                "mode: " + mode if mode else "base styles"))
        for css_class, d in sorted(styles.items()):
            if mode:
                selector = 'span.{0}-{1}'.format(mode, css_class)
            else:
                selector = '.' + css_class
            sheet.append(css_group(selector, map(css_item, sorted(d.items()))))
    return '\n'.join(sheet)


def html_escape(text):
    """Escape &, < and >."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def html_escape_attr(text):
    """Escape &, ", < and >."""
    return html_escape(text).replace('"', '&quot;')


def html(cursor, mapping, span=format_css_span_class):
    """Return a HTML string with the tokens wrapped in <span class=> elements.
    
    The span argument is a function returning an attribute for the <span> 
    tag for the specified style. By default, it returns a 'class="group 
    style base"' string. You'll want to wrap the HTML inside <pre> tokens 
    and add a CSS stylesheet.
    
    """
    result = []
    for t, style in melt_mapped_tokens(map_tokens(cursor, mapping)):
        arg = span(style) if style else None
        if arg:
            result.append('<span {0}>'.format(arg))
            result.append(html_escape(t))
            result.append('</span>')
        else:
            result.append(html_escape(t))
    return ''.join(result)


def format_html_document(body, title, stylesheet=None, stylesheet_ref=None, encoding='UTF-8'):
    """Return a complete HTML document.
    
    The body is put inside body tags unchanged.  The title is html-escaped.
    If stylesheet_ref is given, it is put as a reference in the HTML, else if
    stylesheet is given, it is put verbatim in a <style> section in the HTML.
    The encoding is set in the meta http-equiv field, but the returned HTML is
    in normal Python unicode (python2) or str (python3) format.
    
    """
    if stylesheet_ref:
        css = '<link rel="stylesheet" type="text/css" href="{0}"/>'.format(html_escape_attr(stylesheet_ref))
    elif stylesheet:
        css = '<style type="text/css">\n{0}\n</style>\n'.format(stylesheet)
    else:
        css = ''
    return (
        '<html><head>\n'
        '<title>{title}</title>\n'
        '<meta http-equiv="Content-Type" content="text/html; charset={encoding}" />\n'
        '{css}'
        '</head>\n'
        '<body>\n{body}</body>\n</html>\n').format(
            title = html_escape(title),
            encoding = encoding,
            body = body,
            css = css,
        )


