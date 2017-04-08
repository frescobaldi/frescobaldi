# qutil.py -- various Qt4-related utility functions
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
Some Qt4-related utility functions.
"""


import contextlib
import re
import weakref

from PyQt5.QtCore import QEventLoop, QSettings, QSize, QTimer, Qt
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QProgressDialog

import appinfo


def saveDialogSize(dialog, key, default=QSize()):
    """Makes the size of a QDialog persistent.

    Resizes a QDialog from the setting saved in QSettings().value(key),
    defaulting to the optionally specified default size, and stores the
    size of the dialog at its finished() signal.

    Call this method at the end of the dialog constructor, when its
    widgets are instantiated.

    """
    size = QSettings().value(key, default, QSize)
    if size:
        dialog.resize(size)
    dialogref = weakref.ref(dialog)
    def save():
        dialog = dialogref()
        if dialog:
            QSettings().setValue(key, dialog.size())
    dialog.finished.connect(save)


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
    """Adds accelerators to the list of QActions (or QLabels used as buddy).

    Actions that have accelerators are skipped, the accelerators that they use
    are not used. This can be used for e.g. menus that are created on the fly.

    used is a sequence of already used accelerators (in lower case).

    """
    # filter out the actions that already have an accelerator
    todo = []
    used = set(used)
    for a in actions:
        if a.text():
            accel = getAccelerator(a.text())
            used.add(accel) if accel else todo.append(a)

    def finditers(action):
        """Yields two-tuples (priority, re.finditer object).

        The finditer object finds suitable accelerator positions.
        The priority can be used if multiple actions want the same shortcut.

        """
        text = action.text()
        if isinstance(action, QAction) and not action.shortcut().isEmpty():
            # if the action has a shortcut with A-Z or 0-9, match that character
            shortcut = action.shortcut()[action.shortcut().count()-1]
            key = shortcut & ~Qt.ALT & ~Qt.SHIFT & ~Qt.CTRL & ~Qt.META
            if 48 < key < 58 or 64 < key < 91 or 96 < key < 123:
                yield 0, re.finditer(r'\b{0:c}'.format(key), text, re.I)
        yield 1, re.finditer(r'\b\w', text)
        yield 2, re.finditer(r'\B\w', text)

    def find(action):
        """Yields three-tuples (priority, pos, accel) from finditers()."""
        for prio, matches in finditers(action):
            for m in matches:
                yield prio, m.start(), m.group().lower()

    todo = [(a, find(a)) for a in todo]

    while todo:
        # just pick the first accel for every action
        accels = {}
        for a, source in todo:
            for prio, pos, accel in source:
                if accel not in used:
                    accels.setdefault(accel, []).append((prio, pos, a, source))
                    break

        # now, fore every accel, if more than one action wants the same accel,
        # pick the action with the first priority or position, and try again the
        # other actions.
        todo = []
        used.update(accels)
        for action_list in accels.values():
            action_list.sort(key=lambda i: i[:2])
            pos, a = action_list[0][1:3]
            a.setText(a.text()[:pos] + '&' + a.text()[pos:])
            todo.extend((a, source) for prio, pos, a, source in action_list[1:])


def getAccelerator(text):
    """Returns the accelerator (in lower case) contained in the text, if any.

    An accelerator is a character preceded by an ampersand &.

    """
    m = re.search(r'&(\w)', text.replace('&&', ''))
    if m:
        return m.group(1).lower()


def removeAccelerator(text):
    """Removes accelerator ampersands from a QAction.text() string."""
    return text.replace('&&', '\0').replace('&', '').replace('\0', '&')


def removeShortcut(action, key):
    """Removes matching QKeySequence from the list of the action."""
    key = QKeySequence(key)
    shortcuts = action.shortcuts()
    for s in action.shortcuts():
        if key.matches(s) or s.matches(key):
            shortcuts.remove(s)
    action.setShortcuts(shortcuts)


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
    """Returns a QColor as if color1 is painted on color2 with alpha value mix (0.0 - 1.0)."""
    r1, g1, b1 = color1.red(), color1.green(), color1.blue()
    r2, g2, b2 = color2.red(), color2.green(), color2.blue()
    r = r1 * mix + r2 * (1 - mix)
    g = g1 * mix + g2 * (1 - mix)
    b = b1 * mix + b2 * (1 - mix)
    return QColor(r, g, b)


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


def waitForSignal(signal, message="", timeout=0):
    """Waits (max timeout msecs if given) for a signal to be emitted.

    It the waiting lasts more than 2 seconds, a progress dialog is displayed
    with the message.

    Returns True if the signal was emitted.
    Return False if the wait timed out or the dialog was canceled by the user.

    """
    loop = QEventLoop()
    dlg = QProgressDialog(minimum=0, maximum=0, labelText=message)
    dlg.setWindowTitle(appinfo.appname)
    dlg.setWindowModality(Qt.ApplicationModal)
    QTimer.singleShot(2000, dlg.show)
    dlg.canceled.connect(loop.quit)
    if timeout:
        QTimer.singleShot(timeout, dlg.cancel)
    stop = lambda: loop.quit()
    signal.connect(stop)
    loop.exec_()
    signal.disconnect(stop)
    dlg.hide()
    dlg.deleteLater()
    return not dlg.wasCanceled()


