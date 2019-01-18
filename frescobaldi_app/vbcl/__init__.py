# This file is part of the Frescobaldi Extensions project,
# https://github.com/frescobaldi-extensions
#
# Copyright (c) 2018 by Urs Liska and others
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
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

# VBCL parser
# Andrew Bernard 2017

import re

# compile the match patterns
comment = re.compile(r"^\s*#")
nv_pair = re.compile(r"^(.*):\s+(.*)$")
long_text_start = re.compile(r"^(.*):\s+<")
long_text_end = re.compile(r"^\s*>")
list_items_start = re.compile(r"^(.*):\s+\[")
list_items_end = re.compile(r"^\s*\]")


def check_mandatory_keys(d, mandatory_keys):
    """Check if all mandatory keys are present. Raise a ValueError if not."""
    if mandatory_keys:
        missing = []
        for key in mandatory_keys:
            if not key in d.keys():
                missing.append(key)
        if missing:
            raise ValueError(
            _("VBCL Error: Missing mandatory key(s) '{}'".format(
                ', '.join(missing))))

def set_defaults(d, defaults):
    """Ensure optional properties are set to default/'empty' values."""
    for key in defaults:
        d[key] = d.get(key, defaults[key])


def parse(lines, mandatory_keys, defaults):
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

    check_mandatory_keys(d, mandatory_keys)
    set_defaults(d, defaults)
    return d


def parse_file(filename, mandatory_keys=None, defaults=None):
    """Returns a dictionary corresponding to a parsed VBCL config file.
    Raises an exception if the given file doesn't exist or isn't readable"""

    with open(filename) as f:
        cfg_dict = parse(f.read().split('\n'), mandatory_keys, defaults)
        return cfg_dict
