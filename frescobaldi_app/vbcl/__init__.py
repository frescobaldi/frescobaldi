#!/usr/bin/env python3
#
# VBCL parser
#
# Andrew Bernard 2017

import re

# compile the match patterns
comment = re.compile(r"^\s*#")
nv_pair = re.compile(r"^(.*):\s+(.*)$")
long_text_start = re.compile(r"^(.*):\s+<")
long_text_end = re.compile(r"^\s*>")
list_items_start = re.compile(r"^(.*):\s+\[")
list_items_end = re.compile(r"^\s*\]")

defaults = {
    'name': 'NN',
    'display-name': 'NN',
    'short-description': None,
    'description': None,
    'website': None,
    'repository': None,
    'dependencies': [],
    'oll-core': '0.0.0',
    'maintainers': [],
    'version': '0.0.0',
    'license': 'None'
}


def set_defaults(d):
    """Ensure mandatory properties are set to 'empty' values."""
    for key in defaults:
        d[key] = d.get(key, defaults[key])
    return d


def parse(lines):
    """Returns a dictionary corresponding to a parsed VBCL string list."""
    d = dict()
    it = iter(lines)

    try:
        while True:
            line = next(it)
            # comments - discard
            if comment.search(line):
                continue
            else:
                # long text
                m = long_text_start.search(line)
                if m:
                    text = str()
                    while True:
                        line = next(it)
                        if long_text_end.search(line):
                            d[m.group(1)] = text.strip('\n')
                            break
                        text += (line.strip(' '))
                        text += '\n'
                        continue
                else:
                    # list
                    m = list_items_start.search(line)
                    if m:
                        items = list()
                        while True:
                            line = next(it)
                            if list_items_end.search(line):
                                d[m.group(1)] = items
                                break
                            items.append(line.strip(' \n'))
                            continue
                    else:
                        # name value pair
                        m = nv_pair.search(line)
                        if m:
                            d[m.group(1).strip()] = m.group(2).strip()
    except StopIteration:
        pass

    cfg = set_defaults(d)
    return cfg


def parse_file(filename):
    """Returns a dictionary corresponding to a parsed VBCL config file."""

    with open(filename) as f:
        cfg_dict = parse(f.read().split('\n'))
        return cfg_dict
