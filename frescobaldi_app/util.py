# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Some utility functions.

The functions that are directly Qt-related use camelCaps,
but the other utility functions use the python_convention.
"""

from __future__ import unicode_literals

import codecs
import contextlib
import glob
import itertools
import os
import re
import weakref

from PyQt4.QtCore import QSettings, QSize, Qt
from PyQt4.QtGui import QApplication, QColor

import info
import variables


def iswritable(path):
    """Returns True if the path can be written to or created."""
    return ((os.path.exists(path) and os.access(path, os.W_OK))
            or os.access(os.path.dirname(path), os.W_OK))


if os.name == 'nt':
    def equal_paths(p1, p2):
        """Returns True if the paths are equal (case and separator insensitive)."""
        return p1.lower().replace('\\', '/') == p2.lower().replace('\\', '/')
else:
    def equal_paths(p1, p2):
        """Returns True if the paths are equal."""
        return p1 == p2
        

def homify(path):
    """Replaces the homedirectory (if present) in the path with a tilde (~)."""
    homedir = os.path.expanduser('~')
    if equal_paths(path[:len(homedir)+1], homedir + '/'):
        path = "~" + path[len(homedir):]
    return path


def files(basenames, extension = '.*'):
    """Yields filenames with the given basenames matching the given extension."""
    def source():
        for name in basenames:
            name = name.replace('[', '[[]').replace('?', '[?]').replace('*', '[*]')
            yield glob.iglob(name + extension)
            yield sorted(glob.iglob(name + '-*[0-9]' + extension), key=naturalsort)
    return itertools.chain.from_iterable(source())


def group_files(names, groups):
    """Groups the given filenames by extension.
    
    names: an iterable (or list or tuple) yielding filenames.
    groups: an iterable (or list or tuple) yielding strings.
    
    Each group is a string containing one or more extensions, without period,
    separated by a space. If a filename has one of the extensions in the group,
    the names is added to the list of file for that group.
    An exclamation sign at the beginning of the string negates the match.
    
    Yields the same number of lists as there were group arguments.
    
    """
    allgroups = []
    for group in groups:
        if group.startswith('!'):
            pred = lambda e, ext=group[1:].split(): e not in ext
        else:
            pred = lambda e, ext=group.split(): e in ext
        allgroups.append(([], pred))
    for name in names:
        ext = os.path.splitext(name)[1][1:].lower()
        for files, pred in allgroups:
            if pred(ext):
                files.append(name)
                break
    return (files for files, pred in allgroups)


@contextlib.contextmanager
def signalsBlocked(*objs):
    """Blocks the signals of the given QObjects and then returns a contextmanager"""
    blocks = [obj.blockSignals(True) for obj in objs]
    try:
        yield
    finally:
        for obj, block in zip(objs, blocks):
            obj.blockSignals(block)


@contextlib.contextmanager
def deleteLater(*qobjs):
    """Performs code and calls deleteLater() when done on the specified QObjects."""
    try:
        yield
    finally:
        for obj in qobjs:
            obj.deleteLater()


def addAccelerators(actions, used=[]):
    """Adds accelerators to the list of actions.
    
    Actions that have accelerators are skipped, the accelerators that they use
    are not used. This can be used for e.g. menus that are created on the fly.
    
    used is a sequence of already used accelerators (in lower case).
    
    """
    todo = []
    used = list(used)
    for a in actions:
        if a.text():
            accel = getAccelerator(a.text())
            used.append(accel) if accel else todo.append(a)
    for a in todo:
        text = a.text()
        for m in itertools.chain(re.finditer(r'\b\w', text),
                                 re.finditer(r'\B\w', text)):
            if m.group().lower() not in used:
                used.append(m.group().lower())
                a.setText(text[:m.start()] + '&' + text[m.start():])
                break


def getAccelerator(text):
    """Returns the accelerator (in lower case) contained in the text, if any.
    
    An accelerator is a character preceded by an ampersand &.
    
    """
    m = re.search(r'(?<!&)&(\w)', text)
    if m:
        return m.group(1).lower()


def addcolor(color, r, g, b):
    """Adds r, g and b values to the given color and returns a new QColor instance."""
    r += color.red()
    g += color.green()
    b += color.blue()
    d = max(r, g, b) - 255
    if d > 0:
        r = max(0, r - d)
        g = max(0, g - d)
        b = max(0, b - d)
    return QColor(r, g, b)


def mixcolor(color1, color2, mix):
    """Returns a QColor as if color1 is painted on color1 with alpha value mix (0.0 - 1.0)."""
    r1, g1, b1 = color1.red(), color1.green(), color1.blue()
    r2, g2, b2 = color2.red(), color2.green(), color2.blue()
    r = r1 * mix + r2 * (1 - mix)
    g = g1 * mix + g2 * (1 - mix)
    b = b1 * mix + b2 * (1 - mix)
    return QColor(r, g, b)


def naturalsort(text):
    """Returns a key for the list.sort() method.
    
    Intended to sort strings in a human way, for e.g. version numbers.
    
    """
    return tuple(int(s) if s.isdigit() else s for s in re.split(r'(\d+)', text))


def uniq(iterable):
    """Returns an iterable, removing duplicates. The items should be hashable."""
    s, l = set(), 0
    for i in iterable:
        s.add(i)
        if len(s) > l:
            yield i
            l = len(s)


def decode(data, encoding=None):
    """Returns the unicode text from the encoded, data. Prefer encoding if given.
    
    The text is also checked for the 'coding' document variable.
    
    """
    encodings = [encoding] if encoding else []
    for bom, encoding in (
        (codecs.BOM_UTF8, 'utf-8'),
        (codecs.BOM_UTF16_LE, 'utf_16_le'),
        (codecs.BOM_UTF16_BE, 'utf_16_be'),
            ):
        if data.startswith(bom):
            encodings.append(encoding)
            data = data[len(bom):]
            break
    else:
        var_coding = variables.variables(data).get("coding")
        if var_coding:
            encodings.append(var_coding)
    encodings.append('utf-8')
    encodings.append('latin1')
    
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except (UnicodeError, LookupError):
            continue
    return data.decode('utf-8', 'replace')


def encode(text, default_encoding='utf-8'):
    """Returns the bytes representing the text, encoded.
    
    Looks at the 'coding' variable to determine the encoding,
    otherwise falls back to the given default encoding, defaulting to 'utf-8'.
    
    """
    encoding = variables.variables(text).get("coding")
    if encoding:
        try:
            return text.encode(encoding)
        except (LookupError, UnicodeError):
            pass
    return text.encode(default_encoding)


def saveDialogSize(dialog, key, default=QSize()):
    """Makes the size of a QDialog persistent.
    
    Resizes a QDialog from the setting saved in QSettings().value(key),
    defaulting to the optionally specified default size, and stores the
    size of the dialog at its finished() signal.
    
    Call this method at the end of the dialog constructor, when its
    widgets are instantiated.
    
    """
    size = QSettings().value(key, default)
    if size:
        dialog.resize(size)
    dialogref = weakref.ref(dialog)
    def save():
        dialog = dialogref()
        if dialog:
            QSettings().setValue(key, dialog.size())
    dialog.finished.connect(save)


@contextlib.contextmanager
def busyCursor(cursor=Qt.WaitCursor, processEvents=True):
    """Performs the contained code using a busy cursor.
    
    The default cursor used is Qt.WaitCursor.
    If processEvents is True (the default), QApplication.processEvents()
    will be called once before the contained code is executed.
    
    """
    QApplication.setOverrideCursor(cursor)
    processEvents and QApplication.processEvents()
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


def tempdir():
    """Returns a temporary directory that is erased on app quit."""
    import tempfile
    global _tempdir
    try:
        _tempdir
    except NameError:
        _tempdir = tempfile.mkdtemp(prefix = info.name +'-')
        import atexit
        @atexit.register
        def remove():
            import shutil
            shutil.rmtree(_tempdir, ignore_errors=True)
    return tempfile.mkdtemp(dir=_tempdir)


