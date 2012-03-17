# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
The built-in help system.

Inherit from 'page' to make a help page.
See helpimpl.py.
"""

from PyQt4.QtGui import QDialogButtonBox, QKeySequence

from .helpimpl import page, action, shortcut, menu, link


def help(page):
    """Shows the help window with the specified page (class or name)."""
    window().displayHelp(page)


def window():
    global _browser
    try:
        return _browser
    except NameError:
        from . import browser
        _browser = browser.Window()
    return _browser


def addButton(box, page):
    """Adds a Help button to the specified QDialogButtonBox.
    
    When clicked or F1 (the system standard help key) is pressed,
    the specified help page (class or name) is opened.
    
    """
    box.addButton(QDialogButtonBox.Help).setShortcut(QKeySequence.HelpContents)
    box.helpRequested.connect(lambda: help(page))


def openWhatsThis(widget, enabled=True):
    """Open WhatsThis links in help browser if enabled is True (default)."""
    from . import whatsthis
    if enabled:
        widget.installEventFilter(whatsthis.handler)
    else:
        widget.removeEventFilter(whatsthis.handler)


