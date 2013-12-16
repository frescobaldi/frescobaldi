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
Harvest information from a ly.document.DocumentBase instance.

"""

from __future__ import unicode_literals
from __future__ import absolute_import

import collections
import itertools

import ly.lex.lilypond
import ly.pitch


class DocInfo(object):
    """Harvest information from a ly.document.DocumentBase instance.
    
    All tokens are saved in the tokens attribute as a tuple.
    All corresponding classes are in the classes attribute as a tuple.
    This makes quick search and access possible.
    
    The tokens are requested from the document using the 
    tokens_with_position() method, so you can always locate them back in the 
    original document using their pos attribute.
    
    DocInfo does not update when the document changes, you should just 
    instantiate a new one.
    
    """
    def __init__(self, doc):
        """Initialize with ly.document.DocumentBase instance."""
        self._d = doc
        self.tokens = sum(map(doc.tokens_with_position, doc), ())
        self.classes = tuple(map(type, self.tokens))
    
    @property
    def document(self):
        return self._d
    
    def mode(self):
        """Return the mode, e.g. "lilypond"."""
        return self._d.initial_state().mode()
    
    def find(self, token, cls=None, pos=0, endpos=-1):
        """Return the index of the first specified token after pos.
        
        If cls is given, the token should be an instance of the specified 
        class. If endpos is given, never searches beyond endpos. Returns -1 
        if the token is not found.
        
        """
        while True:
            try:
                i = self.tokens.index(token, pos, endpos)
            except ValueError:
                return -1
            if not cls or issubclass(self.classes[i], cls):
                return i
            pos = i + 1
            
    def find_all(self, token, cls=None, pos=0, endpos=-1):
        """Yield all indices of the first specified token after pos.
        
        If cls is given, the token should be an instance of the specified 
        class. If endpos is given, never searches beyond endpos. Returns -1 
        if the token is not found.
        
        """
        while True:
            i = self.find(token, cls, pos, endpos)
            if i == -1:
                break
            yield i
            pos = i + 1
    
    def version_string(self):
        """Return the version as a string, e.g. "2.19.8".
        
        Looks for the \\version LilyPond command. The string is returned 
        without quotes. Returns None if there was no \\version command found.
        
        """
        i = self.find("\\version", ly.lex.lilypond.Keyword)
        if i != -1:
            tokens = iter(self.tokens[i+1:i+10])
            for t in tokens:
                if not isinstance(t, (ly.lex.Space, ly.lex.Comment)):
                    if t == '"':
                        pred = lambda t: t != '"'
                    else:
                        pred = lambda t: not isinstance(t, (ly.lex.Space, ly.lex.Comment))
                    return ''.join(itertools.takewhile(pred, tokens))

    def include_args(self):
        """Yield the arguments of \\include commands in the token stream."""
        for i in self.find_all("\\include", ly.lex.lilypond.Keyword):
            tokens = iter(self.tokens[i+1:i+10])
            for token in tokens:
                if not isinstance(token, (ly.lex.Space, ly.lex.Comment)):
                    if token == '"':
                        yield ''.join(itertools.takewhile(lambda t: t != '"', tokens))
                    break

    def language(self):
        """The pitch language, None if not set in the document."""
        languages = ly.pitch.pitchInfo.keys()
        for i in self.find_all("\\language", ly.lex.lilypond.Keyword):
            for t in self.tokens[i+1:i+10]:
                if isinstance(t, ly.lex.Space):
                    continue
                elif t == '"':
                    continue
                if t in languages:
                    return t
        for n in self.include_args():
            lang = t.rsplit('.', 1)[0]
            if lang in languages:
                return lang
    
    def count_tokens(self, cls):
        """Return the number of tokens that are a subclass of the specified class."""
        return sum(map(lambda c: issubclass(c, cls), self.classes), False)

    def counted_tokens(self):
        """Return a dictionary mapping classes to the number of instances of that class."""
        try:
            # only in Python 2.7+
            return collections.Counter(self.classes)
        except AttributeError:
            # for the time being also support Python 2.6
            d = collections.defaultdict(int)
            for c in self.classes:
                d[c] += 1
            return d


