# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Infrastructure to get local variables embedded in comments in a document.
"""

import re
import weakref

import ly.tokenize
import tokeniter

__all__ = ['get', 'update']


def get(document, varname, default=None):
    """Get a single value from the document.
    
    If a default is given and the type is bool or int, the value is converted to the same type.
    If no value exists, the default is returned.
    
    """
    variables = _manager(document).variables()
    try:
        return _prepare(variables[varname], default)
    except KeyError:
        return default


def update(document, dictionary):
    """Updates the given dictionary with values from the document, using present values as default."""
    for name, value in _manager(document).variables().items():
        if name in dictionary:
            dictionary[name] = _prepare(value, dictionary[name])
    return dictionary


def _prepare(value, default):
    """Try to convert the value (which is a string) to the type of the default value.
    
    If (for int and bool) that fails, returns the default, otherwise returns the string unchanged.
    
    """
    if isinstance(default, bool):
        if value.lower() in ('true', 'yes', 'on', 't', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', 'f', '0'):
            return False
        return default
    elif isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    return value


_var_mgrs = weakref.WeakKeyDictionary()


def _manager(document):
    """Returns a VariableManager for this document."""
    try:
        return _var_mgrs[document]
    except KeyError:
        result = _var_mgrs[document] = _VariableManager(document)
    return result


# how many lines to watch from beginning to end
LINES = 10

class _VariableManager(object):
    """ Caches variables for documents. """
    def __init__(self, document):
        self.document = weakref.ref(document)
        _var_mgrs[document] = self
        self._variables = None
        
    def slotContentsChange(self, position, removed, added):
        """Called if the document changes."""
        if (self.document().findBlock(position).blockNumber() < LINES or
            self.document().findBlock(position + added).blockNumber() > self.document().blockCount() - LINES):
            self._variables = None
            # disconnect, connect when variables are requested again
            self.document().contentsChange.disconnect(self.slotContentsChange)
            
    def variables(self):
        if self._variables is None:
            self._variables = {}
            interesting = False
            for block in self.interestingBlocks():
                comment = []
                for token in tokeniter.tokens(block):
                    if isinstance(token, ly.tokenize.CommentBase):
                        if not interesting and '-*-' in token:
                            interesting = True
                        if interesting:
                            comment.append(token)
                    else:
                        interesting = False
                self._variables.update(re.findall(r'([a-z]+(?:-[a-z]+)*):[ \t]*(.*?);', ''.join(comment)))
            self.document().contentsChange.connect(self.slotContentsChange)
        return self._variables
    
    def interestingBlocks(self):
        """Iterate over the first 5 and last 5 blocks."""
        lines = self.document().blockCount()
        for num in filter(lambda i: i < LINES or i > lines-LINES, range(lines)):
            yield self.document().findBlockByNumber(num)


