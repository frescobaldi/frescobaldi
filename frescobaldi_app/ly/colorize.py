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

Highlighting is based on CSS properties and their values, although the Mapping
object can map a token's class to any object or value.

The Mapping object normally maps a token's class basically to a CSS class and
possibly a base CSS class. This way you can define base styles (e.g. string,
comment, etc) and have specific classes (e.g. LilyPond string, Scheme 
comment) inherit from that base style. This css class is described by the 
css_class named tuple, with its three fields: mode, ccscls, base. E.g. 
('lilypond', 'articulation', 'keyword'). The base field may be None.

The css classes are mapped to dictionaries of css properties, like
{'font-weight': 'bold', 'color': '#4800ff'}, etc.

A scheme (a collection of styles) is simply a dictionary mapping the mode to
a dictionary of CSS dictionaries. The base styles are in the [None] item of the
scheme dictionary.


"""

from __future__ import unicode_literals
from __future__ import absolute_import

import collections

import ly.lex


# don't test all the Token base classes
_token_mro_slice = slice(1, -len(ly.lex.Token.__mro__))


css_class = collections.namedtuple("css_class", "mode cls base")


class Mapper(dict):
    """Maps token classes to arbitrary values, which can be highlighting styles.
    
    Mapper behaves like a dict, you set items with a token class as key to an
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


def default_mapping():
    """Return a good default mapping from token class(es) to style and default style, per group."""
    from ly.lex import lilypond
    from ly.lex import scheme
    from ly.lex import html
    from ly.lex import texinfo
    #from ly.lex import latex
    #from ly.lex import docbook
    
    return (
        ('lilypond', (
            ('keyword', 'keyword', (lilypond.Keyword,)),
            ('command', 'function', (lilypond.Command, lilypond.Skip)),
            ('pitch', None, (lilypond.MusicItem,)),
            ('octave', None, (lilypond.Octave,)),
            ('duration', None, (lilypond.Duration,)),
            ('dynamic', None, (lilypond.Dynamic,)),
            ('check', None, (lilypond.OctaveCheck, lilypond.PipeSymbol)),
            ('articulation', None, (lilypond.Direction, lilypond.Articulation)),
            ('fingering', None, (lilypond.Fingering,)),
            ('stringnumber', None, (lilypond.StringNumber,)),
            ('slur', None, (lilypond.Slur,)),
            ('chord', None, (lilypond.Chord, lilypond.ChordItem)),
            ('markup', 'function', (lilypond.Markup,)),
            ('lyricmode', 'function', (lilypond.LyricMode,)),
            ('lyrictext', None, (lilypond.Lyric,)),
            ('repeat', 'function', (lilypond.Repeat,)),
            ('specifier', 'variable', (lilypond.Specifier,)),
            ('usercommand', 'variable', (lilypond.UserCommand,)),
            ('delimiter', 'keyword', (lilypond.Delimiter,)),
            ('context', None, (lilypond.ContextName,)),
            ('grob', None, (lilypond.GrobName,)),
            ('property', 'variable', (lilypond.ContextProperty,)),
            ('variable', 'variable', (lilypond.Variable,)),
            ('uservariable', None, (lilypond.UserVariable,)),
            ('value', 'value', (lilypond.Value,)),
            ('string', 'string', (lilypond.String,)),
            ('stringescape', 'escape', (lilypond.StringQuoteEscape,)),
            ('comment', 'comment', (lilypond.Comment,)),
            ('error', 'error', (lilypond.Error,)),
            ('repeat', None, (lilypond.Repeat, lilypond.Tremolo,)),
        )),
        ('scheme', (
            ('scheme', None, (lilypond.SchemeStart, scheme.Scheme,)),
            ('string', 'string', (scheme.String,)),
            ('comment', 'comment', (scheme.Comment,)),
            ('number', 'value', (scheme.Number,)),
            ('lilypond', None, (scheme.LilyPond,)),
            ('keyword', 'keyword', (scheme.Keyword,)),
            ('function', 'function', (scheme.Function,)),
            ('variable', 'variable', (scheme.Variable,)),
            ('constant', 'variable', (scheme.Constant,)),
            ('delimiter', None, (scheme.OpenParen, scheme.CloseParen,)),
        )),
        ('html', (
            ('tag', 'keyword', (html.Tag,)),
            ('attribute', 'variable', (html.AttrName,)),
            ('value', 'value', (html.Value,)),
            ('string', 'string', (html.String,)),
            ('entityref', 'escape', (html.EntityRef,)),
            ('comment', 'comment', (html.Comment,)),
            ('lilypondtag', 'function', (html.LilyPondTag,)),
        )),
        ('texinfo', (
            ('keyword', 'keyword', (texinfo.Keyword,)),
            ('block', 'function', (texinfo.Block,)),
            ('attribute', 'variable', (texinfo.Attribute,)),
            ('escapechar', 'escape', (texinfo.EscapeChar,)),
            ('verbatim', 'string', (texinfo.Verbatim,)),
            ('comment', 'comment', (texinfo.Comment,)),
        )),
    ) # end of mapping


