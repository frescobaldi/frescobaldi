#!python
#a very simple markdown-like parser

import re

_line_re = re.compile(
    r"^(?P<blockquote>(\s*>)*)"         # blockquote
    r"(?P<indent>\s*)"                  # initial space (indent)
    r"((?P<heading>=+)"                 # heading
    r"|(?P<verbatim>```(?P<specifier>.*?))\s*$" # verbatim
    r"|(?P<ul>[-*])(?=\s)"              # unordered list item
    r"|(?P<ol>\d+)\.?"                  # ordered list item
    r"|\[(?P<numbered_link>\d+)]"       # numbered link
        r"\s*(?P<url>\S+)\s*(.*?)\s*$"  # with url and title          
    r")?\s*(?P<text>.*)$"               # rest of the line
    )

def events(lines):
    """Yield events, parsing the lines."""
    in_paragraph = False
    in_verbatim = False
    blockquote_level = 0
    current_indent = [0]
    
    for l in lines:
        if not l or l.isspace():
            if in_paragraph:
                in_paragraph = False
                yield 'PARAGRAPH_END'
            continue
        l = l.expandtabs()
        
        d = _line_re.match(l).groupdict() # will always match
        
        # handle numbered inline links
        if d['numbered_link']:
            yield 'NUMBERED_LINK'
            yield int(d['numbered_link']), d['url'], d['title']
            continue
        
        # are we in a blockquote?
        # if the blockquote-count changes, start a new paragraph
        blockquote_count = d['blockquote'].count('>')
        if blockquote_count == 0 and in_paragraph and blockquote_level > 0:
            pass # keep the blockquote as long as we are in the paragraph
        elif blockquote_count < blockquote_level:
            if in_paragraph:
                yield 'PARAGRAPH_END'
            for blockquote_level in range(blockquote_level+1, blockquote_count+1):
                yield 'BLOCKQUOTE_START'
            if in_paragraph:
                yield 'PARAGRAPH_START'
        elif blockquote_count > blockquote_level:
            if in_paragraph:
                yield 'PARAGRAPH_END'
            for blockquote_level in range(blockquote_level-1, blockquote_count-1, -1):
                yield 'BLOCKQUOTE_END'
            if in_paragraph:
                yield 'PARAGRAPH_START'
        
        
        # verbatim
        if d['verbatim']:
            if in_verbatim:
                in_verbatim = False
                yield 'VERBATIM_END'
            else:
                in_verbatim = True
                if in_paragraph:
                    in_paragraph = False
                    yield 'PARAGRAPH_END'
                yield 'VERBATIM_START',
                yield d['specifier']
        
        
        if not in_paragraph:
            in_paragraph = True
            yield 'PARAGRAPH_START'

        # handle lists and verbatim etc
        
