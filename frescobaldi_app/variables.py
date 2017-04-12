# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Infrastructure to get local variables embedded in comments in a document.
"""


import re

from PyQt5.QtCore import QTimer

import signals
import plugin


__all__ = ['get', 'update', 'manager', 'variables']


_variable_re = re.compile(r'\s*?([a-z]+(?:-[a-z]+)*):[ \t]*(.*?);')

_LINES = 5      # how many lines from top and bottom to scan for variables


def get(document, varname, default=None):
    """Get a single value from the document.

    If a default is given and the type is bool or int, the value is converted to the same type.
    If no value exists, the default is returned.

    """
    variables = manager(document).variables()
    try:
        return prepare(variables[varname], default)
    except KeyError:
        return default


def update(document, dictionary):
    """Updates the given dictionary with values from the document, using present values as default."""
    for name, value in manager(document).variables().items():
        if name in dictionary:
            dictionary[name] = prepare(value, dictionary[name])
    return dictionary


def manager(document):
    """Returns a VariableManager for this document."""
    return VariableManager.instance(document)


def variables(text):
    """Reads variables from the first and last _LINES lines of text."""
    lines = text.splitlines()
    start, count = 0, len(lines)
    d = {}
    if count > 2 * _LINES:
        d.update(m.group(1, 2) for n, m in positions(lines[:_LINES]))
        start = count - _LINES
    d.update(m.group(1, 2) for n, m in positions(lines[start:]))
    return d


class VariableManager(plugin.DocumentPlugin):
    """Caches variables in the document and monitors for changes.

    The changed() Signal is emitted some time after the list of variables has been changed.
    It is recommended to not change the document itself in response to this signal.

    """
    changed = signals.Signal() # without argument

    def __init__(self, document):
        self._updateTimer = QTimer(singleShot=True, timeout=self.slotTimeout)
        self._variables = self.readVariables()
        document.contentsChange.connect(self.slotContentsChange)
        document.closed.connect(self._updateTimer.stop) # just to be sure

    def slotTimeout(self):
        variables = self.readVariables()
        if variables != self._variables:
            self._variables = variables
            self.changed()

    def slotContentsChange(self, position, removed, added):
        """Called if the document changes."""
        if (self.document().findBlock(position).blockNumber() < _LINES or
            self.document().findBlock(position + added).blockNumber() > self.document().blockCount() - _LINES):
            self._updateTimer.start(500)

    def variables(self):
        """Returns the document variables (cached) as a dictionary. This method is recommended."""
        if self._updateTimer.isActive():
            # an update is pending, force it
            self._updateTimer.stop()
            self.slotTimeout()
        return self._variables

    def readVariables(self):
        """Reads the variables from the document and returns a dictionary. Internal."""
        count = self.document().blockCount()
        blocks = [self.document().firstBlock()]
        if count > _LINES * 2:
            blocks.append(self.document().findBlockByNumber(count - _LINES))
            count = _LINES
        def lines(block):
            for i in range(count):
                yield block.text()
                block = block.next()
        variables = {}
        for block in blocks:
            variables.update(m.group(1, 2) for n, m in positions(lines(block)))
        return variables


def positions(lines):
    """Lines should be an iterable returning lines of text.

    Returns an iterable yielding tuples (lineNum, matchObj) for every variable found.
    Every matchObj has group(1) pointing to the variable name and group(2) to the value.

    """
    commentstart = ''
    interesting = False
    for lineNum, text in enumerate(lines):
        # first check the line start
        start = 0
        if interesting:
            # already parsing? then skip comment start tokens
            m = re.match(r'\s*{0}'.format(re.escape(commentstart)), text)
            if m:
                start = m.end()
        else:
            # does the line have '-*-' ?
            m = re.search(r'(\S*)\s*-\*-', text)
            if m:
                interesting = True
                commentstart = m.group(1)
                start = m.end()
        # now parse the line
        if interesting:
            while True:
                m = _variable_re.match(text, start)
                if m:
                    yield lineNum, m
                    start = m.end()
                else:
                    if start < len(text) and not text[start:].isspace():
                        interesting = False
                    break


def prepare(value, default):
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


