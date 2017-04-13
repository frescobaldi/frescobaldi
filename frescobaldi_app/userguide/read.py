# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2014 by Wilbert Berendsen
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
Reading the Frescobaldi User Manual.
"""


import os
import re

import simplemarkdown


_variable_re = re.compile(r"\{([a-z]+(_[a-z]+)*)\}", re.UNICODE)
_document_split_re = re.compile(r'^#([A-Z]\w+)\s*$', re.MULTILINE)


def split_document(s):
    """Split the help page text and its #SUBDOCS and other headers.

    Returns a tuple consisting of the document text and a dictionary
    representing the #-named blocks; every value is the content of the block
    with a list of lines for every block.

    """
    l = _document_split_re.split(s)
    i = iter(l[1:])
    return l[0], dict((name, split_lines(value)) for name, value in zip(i, i))

def split_lines(s):
    """Split s in lines and strip() all lines. Returns a list."""
    return list(line.strip() for line in s.strip().splitlines())

def document(filename):
    if not filename.endswith('.md'):
        filename += '.md'
    if not os.path.isabs(filename):
        from . import __path__
        filename = os.path.join(__path__[0], filename)
    with open(filename, 'rb') as f:
        return split_document(f.read().decode('utf-8'))


class Parser(simplemarkdown.Parser):
    def parse_inline_text(self, text):
        text = text.replace('\n', ' ')
        if not text.startswith('!'):
            result = self.probably_translate(text)
            if result:
                super(Parser, self).parse_inline_text(result)
        else:
            result = []
            for t, tx in simplemarkdown.iter_split2(text[1:], '_(', ')_'):
                if t:
                    result.append(t)
                if tx:
                    result.append(self.probably_translate(tx))
            if None not in result:
                super(Parser, self).parse_inline_text(''.join(result))

    def probably_translate(self, s):
        """Translates the string if it is a sensible translatable message.

        The string is not translated if it does not contain any letters
        or if it is is a Python format string without any text outside the
        variable names.

        """
        pos = 0
        for m in _variable_re.finditer(s):
            if m.start() > pos and any(c.isalpha() for c in s[pos:m.start()]):
                return self.translate(s)
            pos = m.end()
        if pos < len(s) and any(c.isalpha() for c in s[pos:]):
            return self.translate(s)
        return s

    def translate(self, text):
        """Translates the text."""
        return _(text)


