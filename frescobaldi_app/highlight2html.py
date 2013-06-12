# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Export syntax-highlighted text as HTML.
"""

from __future__ import unicode_literals

from PyQt4.QtGui import QTextFormat

import ly.lex
import highlighter
import textformats
import tokeniter


def textformat2css(f):
    """Convert a QTextFormat to a dict of CSS style declarations."""
    d = {}
    if f.hasProperty(QTextFormat.ForegroundBrush):
        d['color'] = f.foreground().color().name()
    if f.hasProperty(QTextFormat.BackgroundBrush):
        d['background'] = f.background().color().name()
    if f.hasProperty(QTextFormat.FontWeight):
        d['font-weight'] = format(f.fontWeight() * 8)
    if f.fontItalic():
        d['font-style'] = 'italic'
    if f.boolProperty(QTextFormat.TextUnderlineStyle):
        d['text-decoration'] = 'underline'
        if f.hasProperty(QTextFormat.TextUnderlineColor):
            d['text-decoration-color'] = f.underlineColor().name()
    return d


def escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class HtmlHighlighter(object):
    """Convert highlighted text or tokens to HTML."""
    
    # Set the inline_style attribute to True to use inline style attributes
    inline_style = False
    
    wrapper_css_doc = (
    "/*\n"
    " * LilyPond CSS\n"
    " * Style sheet for displaying LilyPond source code\n"
    " *\n"
    " * Exported from Frescobaldi\n" #TODO: Enter version string
    " */\n\n"
    )
    
    wrapper_html_doc = (
    "<html>\n"
    "<head>\n"
    "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'>\n"
    "{css}\n"
    "</head>\n"
    "<body{bodyattr}>\n"
    "{content}\n"
    "</body>\n</html>\n"
    )
    
    wrapper_html_content = "<pre>{content}</pre>\n"
    
    def __init__(self, data=None, inline_style=False):
        """Initialize the HtmlHighlighter with a TextFormatData instance.
        
        If none is given, the textformats.textFormat('editor') is used.
        
        """
        self.inline_style = inline_style
        self.setFormatData(data or textformats.formatData('editor'))
    
    def setFormatData(self, data):
        """Sets a TextFormatData instance for this HTML highlighter."""
        self._data = data
        self._formats = f = {} # maps css class to css declarations
        self._classes = c = {} # maps token class to css class
        for cls, fmt in highlighter.mapping(data).items():
            name = cls.__module__.split('.')[-1] + '-' + cls.__name__.lower()
            c[cls] = name
            f[name] = textformat2css(fmt)

    def css_data(self):
        """Yield css stubs for all the styles."""
        yield 'body', {
            'color': self._data.baseColors['text'].name(),
            'background': self._data.baseColors['background'].name(),
            #'font-family': '"{0}"'.format(self._data.font.family()),
            #'font-size': format(self._data.font.pointSizeF()),
        }
        for c in sorted(self._formats):
            yield '.' + c, self._formats[c]

    @classmethod
    def format_css_items(self, items, separator=" "):
        """Formats css items as text using the separator string.
        
        By default a space is used, but you could also use e.g. "\n  ".
        
        """
        return separator.join(
            "{0}: {1};".format(k, v)
            for k, v in items.items())

    def stylesheet(self, standalone = False):
        """Returns the stylesheet for all the styles."""
        header = ""
        if standalone:
            header = self.wrapper_css_doc
        return header + "\n".join(
            '{0} {{\n  {1}\n}}\n'.format(
            selector, self.format_css_items(items, '\n  '))
            for selector, items in self.css_data())

    def html_for_token(self, token, cls=None):
        """Return a piece of HTML for the specified token.
        
        The specified class is used, or the token's class.
        
        """
        if cls is None:
            cls = type(token)
        try:
            css = self._classes[cls]
        except KeyError:
            for c in cls.__mro__[highlighter._token_mro_slice]:
                try:
                    css = self._classes[c]
                    break
                except KeyError:
                    pass
            else:
                return escape(token)
            self._classes[cls] = css
        if self.inline_style:
            style = self.format_css_items(self._formats[css])
            return '<span style="{0}">{1}</span>'.format(style, escape(token))
        else:
            return '<span class="{0}">{1}</span>'.format(css, escape(token))
            
    def html_doc_wrapper(self, content):
        """Returns a full HTML document.
        
        The body should be the HTML for all the text.
        It will be wrapped in a html/body construct, and the stylesheet
        will be put in the header, if inline_style is set to False (default).
        
        """
        if self.inline_style:
            css = ''
            bodyattr = ' text="{0}" bgcolor="{1}"'.format(
                self._data.baseColors['text'].name(),
                self._data.baseColors['background'].name())
        else:
            css = '<style type="text/css">\n{0}</style>'.format(
                escape(self.stylesheet()))
            bodyattr = ''
        return self.wrapper_html_doc.format(
            css=css,
            bodyattr=bodyattr,
            content=content)
        
    def html_document(self, doc, bodyOnly = False):
        """Returns HTML for the specified Document.
           If bodyOnly is False (default) it returns a full document,
           otherwise it returns only the <pre></pre> content."""
        def html():
            block = doc.firstBlock()
            while block.isValid():
                yield "".join(map(self.html_for_token, tokeniter.tokens(block)))
                block = block.next()
        result = self.wrapper_html_content.format(content="\n".join(html()))
        if not bodyOnly:
            result = self.html_doc_wrapper(result)
        return result
    
    def html_selection(self, cursor):
        """Return HTML for the cursor's selection."""
        d = cursor.document()
        start = d.findBlock(cursor.selectionStart())
        startpos = cursor.selectionStart() - start.position()
        end = d.findBlock(cursor.selectionEnd())
        endpos = cursor.selectionEnd() - end.position()
        
        html = []
        # first block, skip tokens before selection
        block = start
        source = iter(tokeniter.tokens(block))
        for t in source:
            if t.end > startpos:
                startslice = max(0, startpos - t.pos)
                endslice = None
                if block == end and t.end > endpos:
                    endslice = endpos - t.pos
                html.append(self.html_for_token(t[startslice:endslice], type(t)))
                break
        while block != end:
            html.extend(map(self.html_for_token, source))
            html.append('\n')
            block = block.next()
            source = iter(tokeniter.tokens(block))
        # last block, go to end of selection
        for t in source:
            if t.end > endpos:
                if t.pos < endpos:
                    html.append(self.html_for_token(t[:endpos-t.pos], type(t)))
                break
            html.append(self.html_for_token(t))
        return self.wrapper_html_content.format(content="".join(html))
