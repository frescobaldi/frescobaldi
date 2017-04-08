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
Creates translatable strings for the Frescobaldi User Manual.

Writes a POT file.

"""


import sys
import textwrap

import simplemarkdown
import userguide.read


class Parser(userguide.read.Parser):
    def __init__(self, output_file=None):
        super(Parser, self).__init__()
        w = self.wrapper = textwrap.TextWrapper()
        w.break_long_words = False
        w.break_on_hyphens = False
        w.initial_indent = ''
        w.subsequent_indent = ''
        self._output_lines = []
        self.f = output_file

    def make_translation_strings(self, filename):
        self._curfilename = filename
        self.parse(userguide.read.document(filename)[0], lineno=1)

    def write(self, string):
        self.f.write(string.encode('utf8'))

    def translate(self, s):
        self.write('#: {0}:{1}\n'.format(self._curfilename, self.lineno))
        # is there markdown formatting in the string?
        formatting = False
        for c in '[]', '**', '``':
            for t, t2 in simplemarkdown.iter_split2(s, *c):
                formatting = bool(t2)
                break
            if formatting:
                self.write('#. NOTE: markdown formatting\n')
                break
        s = s.replace('\\', '\\\\').replace('"', '\\"')
        lines = self.wrapper.wrap(s)
        if len(lines) > 1:
            self.write('msgid ""\n')
            for l in lines[:-1]:
                self.write(('"' + l + ' "\n'))
            self.write(('"' + lines[-1] + '"\n'))
        else:
            self.write(('msgid "' + lines[0] + '"\n'))
        self.write('msgstr ""\n\n')


def md2pot(filename, md_files):
    with open(filename, 'wb') as f:
        p = Parser(f)
        for name in md_files:
            p.make_translation_strings(name)

if __name__ == '__main__':
    md2pot('/dev/stdout', sys.argv[1:])

