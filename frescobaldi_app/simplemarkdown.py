#!python

"""
This is a very basic markdown-like parser.

It currently does not support blockquotes.

It supports different ways to iterate over the parsed text fragments and events.

It supports the following blocklevel items:

=== heading 1

== heading 2

= heading 3

plain text paragraph

* unordered list

1. ordered list

definition
: list explanation blabla


```language
code
```

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


class SimpleMarkdown(object):
    def __init__(self):
        self._lists = []
    
    def parse(self, text):
        """Parse the text and call methods on certain events."""
        # split in code and non-code blocks
        blocks = iter(text.split('\n```'))
        for text, code in itertools.izip_longest(blocks, blocks):
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
        
        Just calls parse_lines() with lists of connected non-blank lines.
        
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
    
    def parse_lines(self, para):
        """Parse a list of one or more lines without blank lines in between.
        
        Dispatches the lines to handle headings, lists or plain text paragraphs.
        
        """
        indent = len(chop_left(para[0]))
        prefix = para[0].split(None, 1)[0]
        if prefix.startswith('='):
            self.handle_lists(indent)
            self.parse_heading(para, prefix)
        elif self.is_ul_item(prefix):
            self.handle_lists(indent, 'ul')
            self.parse_ul(para)
        elif self.is_ol_item(prefix):
            self.handle_lists(indent, 'ol')
            self.parse_ol(para)
        elif len(para) > 1 and para[1].lstrip().startswith(': '):
            self.handle_lists(indent, 'dl')
            self.parse_dl(para)
        else:
            self.handle_lists(indent)
            self.parse_paragraph(para)
    
    def is_ul_item(self, prefix):
        """Return True if the prefix is a unordered list prefix ("*")."""
        return prefix == '*'

    def is_ol_item(self, prefix):
        """Return True if the prefix is a ordered list prefix (number period)."""
        return prefix.endswith('.') and prefix[:-1].isdigit()
    
    def parse_paragraph(self, para):
        """Parse a plain paragraph of text."""
        self.paragraph_start()
        self.parse_plain_text(para)
        self.paragraph_end()
    
    def parse_heading(self, para, prefix):
        """Parse a header text."""
        prefix = chop_left(para[0], '= ')
        heading_type = 4 - min(prefix.count('='), 3)
        para[0] = para[0][len(prefix):]
        self.heading_start(heading_type)
        self.parse_plain_text(para)
        self.heading_end(heading_type)
    
    def parse_ol(self, para):
        """Parse ordered lists.
        
        Every line of the supplied group of lines is checked for a number,
        if they are separate items, no paragraph tags are put around the list
        items.
        
        """
        # split in list items
        items = self.split_list_items(para, self.is_ol_item)
        paragraph_item = len(items) == 1
        for item in items:
            item[0] = item[0].split(None, 1)[1]
            self.orderedlist_item_start()
            if paragraph_item:
                self.paragraph_plain_text(item)
            else:
                self.parse_plain_text(item)
            self.orderedlist_item_end()
            
    def parse_ul(self, para):
        """Parse unordered lists.
        
        Every line of the supplied group of lines is checked for an asterisk,
        if they are separate items, no paragraph tags are put around the list
        items.
        
        """
        items = self.split_list_items(para, self.is_ul_item)
        paragraph_item = len(items) == 1
        for item in items:
            self.unorderedlist_item_start()
            if paragraph_item:
                self.paragraph_plain_text(item)
            else:
                self.parse_plain_text(item)
            self.unorderedlist_item_end()
    
    def split_list_items(self, para, pred):
        """Returns lists of lines that each represent a list item.
        
        The pred function should return true for a line that has an item prefix.
        
        """
        items = []
        item = []
        for line in para:
            if pred(line.split(None, 1)[0]):
                if item:
                    items.append(item)
                item = [line.split(None, 1)[1]]
            else:
                item.append(line)
        if item:
            items.append(item)
        return items
        
    def parse_dl(self, para):
        """Parse a definition list item."""
        definition = para[0]
        para[1] = para[1].split(':', 1)[1]
        self.definitionlist_item_start()
        self.definitionlist_item_term_start()
        self.parse_plain_text([definition])
        self.definitionlist_item_term_end()
        self.definitionlist_item_definition_start()
        self.parse_plain_text(para[1:])
        self.definitionlist_item_definition_end()
        self.definitionlist_item_end()
    
    def parse_plain_text(self, lines):
        """A continuous text block with possibly inline markup."""
        # TODO handle inline markup
        self.plain_text(lines)
        
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
            
    def paragraph_plain_text(self, para):
        """Create a paragraph, adding the plain text."""
        self.paragraph_start()
        self.parse_plain_text(para)
        self.paragraph_end()
    
        

    
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



