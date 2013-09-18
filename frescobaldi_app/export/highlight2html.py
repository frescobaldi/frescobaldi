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
import info

from . import options


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
    
    css_doc_header = (
    "/*\n"
    " * LilyPond CSS\n"
    " * Style sheet for displaying LilyPond source code\n"
    " *\n"
    " * Exported by {appname} {version}\n"
    " */\n\n"
    ).format(appname=info.appname, version=info.version)
    
    wrap_html_doc = (
    "<html>\n"
    "<head>\n"
    "{title}"
    "<meta http-equiv=\"Content-Type\" content=\"text/html\"; charset=\"utf-8\">\n"
    "<meta generator=\"{appname} {version}\">\n"
    "{css}"
    "</head>\n"
    "<body{bodyattr}>\n"
    "{content}\n"
    "</body>\n"
    "</html>\n"
    )
    
    wrap_html_content = "<pre{style}>{content}</pre>\n"
    
    def __init__(self, data=None):
        """Initialize the HtmlHighlighter with a TextFormatData instance.
        
        If none is given, the textformats.textFormat('editor') is used.
        
        """
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
        c["lilypond-linenumber"] = "lilypond-linenumber"
        f["lilypond-linenumber"] = {
            'background': '#ccc',
            'border-right': '0.3ex solid #333',
            'padding-left': '1ex', 
            'padding-right': '1ex', 
            'margin-right': '1ex', 
        }

    def css_data(self):
        """Yield css stubs for all the styles."""
        yield 'body', {
            'color': self._data.baseColors['text'].name(),
            'background': self._data.baseColors['background'].name(),
            #'font-family': '"{0}"'.format(self._data.font.family()),
            #'font-size': format(self._data.font.pointSizeF()),
        }
        if self.printLayout():
            yield 'pre', {
                'color': self._data.baseColors['text'].name(),
                'background': self._data.baseColors['background'].name(),
                'font-family': '"{0}"'.format(self._data.font.family()),
                'font-size': format(self._data.font.pointSizeF() * 0.7),
            }
        else:
            yield 'pre.lilypond', {
                '/* Empty class': ' Can be customized in concrete style sheet */', 
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

    def printLayout(self):
        return (options.value("dest") == "printer" or
             (options.value("dest") == "file" and
              options.value("filetype") == "pdf"))
        
    def stylesheet(self):
        """Returns the stylesheet for all the styles."""
        return "\n".join(
            '{0} {{\n  {1}\n}}\n'.format(
            selector, self.format_css_items(items, '\n  '))
            for selector, items in self.css_data())

    def html_doc_wrapper(self, content, title):
        """Returns a full HTML document.
        
        The body should be the HTML for all the text.
        It will be wrapped in a html/body construct, and the stylesheet
        will be put in the header, if inline_style is set to False (default).
        
        """
        if options.value("print_title") and self.printLayout():
            html_title = "<p>{title_tag}</p>\n".format(title_tag=title)
            content = html_title + content

        if options.value("style") == "inline":
            css = ''
            bodyattr = ' text="{0}" bgcolor="{1}"'.format(
                self._data.baseColors['text'].name(),
                self._data.baseColors['background'].name())
        elif options.value("style") == "external":
            css = "<link rel=\"stylesheet\" type=\"text/css\" href=\"{external_css}\">\n".format(
                external_css=options.value("external_css"))
            bodyattr = ""
        else:
            css = "<style type=\"text/css\">\n{0}\n</style>\n".format(
                escape(self.stylesheet()))
            bodyattr = ""
        if options.value("print_title"):
            titletag="<title>{doc_title}</title>\n".format(doc_title=title)
        else:
            titletag = ""
        return self.wrap_html_doc.format(
            css=css,
            bodyattr=bodyattr,
            content=content,
            appname=info.appname, 
            version=info.version, 
            title=titletag)
        
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
        if options.value("style") == "inline":
            style = self.format_css_items(self._formats[css])
            return '<span style="{0}">{1}</span>'.format(style, escape(token))
        else:
            return '<span class="{0}">{1}</span>'.format(css, escape(token))
            
    def html_for_linenumber(self, linenum):
        digits = self.linenumdigits
        if not digits:
            return ""
        token = str(linenum)
        print "token:",  token, "length:", len(token)
        for i in range(len(token), digits):
#        while len(token) < options.get("linenumdigits"):
            token = "0" + token
        return "<span class=\"lilypond-linenumber\">{t}</span>".format(t=token)
    
    def tokens_in_block(self, block, startpos = 0, endpos = None):
        """Return a list of the tokens in the given block.
           Respect startpos and endpos (for partially selected lines).
           Tokens can be clipped."""
        source = list(tokeniter.tokens(block))
        
        if (startpos == 0) and (endpos == None):
            return source
            
        token_list = tl = []
        
        for t in source:
            if t.pos >= startpos and (endpos == None or t.end <= endpos):
                tl.append(t)
                continue
            if endpos != None and t.pos >= endpos:
                return tl
            if t.end <= startpos:
                continue
            endslice = None
            if t.pos <= startpos: #implies that t.end > startpos
                startslice = startpos - t.pos
                if endpos != None and t.end > endpos: 
                    endslice = endpos - t.pos # laenge des Slice ermitteln
            else:
                startslice = None
                endslice = endpos - t.pos
            tl.append(type(t)((t[startslice:endslice]), t.pos))
            if endpos != None and t.end >= endpos:
                return tl
        return tl

    def html_for_block(self, block, start = 0, end = None):
        """Return HTML for a given block.
           Combine consecutive elements
           (i.e. tokens of the same class, 
           separated by spaces) to one token."""
        token_list = tl = self.tokens_in_block(block, start, end)
        html = ""

        def block_comment(tl):
            t = ""
            tpos = tl[0].pos
            while len(tl):
                if isinstance(tl[0], ly.lex.lilypond.BlockCommentEnd):
                    self.block_comment = False
                    t += tl.pop(0)
                    return (ly.lex.lilypond.Comment(t, tpos), tl)
                t += tl.pop(0)
            return (ly.lex.lilypond.Comment(t, tpos), [])
        
        def next_type(i):
            return type(tl[i]) if len(tl) > i else None
            
        def consecutive_tokens(tl):
            current_type = type(tl[0])
            if (self.block_comment or 
                current_type is ly.lex.lilypond.BlockCommentSpace or 
                next_type(1) is ly.lex.lilypond.BlockCommentSpace):
                self.block_comment = True
                return block_comment(tl)
            while (next_type(1) is ly.lex._token.Space and 
                   next_type(2) is current_type):
                tl[0] += tl[1] + tl[2]
                del tl[1:3]
            return (tl[0], tl[1:])
        
        if options.value("linenumbers") and self.linenumdigits:
            linenum = str(block.blockNumber() + 1)
            for i in range(len(linenum), self.linenumdigits):
                linenum = "0" + linenum
            html += self.html_for_token(linenum, "lilypond-linenumber")
        while len(tl):
            t, tl = consecutive_tokens(tl)
            html += self.html_for_token(t) if t else ""
        return html + '\n'
    
    def html_content(self, cursor):
        """Return content for the selection or the document
           as HTML or the CSS."""
        
        if options.value("source") == "css":
            print self.stylesheet()
            return self.stylesheet()
        if options.value("source") == "document":
            cursor.select(QTextCursor.Document)
        
        d = cursor.document()
        start = d.findBlock(cursor.selectionStart())
        startpos = cursor.selectionStart() - start.position()
        end = d.findBlock(cursor.selectionEnd())
        endpos = cursor.selectionEnd() - end.position()
        self.block_comment = False
        
        if options.value("linenumbers"):
            self.linenumdigits = len(str(end.blockNumber()))
        else:
            self.linenumdigits = 0
        
        block = start
        nd = endpos if block == end else None
        html = self.html_for_block(block, startpos, nd)
        
        if block != end:
            # process consecutive lines
            block = block.next()
            while block != end:
                html += self.html_for_block(block)
                block = block.next()
            # process last line
            html += self.html_for_block(block, end = endpos)
        
        if options.value("style") == "inline":
            prestyle = " style=\"line-height: 120%\""
        else:
            prestyle = " class=\"lilypond\""
        return self.wrap_html_content.format(content="".join(html[:len(html)]), 
                                             style=prestyle)
        
    def html_document(self, content, title):
        """Wraps the given HTML or CSS content
           to a complete file"""
        if options.value("source") == "css":
            return self.css_doc_header + content
        else:
            return self.html_doc_wrapper(content, title)
        
    
