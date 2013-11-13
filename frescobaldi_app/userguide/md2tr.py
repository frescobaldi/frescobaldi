# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
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
Creates translatable strings for the Frescobaldi User Manual.

This script is run standalone.

"""

from __future__ import unicode_literals

import sys
sys.path.insert(0, '..')

import textwrap

import simplemarkdown
import userguide.read 


class Parser(userguide.read.Parser):
    def __init__(self):
        super(Parser, self).__init__()
        w = self.wrapper = textwrap.TextWrapper()
        w.break_long_words = False
        w.break_on_hyphens = False
        w.initial_indent = '_("'
        w.subsequent_indent = '  " '
    
    def make_translation_strings(self, filename):
        self._output_lines = []
        self.parse(userguide.read.document(filename)[0])
        with open(filename + '.py', 'w') as f:
            f.write('#!python\n')
            f.write('# coding: utf-8\n')
            for l in self._output_lines:
                f.write((l + '\n').encode('utf-8'))

    def translate(self, s):
        # is there markdown formatting in the string?
        formatting = False
        for c in '[]', '**', '``':
            for t, t2 in simplemarkdown.iter_split2(s, *c):
                formatting = bool(t2)
                break
            if formatting:
                self._output_lines.append('#L10N NOTE: markdown formatting')
                break
        s = s.replace('\\', '\\\\').replace('"', '\\"')
        l = [i + '"' for i in self.wrapper.wrap(s)]
        l[-1] += ')'
        self._output_lines.extend(l)



def main():
    p = Parser()
    for name in sys.argv[1:]:
        p.make_translation_strings(name)

if __name__ == '__main__':
    main()

