#!python
#a very simple markdown-like parser


from __future__ import unicode_literals

import re

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


def events(lines):
    """Yield events, parsing the lines."""
    in_paragraph = False
    in_verbatim = False
    blockquote_level = 0
    current_indent = [0]
    
    for line in lines:
        l = line.expandtabs()
        
        d = _line_re.match(l).groupdict() # will always match
        
        if in_verbatim:
            if d['verbatim']:
                in_verbatim = False
                yield 'verbatim_end',
            else:
                yield 'verbatim_line', line
            continue
        
        if not d['prefix'] and not d['text']:
            # blank line
            if in_paragraph:
                in_paragraph = False
                yield 'paragraph_end',
            continue
            
        # handle numbered inline links
        if d['numbered_link']:
            yield 'numbered_link', int(d['numbered_link']), d['url'], d['title']
            continue
        
        # are we in a blockquote?
        # if the blockquote-count changes, start a new paragraph
        blockquote_count = d['blockquote'].count('>')
        if blockquote_count == 0 and in_paragraph and blockquote_level > 0:
            pass # keep the blockquote as long as we are in the paragraph
        elif blockquote_count > blockquote_level:
            if in_paragraph:
                yield 'paragraph_end',
            for blockquote_level in range(blockquote_level+1, blockquote_count+1):
                yield 'blockquote_start',
            if in_paragraph:
                yield 'paragraph_start', 
        elif blockquote_count < blockquote_level:
            if in_paragraph:
                yield 'paragraph_end',
            for blockquote_level in range(blockquote_level-1, blockquote_count-1, -1):
                yield 'blockquote_end',
            if in_paragraph:
                yield 'paragraph_start',
        
        
        # verbatim
        if d['verbatim']:
            in_verbatim = True
            if in_paragraph:
                in_paragraph = False
                yield 'paragraph_end',
            yield 'verbatim_start', d['specifier']
            continue
        
        if not in_paragraph:
            in_paragraph = True
            yield 'paragraph_start',

        # handle lists
        
        # finally, handle character level text
        yield 'text', d['text']
    
    # ending
    if in_verbatim:
        yield 'verbatim_end',
    if in_paragraph:
        yield 'paragraph_end',
    while blockquote_level > 0:
        yield 'blockquote_end',
        blockquote_level -= 1

