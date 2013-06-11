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

from PyQt4.QtGui import QTextFormat, QTextCursor

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
            
    def tokens_in_block(self, block, startpos = 0, endpos = None):
        """Return a list of the tokens in the given block.
           Respect startpos and endpos (for partially selected lines).
           Tokens can be clipped."""
        source = list(tokeniter.tokens(block))
        
        # Sketch: Remove comments and debug 'print's when function is tested enough
        # startpos = 0 or endpos = None          =>  return source
        # 
        # begin loop
        # t.pos >= startpos and t.end <= endpos  => append token and continue
        # t.pos >= endpos                        => return current result
        # t.end <= startpos                      => continue
        # t.pos <= startpos (-> t.end > startpos => slice left, append and continue
        # t.end > endpos (-> t.pos < endpos)     => slice right, a
        
        if (startpos == 0) and (endpos == None):
            print "Return complete line"
            return source
            
        token_list = tl = []
        
        for t in source:
            if t.pos >= startpos and (endpos == None or t.end <= endpos):
                print "Token within boundaries", t, t.pos, startpos
                tl.append(t)
                continue
            if endpos != None and t.pos >= endpos:
                print "Token right of boundary", t
                return tl
            if t.end <= startpos:
                print "Token left of boundary", t
                continue
            endslice = None
            if t.pos <= startpos: #implies that t.end > startpos
                print "Token clipped left", t
                startslice = startpos - t.pos
                if endpos != None and t.end > endpos: 
                    endslice = endpos - t.pos # laenge des Slice ermitteln
            else:
                print "Token clipped right", t
                startslice = None
                endslice = endpos - t.pos
            tl.append(type(t)((t[startslice:endslice]), t.pos))
            if endpos != None and t.end >= endpos:
                return tl
        return tl

    def html_for_block(self, block, start = 0, end = None):
        """Return HTML for a given block."""
        print "html_for_block, char", start, "to", end
        token_list = tl = self.tokens_in_block(block, start, end)
        
        # then process this list
        # this has to be changed too, in order to clean up the output
        # For now I (UL) am only interested in factoring out.
        result = (map(self.html_for_token, tl))
        result.append('\n')
        print "".join(result)
        return result
    
    def html(self, cursor):
        """Return HTML for the cursor's selection,
           which may contain the complete document."""
        d = cursor.document()
        start = d.findBlock(cursor.selectionStart())
        startpos = cursor.selectionStart() - start.position()
        end = d.findBlock(cursor.selectionEnd())
        endpos = cursor.selectionEnd() - end.position()
        
        block = start
        nd = endpos if block == end else None
        html = self.html_for_block(block, startpos, nd)
        
        if block != end:
            # process consecutive lines
            block = block.next()
            while block != end:
                html.extend(self.html_for_block(block))
                block = block.next()
            # process last line
            html.extend(self.html_for_block(block, end = endpos))
        
        #remove trailing newline character
        html.pop()
        return self.wrapper_html_content.format(content="".join(html))

    def html_document(self, cursor, bodyOnly = False):
        """Returns HTML for the specified Document.
           If bodyOnly is False (default) it returns a full document,
           otherwise it returns only the <pre></pre> content."""
        cursor.select(QTextCursor.Document)
        if bodyOnly:
            return self.html(cursor)
        else:
            return self.html_doc_wrapper(self.html(cursor))
        
    def html_selection(self, cursor):
        return self.html(cursor)
    
