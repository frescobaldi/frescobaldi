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
                    del para[:]
            else:
                para.append(line)
        if para:
            self.parse_lines(para)
        self.end_list_if_needed()
    
    def parse_lines(self, para):
        """Parse a list of one or more lines without blank lines in between.
        
        Dispatches the lines to handle headings, lists or plain text paragraphs.
        
        """
        prefix = para[0].split(1)[0]
        if prefix.startswith('='):
            self.parse_heading(para, prefix)
        elif prefix == '*':
            self.parse_ul(para)
        elif prefix.endswith('.') and prefix[:-1].isdigit():
            self.parse_ol(para)
        elif len(para) > 1 and para[1].lstrip().startswith(': '):
            self.parse_dl(para)
        else:
            self.parse_paragraph(para)
    
    def parse_paragraph(self, para):
        """Parse a plain paragraph of text."""
        if not para[0][0].isspace():
            self.end_list_if_needed()
        self.paragraph_start()
        self.parse_plain_text(para)
        self.paragraph_end()
    
    def parse_heading(self, para, prefix):
        """Parse a header text."""
        prefix = chop_left(para[0], '=')
        para[0] = para[0][len(prefix):]
        self.heading_start(len(prefix))
        self.heading(para)
        self.heading_end()
    
    def parse_ol(self, para):
        """Parse ordered lists.
        
        Every line of the supplied group of lines is checked for a number,
        if they are separate items, no paragraph tags are put around the list
        items.
        
        """
            
    def parse_ul(self, para):
        """Parse unordered lists.
        
        Every line of the supplied group of lines is checked for an asterisk,
        if they are separate items, no paragraph tags are put around the list
        items.
        
        """
        
        
    def parse_dl(self, para):
        """Parse a definition list item."""
            
        
        

    
    ##
    # handlers
    ##
    
    def code(self, code, specifier=None):
        print 'code', specifier, code



            
        
        
