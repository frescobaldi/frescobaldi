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
Harvest information from a ly.document.DocumentBase instance.

"""

from __future__ import unicode_literals
from __future__ import absolute_import

import re
import collections
import functools
import itertools

import ly.lex.lilypond
import ly.pitch


def _cache(func):
    """Simple decorator caching the return value of a function."""
    @functools.wraps(func)
    def wrapper(self):
        try:
            return self._cache_[func]
        except AttributeError:
            self._cache_ = {}
        except KeyError:
            pass
        result = self._cache_[func] = func(self)
        return result
    return wrapper


class DocInfo(object):
    """Harvest information from a ly.document.DocumentBase instance.
    
    All tokens are saved in the tokens attribute as a tuple. Newline tokens 
    are added between all lines. All corresponding classes are in the 
    classes attribute as a tuple. This makes quick search and access possible.
    
    The tokens are requested from the document using the 
    tokens_with_position() method, so you can always locate them back in the 
    original document using their pos attribute.
    
    DocInfo does not update when the document changes, you should just 
    instantiate a new one.
    
    """
    def __init__(self, doc):
        """Initialize with ly.document.DocumentBase instance."""
        self._d = doc
        blocks = iter(doc)
        for b in blocks:
            tokens = doc.tokens_with_position(b)
            self.tokens = sum(map(
                lambda b: ((ly.lex.Newline('\n', doc.position(b) - 1),) +
                           doc.tokens_with_position(b)),
                blocks), tokens)
        self.classes = tuple(map(type, self.tokens))
    
    @property
    def document(self):
        return self._d
    
    def range(self, start=0, end=None):
        """Return a new instance of the DocInfo class for the selected range.
        
        Only the tokens completely contained within the range start..end are 
        added to the new instance. This can be used to perform fast searches 
        on a subset of a document.
        
        """
        if start == 0 and end is None:
            return self
        
        lo = 0
        hi = len(self.tokens)
        while lo < hi:
            mid = (lo + hi) // 2
            if start > self.tokens[mid].pos:
                lo = mid + 1
            else:
                hi = mid
        start = lo
        if end is not None:
            lo = 0
            hi = len(self.tokens)
            while lo < hi:
                mid = (lo + hi) // 2
                if end < self.tokens[mid].pos:
                    hi = mid
                else:
                    lo = mid + 1
            end = lo - 1            
        s = slice(start, end)
        n = type(self).__new__(type(self))
        n._d = self._d
        n.tokens = self.tokens[s]
        n.classes = self.classes[s]
        return n
    
    @_cache
    def mode(self):
        """Return the mode, e.g. "lilypond"."""
        return self._d.initial_state().mode()
    
    def find(self, token=None, cls=None, pos=0, endpos=-1):
        """Return the index of the first specified token and/or class after pos.
        
        If token is None, the cls should be specified. If cls is given, the 
        token should be an instance of the specified class. If endpos is 
        given, never searches beyond endpos. Returns -1 if the token is not 
        found.
        
        """
        if token is None:
            try:
                return self.classes.index(cls, pos, endpos)
            except ValueError:
                return -1
        elif cls is None:
            try:
                return self.tokens.index(token, pos, endpos)
            except ValueError:
                return -1
        else:
            while True:
                try:
                    i = self.tokens.index(token, pos, endpos)
                except ValueError:
                    return -1
                if cls == self.classes[i]:
                    return i
                pos = i + 1
    
    def find_all(self, token=None, cls=None, pos=0, endpos=-1):
        """Yield all indices of the first specified token and/or class after pos.
        
        If token is None, the cls should be specified. If cls is given, the 
        token should be an instance of the specified class. If endpos is 
        given, never searches beyond endpos. Returns -1 if the token is not 
        found.
        
        """
        while True:
            i = self.find(token, cls, pos, endpos)
            if i == -1:
                break
            yield i
            pos = i + 1
    
    @_cache
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

    @_cache
    def version(self):
        """Return the version_string() as a tuple of ints, e.g. (2, 16, 2)."""
        version = self.version_string()
        if version:
            return tuple(map(int, re.findall(r"\d+", version)))
        return ()

    @_cache
    def include_args(self):
        """The list of \\include command arguments."""
        result = []
        for i in self.find_all("\\include", ly.lex.lilypond.Keyword):
            tokens = iter(self.tokens[i+1:i+10])
            for token in tokens:
                if not isinstance(token, (ly.lex.Space, ly.lex.Comment)):
                    if token == '"':
                        result.append(''.join(itertools.takewhile(lambda t: t != '"', tokens)))
                    break
        return result
    
    @_cache
    def scheme_load_args(self):
        """The list of scheme (load) command arguments."""
        result = []
        for i in self.find_all("load", ly.lex.scheme.Keyword):
            tokens = iter(self.tokens[i+1:i+10])
            for token in tokens:
                if not isinstance(token, (ly.lex.Space, ly.lex.Comment)):
                    if token == '"':
                        result.append(''.join(itertools.takewhile(lambda t: t != '"', tokens)))
                    break
        return result
    
    @_cache
    def output_args(self):
        """The list of arguments of constructs defining the name of output documents.
        
        This looks at the \\bookOutputName, \\bookOutputSuffix and define 
        output-suffix commands.
        
        Every argument is a two tuple(type, argument) where type is either 
        "suffix" or "name".
        
        """
        result = []
        for arg_type, cmd, cls in (
                ("suffix", "output-suffix", ly.lex.scheme.Word),
                ("suffix", "\\bookOutputSuffix", ly.lex.lilypond.Command),
                ("name", "\\bookOutputName", ly.lex.lilypond.Command),
                ):
            for i in self.find_all(cmd, cls):
                tokens = iter(self.tokens[i+1:i+6])
                for t in tokens:
                    if t == '"':
                        arg = ''.join(itertools.takewhile(lambda t: t != '"', tokens))
                        result.append((arg_type, arg))
                        break
                    elif isinstance(t, (ly.lex.lilypond.SchemeStart,
                                            ly.lex.Space,
                                            ly.lex.Comment)):
                        continue
                    break
        return result
    
    @_cache
    def definitions(self):
        """The list of LilyPond identifiers the document defines."""
        result = []
        for i in self.find_all(None, ly.lex.lilypond.Name):
            if i == 0 or self.tokens[i-1] == '\n':
                result.append(self.tokens[i])
        return result
    
    @_cache
    def markup_definitions(self):
        """The list of markup command definitions in the document."""
        result = []
        # find bla = \markup { .. }
        for i in self.find_all(None, ly.lex.lilypond.Name):
            if i == 0 or self.tokens[i-1] == '\n':
                for t in self.tokens[i+1:i+6]:
                    if t == "\\markup":
                        result.append(self.tokens[i])
                    elif t == "=" or t.isspace():
                        continue
                    break
        # find #(define-markup-command construction
        for i in self.find_all('define-markup-command', ly.lex.scheme.Word):
            for t in self.tokens[i+1:i+6]:
                if isinstance(t, ly.lex.scheme.Word):
                    result.append(t)
                    break
        result.sort(key=lambda t: t.pos)
        return result

    @_cache
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
            lang = n.rsplit('.', 1)[0]
            if lang in languages:
                return lang
    
    @_cache
    def global_staff_size(self):
        """The global-staff-size, if set, else None."""
        i = self.find('set-global-staff-size', ly.lex.scheme.Function)
        if i != -1:
            try:
                return int(self.tokens[i+2])
            except (IndexError, ValueError):
                pass
    
    @_cache
    def complete(self):
        """Return whether the document is probably complete and could be compilable."""
        return self._d.state_end(self._d[len(self._d)-1]).depth() == 1
    
    @_cache
    def has_output(self):
        """Return True when the document probably generates output.
        
        I.e. has notes, rests, markup or other output-generating commands.
        
        """
        for t, c in (
                (None, ly.lex.lilypond.MarkupStart),
                (None, ly.lex.lilypond.Note),
                (None, ly.lex.lilypond.Rest),
                ('\\include', ly.lex.lilypond.Keyword),
                (None, ly.lex.lilypond.LyricMode),
            ):
            for i in self.find_all(t, c):
                return True
        return False
    
    def count_tokens(self, cls):
        """Return the number of tokens that are (a subclass) of the specified class.
        
        If you only want the number of instances of the exact class (not a 
        subclass of) you can use info.classes.count(cls), where info is a 
        DocInfo instance.
        
        """
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


