#!python

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

import itertools



def chop_left(string, chars=None):
    """Return the string that string.lstrip(chars) would chop off."""
    return string[:-len(string.lstrip(chars))]

def iter_split(text, separator):
    """Yield pairs of text before and after the separator.
    
    Text after the separator can be None.
    
    """
    blocks = iter(text.split(separator))
    return itertools.izip_longest(blocks, blocks)

def iter_split2(text, separator, separator2):
    """Yield pairs of text outside and inside the separator.
    
    Text after the separator can be None.
    This can be used to parse e.g. "text with [bracketed words] in it".
    
    """
    for prefix, rest in iter_split(text, separator):
        if rest:
            split_rest = rest.split(separator2, 1)
            if len(split_rest) == 1:
                yield prefix + separator + rest, None
            else:
                yield prefix, split_rest[0]
                yield split_rest[1], None
        else:
            yield prefix, rest


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
        prefix = lines[0].split(None, 1)[0]
        if prefix.startswith('='):
            self.handle_lists(indent)
            self.parse_heading(lines, prefix)
        elif self.is_ul_item(prefix):
            self.handle_lists(indent, 'ul')
            self.parse_ul(lines)
        elif self.is_ol_item(prefix):
            self.handle_lists(indent, 'ol')
            self.parse_ol(lines)
        elif self.is_dl_item(lines):
            self.handle_lists(indent, 'dl')
            self.parse_dl(lines)
        else:
            self.handle_lists(indent)
            self.parse_paragraph(lines)
    
    def is_ul_item(self, prefix):
        """Return True if the prefix is a unordered list prefix ("*")."""
        return prefix == '*'

    def is_ol_item(self, prefix):
        """Return True if the prefix is a ordered list prefix (number period)."""
        return prefix.endswith('.') and prefix[:-1].isdigit()
    
    def is_dl_item(self, lines):
        """Return True lines are a description list item."""
        return len(lines) > 1 and lines[1].lstrip().startswith(': ')
    
    def parse_paragraph(self, lines):
        """Parse a plain paragraph of text."""
        self.paragraph_start()
        self.parse_plain_text(lines)
        self.paragraph_end()
    
    def parse_heading(self, lines, prefix):
        """Parse a header text."""
        heading_type = 4 - min(prefix.count('='), 3)
        lines[0] = lines[0][len(prefix):]
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
            item[0] = item[0].split(None, 1)[1]
            self.orderedlist_item_start()
            if paragraph_item:
                self.paragraph_plain_text(item)
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
                self.paragraph_plain_text(item)
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
            if pred(line.split(None, 1)[0]):
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
            
    def paragraph_plain_text(self, lines):
        """Create a paragraph, adding the plain text."""
        self.paragraph_start()
        self.parse_plain_text(lines)
        self.paragraph_end()
    
    ##
    # inline level parsing
    ##
    
    def parse_plain_text(self, lines):
        """A continuous text block with possibly inline markup."""
        self.parse_inline_block('\n'.join(lines))
        
    def parse_inline_block(self, text):
        self.inline_start()
        for text, code in iter_split(text, '`'):
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
    # handlers
    ##
    
    def code(self, code, specifier=None):
        print 'code', specifier, code
    
    def plain_text(self, lines):
        """Write plain text"""
        print 'plain_text', lines
    
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

    
