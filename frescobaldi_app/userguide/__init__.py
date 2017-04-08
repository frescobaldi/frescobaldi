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
The Frescobaldi User Manual.
"""



def show(name=None):
    """Display the help browser and the specified help page.

    If no name is given, just display the browser.

    """
    global _browser
    try:
        _browser.displayPage(name)
    except NameError:
        from . import browser
        _browser = browser.Window()
        _browser.displayPage(name or 'index')

def addButton(box, name):
    """Adds a Help button to the specified QDialogButtonBox.

    When clicked or F1 (the system standard help key) is pressed,
    the specified help page is opened.

    """
    from PyQt5.QtGui import QKeySequence
    from PyQt5.QtWidgets import QDialogButtonBox
    box.addButton(QDialogButtonBox.Help).setShortcut(QKeySequence.HelpContents)
    box.helpRequested.connect(lambda: show(name))

def openWhatsThis(widget, enabled=True):
    """Open WhatsThis links in help browser if enabled is True (default)."""
    from . import whatsthis
    if enabled:
        widget.installEventFilter(whatsthis.handler)
    else:
        widget.removeEventFilter(whatsthis.handler)

def link(page):
    """Return a HTML link to the page."""
    from . import util
    return util.format_link(page)

def html(name):
    """Return the HTML body for the named help page."""
    from . import page
    return page.Page(name).body()