default_scheme = {
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


def map_tokens(cursor, mapper):
    """Yield a two-tuple(token, style) for every token.
    
    The style is what mapper[token] returns.
    Style may be None, which also happens with unparsed (not-tokenized) text.
    
    """
    text = cursor.document.plaintext()
    start = cursor.start
    tokens = get_tokens(cursor)
    t = None
    for t in tokens:
        if t.pos > start:
            yield text[start:t.pos], None
        yield t, mapper[t]
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


def css_mapper(mapping=None):
    """Return a Mapper dict, mapping token classes to two CSS classes.
    
    By default the mapping returned by default_mapping() is used.
    
    """
    if mapping is None:
        mapping = default_mapping()
    return Mapper((cls, css_class(mode, style, base))
                        for mode, styles in mapping
                            for style, base, clss in styles
                                for cls in clss)


def format_css_span_class(style):
    """Return a string like 'class="mode-style base"' for the specified style."""
    c = style.mode + '-' + style.cls
    if style.base:
        c += ' ' + style.base
    return 'class="{0}"'.format(c)


def css_dict(style, scheme=default_scheme):
    """Return the css properties dict for the style, taken from the scheme.
    
    This can be used for inline style attributes.
    
    """
    d = {}
    try:
        d.update(scheme[None][style.base])
    except KeyError:
        pass
    try:
        d.update(scheme[style.mode][style.cls])
    except KeyError:
        pass
    return d


class css_style_attribute_formatter(object):
    """Return the inline style attribute for a specified style."""
    def __init__(self, scheme=default_scheme):
        self.scheme = scheme
    
    def __call__(self, style):
        d = css_dict(style)
        if d:
            css_item = lambda a: '{0}: {1};'.format(*a)
            return 'style="{0}"'.format(' '.join(map(css_item, sorted(d.items()))))


def format_stylesheet(scheme=default_scheme):
    """Return a formatted stylesheet for the stylesheet scheme dictionary."""
    sheet = []
    css_group = lambda s, g: '{0} {{\n  {1}\n}}\n'.format(s, '\n  '.join(g))
    css_item = lambda a: '{0}: {1};'.format(*a)
    key = lambda i: '' if i[0] is None else i[0]
    for mode, styles in sorted(scheme.items(), key=key):
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


def html(cursor, mapper, span=format_css_span_class):
    """Return a HTML string with the tokens wrapped in <span class=> elements.
    
    The span argument is a function returning an attribute for the <span> 
    tag for the specified style. By default the format_css_span_class() 
    function is used, that returns a 'class="group style base"' string. 
    You'll want to wrap the HTML inside <pre> tokens and add a CSS stylesheet.
    
    """
    result = []
    for t, style in melt_mapped_tokens(map_tokens(cursor, mapper)):
        arg = span(style) if style else None
        if arg:
            result.append('<span {0}>'.format(arg))
            result.append(html_escape(t))
            result.append('</span>')
        else:
            result.append(html_escape(t))
    return ''.join(result)


def format_html_document(body, title="", stylesheet=None, stylesheet_ref=None, encoding='UTF-8'):
    """Return a complete HTML document.
    
    The body is put inside body tags unchanged.  The title is html-escaped. 
    If stylesheet_ref is given, it is put as a <link> reference in the HTML; 
    if stylesheet is given, it is put verbatim in a <style> section in the 
    HTML. The encoding is set in the meta http-equiv field, but the returned 
    HTML is in normal Python unicode (python2) or str (python3) format, you 
    should encode it yourself in the same encoding (by default utf-8) when 
    writing it to a file.
    
    """
    css = ""
    if stylesheet_ref:
        css += '<link rel="stylesheet" type="text/css" href="{0}"/>\n'.format(html_escape_attr(stylesheet_ref))
    if stylesheet:
        css += '<style type="text/css">\n{0}\n</style>\n'.format(stylesheet)
    return (
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
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


