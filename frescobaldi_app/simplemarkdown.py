#!python
# SimpleMarkdown -- a very basic markdown-like parser.
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
SimpleMarkdown -- a very basic markdown-like parser.

It supports different ways to iterate over the parsed text fragments and events.

It supports the following blocklevel items:

=== heading 1

== heading 2

= heading 3

plain text paragraph

* unordered list

1. ordered list

  * nested lists are possible
  
    a paragraph without bullet item

* compact item list
* item 2 (here no paragraphs will be put in the list items)

term of definition list
: definition text


```language
verbatim code
```

Block quotes are not supported

inline level:

*emphasis*

`code`

[link]
[link text]
[image:filename]

"""


from __future__ import unicode_literals



def chop_left(string, chars=None):
    """Return the string that string.lstrip(chars) would chop off."""
    return string[:-len(string.lstrip(chars))]

def iter_split(text, separator):
    """Yield pairs of text before and after the separator."""
    while True:
        t = text.split(separator, 2)
        if len(t) < 3:
            if text:
                yield text, ''
            break
        yield t[:2]
        text = t[2]

def iter_split2(text, separator, separator2):
    """Yield pairs of text outside and inside the separators.
    
    This can be used to parse e.g. "text with [bracketed words] in it".
    
    """
    while True:
        t = text.split(separator, 1)
        if len(t) > 1:
            t2 = t[1].split(separator2, 1)
            if len(t2) > 1:
                yield t[0], t2[0]
                text = t2[1]
                continue
        if text:
            yield text, ''
        return


class SimpleMarkdown(object):
    """SimpleMarkdown -- a very basic Markdown-like parser.
    
    This class encapsulates both the parser and the output generator,
    making it easy to hook in both in the parsing process and the output
    generating process.
    
    """
    def __init__(self):
        self._lists = []
    
    def parse(self, text):
        """Parse the text and call methods on certain events."""
        # split in code and non-code blocks
        for text, code in iter_split(text, '\n```'):
            self.parse_noncode(text)
            if code:
                self.parse_code(code)
        
    def parse_code(self, code):
        """Parse code inside ``` code ``` blocks.
        
        Calls self.code() with the code and the language specifier (if given
        on the first line).
        
        """
        try:
            specifier, code = code.split('\n', 1)
            self.code(code, specifier.strip() or None)
        except ValueError:
            self.code(code)
    
    def parse_noncode(self, text):
        """Parse text outside ``` code ``` blocks.
        
        Just calls parse_lines() with each group of connected non-blank lines.
        
        """
        para = []
        for line in text.splitlines():
            if not line or line.isspace():
                if para:
                    self.parse_lines(para)
                    para = []
            else:
                para.append(line)
        if para:
            self.parse_lines(para)
        self.handle_lists(0)
    
    def parse_lines(self, lines):
        """Parse a list of one or more lines without blank lines in between.
        
        Dispatches the lines to handle headings, lists or plain text paragraphs.
        
        """
        indent = len(chop_left(lines[0]))
        if lines[0].lstrip().startswith('='):
            self.handle_lists(indent)
            self.parse_heading(lines)
        elif self.is_ul_item(lines[0]):
            self.handle_lists(indent, 'ul')
            self.parse_ul(lines)
        elif self.is_ol_item(lines[0]):
            self.handle_lists(indent, 'ol')
            self.parse_ol(lines)
        elif self.is_dl_item(lines):
            self.handle_lists(indent, 'dl')
            self.parse_dl(lines)
        else:
            self.handle_lists(indent)
            self.parse_paragraph(lines)
    
    def is_ul_item(self, line):
        """Return True if the line is a unordered list prefix ("*")."""
        try:
            prefix, line = line.split(None, 1)
            return prefix == '*'
        except ValueError:
            return False

    def is_ol_item(self, line):
        """Return True if the line is a ordered list prefix (number period)."""
        try:
            prefix, line = line.split(None, 1)
            return prefix.endswith('.') and prefix[:-1].isdigit()
        except ValueError:
            return False
    
    def is_dl_item(self, lines):
        """Return True lines are a description list item."""
        return len(lines) > 1 and lines[1].lstrip().startswith(': ')
    
    def parse_paragraph(self, lines):
        """Parse a plain paragraph of text."""
        self.paragraph_start()
        self.parse_plain_text(lines)
        self.paragraph_end()
    
    def parse_heading(self, lines):
        """Parse a header text."""
        prefix = chop_left(lines[0], '= ')
        heading_type = 4 - min(prefix.count('='), 3)
        lines[0] = lines[0].strip('= ')
        self.heading_start(heading_type)
        self.parse_plain_text(lines)
        self.heading_end(heading_type)
    
    def parse_ol(self, lines):
        """Parse ordered lists.
        
        Every line of the supplied group of lines is checked for a number,
        if they are separate items, no paragraph tags are put around the list
        items.
        
        """
        # split in list items
        items = self.split_list_items(lines, self.is_ol_item)
        paragraph_item = len(items) == 1
        for item in items:
            self.orderedlist_item_start()
            if paragraph_item:
                self.parse_paragraph(item)
            else:
                self.parse_plain_text(item)
            self.orderedlist_item_end()
            
    def parse_ul(self, lines):
        """Parse unordered lists.
        
        Every line of the supplied group of lines is checked for an asterisk,
        if they are separate items, no paragraph tags are put around the list
        items.
        
        """
        items = self.split_list_items(lines, self.is_ul_item)
        paragraph_item = len(items) == 1
        for item in items:
            self.unorderedlist_item_start()
            if paragraph_item:
                self.parse_paragraph(item)
            else:
                self.parse_plain_text(item)
            self.unorderedlist_item_end()
    
    def split_list_items(self, lines, pred):
        """Returns lists of lines that each represent a list item.
        
        The pred function should return true for a line that has an item prefix.
        
        """
        items = []
        item = []
        for line in lines:
            if pred(line):
                if item:
                    items.append(item)
                item = [line.split(None, 1)[1]]
            else:
                item.append(line)
        if item:
            items.append(item)
        return items
        
    def parse_dl(self, lines):
        """Parse a definition list item."""
        definition = lines[0]
        lines[1] = lines[1].split(':', 1)[1]
        self.definitionlist_item_start()
        self.definitionlist_item_term_start()
        self.parse_plain_text([definition])
        self.definitionlist_item_term_end()
        self.definitionlist_item_definition_start()
        self.parse_plain_text(lines[1:])
        self.definitionlist_item_definition_end()
        self.definitionlist_item_end()
    
    ##
    # utility methods
    ##
        
    def handle_lists(self, indent, list_type=None):
        """Close ongoing lists or start new lists if needed.
        
        If given, list_type should be 'ol', 'ul', or 'dl'.
        
        """
        if list_type and (not self._lists or self._lists[-1][1] < indent):
            self._lists.append((list_type, indent))
            self.list_start(list_type)
        else:
            while self._lists:
                if self._lists[-1][1] > indent:
                    self.list_end(self._lists[-1][0])
                    self._lists.pop()
                    continue
                elif self._lists[-1][1] == indent and self._lists[-1][0] != list_type:
                    self.list_end(self._lists[-1][0])
                    self._lists.pop()
                    if list_type:
                        self._lists.append((list_type, indent))
                        self.list_start(list_type)
                break
        
    def list_start(self, list_type):
        """Start a list, type should be 'ol', 'ul', or 'dl'."""
        if list_type == "ol":
            self.orderedlist_start()
        elif list_type == "ul":
            self.unorderedlist_start()
        elif list_type == "dl":
            self.definitionlist_start()
            
    def list_end(self, list_type):
        """End a list, type should be 'ol', 'ul', or 'dl'."""
        if list_type == "ol":
            self.orderedlist_end()
        elif list_type == "ul":
            self.unorderedlist_end()
        elif list_type == "dl":
            self.definitionlist_end()
            
    ##
    # inline level parsing
    ##
    
    def parse_plain_text(self, lines):
        """Parse plain text lines with possibly inline markup.
        
        This implementation simply calls parse_inline_block('\n'.join(lines)).
        
        """
        self.parse_inline_block('\n'.join(lines))
        
    def parse_inline_block(self, text):
        """Parse a continuous text block with possibly inline markup."""
        self.inline_start()
        for text, code in iter_split(text, '`'):
            if text:
                self.parse_inline_noncode(text)
            if code:
                self.parse_inline_code(code)
        self.inline_end()
    
    def parse_inline_code(self, text):
        self.inline_code(text)

    def parse_inline_noncode(self, text):
        for normal, emph in iter_split(text, '*'):
            if normal:
                self.parse_inline_text(normal)
            if emph:
                self.inline_emphasis_start()
                self.parse_inline_text(emph)
                self.inline_emphasis_end()
    
    def parse_inline_text(self, text):
        # TODO escape [ and ] ?
        for nolink, link in iter_split2(text, '[', ']'):
            if nolink:
                self.inline_text(nolink)
            if link:
                link = link.split(None, 1)
                if len(link) == 1:
                    url = text = link[0]
                else:
                    url, text = link
                self.link_start(url)
                self.inline_text(text)
                self.link_end(url)
    
    ##
    # block level handlers
    ##

    def code(self, code, specifier=None):
        pass
    
    def heading_start(self, heading_type):
        pass
    
    def heading_end(self, heading_type):
        pass
        
    def paragraph_start(self):
        pass
    
    def paragraph_end(self):
        pass
    
    def orderedlist_start(self):
        pass
    
    def orderedlist_item_start(self):
        pass
    
    def orderedlist_item_end(self):
        pass
    
    def orderedlist_end(self):
        pass
    
    def unorderedlist_start(self):
        pass
    
    def unorderedlist_item_start(self):
        pass
    
    def unorderedlist_item_end(self):
        pass
    
    def unorderedlist_end(self):
        pass
    
    def definitionlist_start(self):
        pass
        
    def definitionlist_item_term_start(self):
        pass
        
    def definitionlist_item_term_end(self):
        pass
        
    def definitionlist_item_definition_start(self):
        pass
        
    def definitionlist_item_definition_end(self):
        pass
        
    def definitionlist_item_start(self):
        pass
        
    def definitionlist_item_end(self):
        pass
        
    def definitionlist_end(self):
        pass

    ##
    # inline handlers
    ##

    def inline_start(self):
        """Called when a block of inline text is parsed."""
        pass
        
    def inline_end(self):
        """Called at the end of parsing a block of inline text.""" 
        pass
    
    def inline_code(self, text):
        pass
    
    def inline_emphasis_start(self):
        pass
    
    def inline_emphasis_end(self):
        pass
    
    def link_start(self, url):
        pass
    
    def link_end(self, url):
        pass
    
    def inline_text(self, text):
        pass


class Markdown2Html(SimpleMarkdown):
    """Converts simple markdown to HTML."""
    def __init__(self):
        SimpleMarkdown.__init__(self)
        self._html = []
    
    def html(self):
        return ''.join(self._html)
    
    def html_escape(self, text):
        """Escapes &, < and >."""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def tag(self, name, attrs=None):
        """Add a tag. Use a name like '/p' to write a close tag.
        
        attrs may be a dictionary of attributes.
        
        """
        if attrs:
            a = ''.join(' {0}="{1}"'.format(
                name, self.html_escape(value).replace('"', '&quot;'))
                for name, value in attrs.items())
        else:
            a = ''
        self._html.append('<{0}{1}>'.format(name, a))
    
    def nl(self):
        """Add a newline."""
        self._html.append('\n')
    
    def text(self, text):
        self._html.append(self.html_escape(text))
    
    ##
    # block level handlers
    ##

    def code(self, code, specifier=None):
        self.tag('code')
        self.tag('pre')
        self.text(code)
        self.tag('/pre')
        self.tag('/code')
        self.nl()
    
    def heading_start(self, heading_type):
        self.tag('h{0}'.format(heading_type))
    
    def heading_end(self, heading_type):
        self.tag('/h{0}'.format(heading_type))
        self.nl()
        
    def paragraph_start(self):
        self.tag('p')
    
    def paragraph_end(self):
        self.tag('/p')
        self.nl()
    
    def orderedlist_start(self):
        self.tag('ol')
        self.nl()
    
    def orderedlist_item_start(self):
        self.tag('li')
    
    def orderedlist_item_end(self):
        self.tag('/li')
        self.nl()
    
    def orderedlist_end(self):
        self.tag('/ol')
        self.nl()
    
    def unorderedlist_start(self):
        self.tag('ul')
        self.nl()
    
    def unorderedlist_item_start(self):
        self.tag('li')
    
    def unorderedlist_item_end(self):
        self.tag('/li')
        self.nl()

    def unorderedlist_end(self):
        self.tag('/ul')
        self.nl()
    
    def definitionlist_start(self):
        self.tag('dl')
        self.nl()
        
    def definitionlist_item_term_start(self):
        self.tag('dt')
        
    def definitionlist_item_term_end(self):
        self.tag('/dt')
        self.nl()
        
    def definitionlist_item_definition_start(self):
        self.tag('dd')
        
    def definitionlist_item_definition_end(self):
        self.tag('/dd')
        self.nl()
        
    def definitionlist_item_start(self):
        pass
        
    def definitionlist_item_end(self):
        pass
        
    def definitionlist_end(self):
        self.tag('/dl')
        self.nl()

    ##
    # inline handlers
    ##

    def inline_start(self):
        """Called when a block of inline text is parsed."""
        pass
        
    def inline_end(self):
        """Called at the end of parsing a block of inline text.""" 
        pass
    
    def inline_code(self, text):
        self.tag('code')
        self.text(text)
        self.tag('/code')
    
    def inline_emphasis_start(self):
        self.tag('em')
    
    def inline_emphasis_end(self):
        self.tag('/em')
    
    def link_start(self, url):
        self.tag('a', {'href': url})
    
    def link_end(self, url):
        self.tag('/a')
    
    def inline_text(self, text):
        self.text(self.html_escape(text))



class _Debug(SimpleMarkdown):
    """A debugging version that prints the events."""
    ##
    # block level handlers
    ##
    
    def code(self, code, specifier=None):
        print 'code', specifier, code
    
    def heading_start(self, heading_type):
        print 'heading_start', heading_type
    
    def heading_end(self, heading_type):
        print 'heading_end', heading_type
        
    def paragraph_start(self):
        print 'paragraph_start'
    
    def paragraph_end(self):
        print 'paragraph_end'
    
    def orderedlist_start(self):
        print 'orderedlist_start'
    
    def orderedlist_item_start(self):
        print 'orderedlist_item_start'
    
    def orderedlist_item_end(self):
        print 'orderedlist_item_end'
    
    def orderedlist_end(self):
        print 'orderedlist_end'
    
    def unorderedlist_start(self):
        print 'unorderedlist_start'
    
    def unorderedlist_item_start(self):
        print 'unorderedlist_item_start'
    
    def unorderedlist_item_end(self):
        print 'unorderedlist_item_end'
    
    def unorderedlist_end(self):
        print 'unorderedlist_end'
    
    def definitionlist_start(self):
        print 'definitionlist_start'
        
    def definitionlist_item_term_start(self):
        print 'definitionlist_item_term_start'
        
    def definitionlist_item_term_end(self):
        print 'definitionlist_item_term_end'
        
    def definitionlist_item_definition_start(self):
        print 'definitionlist_item_definition_start'
        
    def definitionlist_item_definition_end(self):
        print 'definitionlist_item_definition_end'
        
    def definitionlist_item_start(self):
        print 'definitionlist_item_start'
        
    def definitionlist_item_end(self):
        print 'definitionlist_item_end'
        
    def definitionlist_end(self):
        print 'definitionlist_end'

    ##
    # inline handlers
    ##

    def inline_start(self):
        """Called when a block of inline text is parsed."""
        
    def inline_end(self):
        """Called at the end of parsing a block of inline text.""" 
    
    def inline_code(self, text):
        print 'inline_code', text
    
    def inline_emphasis_start(self):
        print 'inline_emphasis_start'
    
    def inline_emphasis_end(self):
        print 'inline_emphasis_end'
    
    def link_start(self, url):
        print 'link_start', url
    
    def link_end(self, url):
        print 'link_end', url
    
    def inline_text(self, text):
        print 'inline_text', text

    
