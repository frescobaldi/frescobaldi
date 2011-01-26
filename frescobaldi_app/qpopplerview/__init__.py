# This file is part of the qpopplerview package.
#
# Copyright (c) 2010, 2011 by Wilbert Berendsen
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
This is a viewer widget for anything Poppler can display (PDF).

It needs the Python binding to Poppler-Qt4: python-poppler-qt4 which provides
the popplerqt4 module.

The View (see view.py) is a QScrollArea that uses a Surface (see surface.py) as
its widget.  The Surface has a Layout (see layout.py) that positions Page
objects (see page.py).

A Page represents a single page from a Poppler.Document. Its rect() method
contains the position and size to draw it. Its computeSize() method computes its
size, and the Layout is expected to set its position.

So the long route to view a PDF document is:
- get a Poppler.Document instance (and set its rendering hints)
- create Page objects for every page you want to show
- add the Page objects to a Layout object (you can add pages from multiple PDF
  documents in one layout)
- get a Surface object and use Surface.setPageLayout() to let the Surface use
  our Layout
- create a View widget and use View.setSurface() to let it use our Surface.

Of course there are some convenience shortcuts:
- View.load(document) loads all pages from a document in a default Layout
- Layout.load(document) also loads all page objects from a document


"""

# viewModes:
FixedScale = 0
FitWidth   = 1
FitHeight  = 2
FitBoth    = FitHeight | FitWidth


from .view import View
from .page import Page
from .layout import AbstractLayout, Layout
from .surface import Surface
from . import cache

