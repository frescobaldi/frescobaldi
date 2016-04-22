# This file is part of the qpopplerview package.
#
# Copyright (c) 2010 - 2014 by Wilbert Berendsen
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
the popplerqt5 module.

The View (see view.py) is a QScrollArea that uses a Surface (see surface.py) as
its widget.  The Surface has a Layout (see layout.py) that positions Page
objects (see page.py).

A Page represents a single page from a Poppler.Document. Its rect() method
contains the position and size to draw it. Its computeSize() method computes its
size, and the Layout is expected to set its position. A Page can be hidden from
the view using Page.setVisible(False). A Layout has no notion of a document,
only Pages. Every Page references the Poppler.Document it belongs to.

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

The default Layout arranges all pages either vertically or horizontally, which
can be set using Layout.setOrientation(Qt.Vertical or Qt.Horizontal).

The View supports four resizing modes:

FixedScale = 0  (don't resize the pages if the View resizes)
FitWidth   = 1  (fit pages in the width of the View)
FitHeight  = 2  (fit pages in the height of the View)
FitBoth    = 3  (fit the full page size in the View)

The Layout.fit() method actually creates the layout described by the viewmode.
The default layout uses the largest Page to determine the "fit" size.
Specialized layouts can react in different ways to the view mode.

View.setViewMode() is used to set the view mode, and View.setScale() automatically
sets the view mode to FixedScale.  View emits viewModeChanged(mode) on mode change.

View, Surface, (Abstract)Layout and Page can all be inherited from to build
more specialized Poppler viewers.

The cache module implements in-memory caching for drawn Page images.
The images are rendered in a background thread.

Furthermore, there is a printer module containing functions to create a PostScript
file of a Poppler.Document and a class to print a Poppler.Document to a QPrinter
using raster images.

The Poppler library is not thread-safe, so when calling into Poppler for drawing
or getting other objects you can acquire a lock with lock(document) that blocks
till a possible running background job for that document has completed.
(Pending tasks will wait until the Qt eventloop is entered again.)

"""

# viewModes:
FixedScale = 0
FitWidth   = 1
FitHeight  = 2
FitBoth    = FitHeight | FitWidth


from .view import View
from .page import Page
from .layout import AbstractLayout, Layout, RowLayout
from .surface import Surface
from .render import RenderOptions
from .highlight import Highlighter
from .magnifier import Magnifier
from .locking import lock
from . import cache


__all__ = [
    'FixedScale', 'FitWidth', 'FitHeight', 'FitBoth',
    'View', 'Page', 'AbstractLayout', 'Layout', 'Surface',
    'RenderOptions', 'Highlighter', 'Magnifier',
    'lock', 'cache',
]
