#!python
#a very simple markdown-like parser


from __future__ import unicode_literals

import re

class Line(object):
    """Represent a line of text."""
    tab_width = 8
    _line_re = re.compile(
        r"^(?P<blockquote>(\s*>)*)"         # blockquote
        r"(?P<indent>\s*)"                  # initial space (indent)
        r"(?P<prefix>(?P<heading>=+)"                 # heading
        r"|(?P<verbatim>```(?P<specifier>.*?))\s*$" # verbatim
        r"|(?P<ul>[-*])(?=\s)"              # unordered list item
        r"|(?P<ol>\d+)\.?"                  # ordered list item
        r"|\[(?P<numbered_link>\d+)]"       # numbered link
            r"\s*(?P<url>\S+)\s*(?P<title>.*?)\s*$"  # with url and title          
        r")?\s*(?P<text>.*)$"               # rest of the line
        , re.UNICODE)

    def __init__(self, text):
        self.orig_text = text
        self.line = l = text.expandtabs(self.tab_width)
        self.d = self._line_re.match(l).groupdict()
    
    def isblank(self):
        return not self.prefix and not self.text
    
    def __getattr__(self, name):
        return self.d[name]

        
def iter2(i):
    """Yield item, next_item from iterable.
    
    Together with the last item, None is yielded.
    
    """
    i = iter(i)
    for i2 in i:
        for i3 in i:
            yield i2, i3
            i2 = i3
        yield i2, None


class SimpleMarkdown(object):
    
    Line = Line
    
    def parse(self, lines):
        """Yield events, parsing the lines."""
        in_paragraph = False
        in_verbatim = False
        blockquote_level = 0
        current_indent = [0]
        
        for l, n in iter2(self.Line(l) for l in lines):
            
            if in_verbatim:
                if l.verbatim:
                    in_verbatim = False
                    self.verbatim_end()
                else:
                    self.verbatim_line(line)
                continue
            
            if l.isblank():
                if in_paragraph:
                    in_paragraph = False
                    self.paragraph_end()
                continue
                
            # handle numbered inline links
            if l.numbered_link:
                self.numbered_link(int(l.numbered_link), l.url, l.title)
                continue
            
            # are we in a blockquote?
            # if the blockquote-count changes, start a new paragraph
            blockquote_count = l.blockquote.count('>')
            if blockquote_count == 0 and in_paragraph and blockquote_level > 0:
                pass # keep the blockquote as long as we are in the paragraph
            elif blockquote_count > blockquote_level:
                if in_paragraph:
                    self.paragraph_end()
                for blockquote_level in range(blockquote_level+1, blockquote_count+1):
                    self.blockquote_start()
                if in_paragraph:
                    self.paragraph_start()
            elif blockquote_count < blockquote_level:
                if in_paragraph:
                    self.paragraph_end()
                for blockquote_level in range(blockquote_level-1, blockquote_count-1, -1):
                    self.blockquote_end()
                if in_paragraph:
                    self.paragraph_start()
            
            
            # verbatim
            if l.verbatim:
                in_verbatim = True
                if in_paragraph:
                    in_paragraph = False
                    self.paragraph_end()
                self.verbatim_start(l.specifier)
                continue
            
            if not in_paragraph:
                in_paragraph = True
                self.paragraph_start()

            # handle lists
            
            # finally, handle character level text
            self.text(l.text)
        
        # ending
        if in_verbatim:
            self.verbatim_end()
        if in_paragraph:
            self.paragraph_end()
        while blockquote_level > 0:
            self.blockquote_end()
            blockquote_level -= 1


    def verbatim_start(self, specifier):
        print 'verbatim_start', specifier
        
    def verbatim_end(self):
        print 'verbatim_end'
    
    def verbatim_line(self, text):
        print 'verbatim_line', text
    
    def paragraph_start(self):
        print 'paragraph_start'

    def paragraph_end(self):
        print 'paragraph_end'
        
    def blockquote_start(self):
        print 'blockquote_start'
    
    def blockquote_end(self):
        print 'blockquote_end'
    
    def numbered_link(self, num, url, text):
        print 'numbered_link', num, url, text
    
    def text(self, text):
        print 'text', text


    
