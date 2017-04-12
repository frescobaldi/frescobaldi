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
A dummy module containing a few of the definitions in popplerqt5.

This is imported if the real popplerqt5 is not available and makes it
possible to import qpopplerview, although it can't do anything useful.

It only contains class definitions that define a namespace, enums or other
constants. Classes can't be instantiated and have no member functions.

"""


__all__ = ["Poppler"]


class _noinst(object):
    """A class that can't be instantiated."""
    def __new__(cls, *args, **kwargs):
        raise TypeError("can't instantiate %s" % cls.__name__)


class Poppler(_noinst):
    class Document(_noinst):
        @staticmethod
        def load(filename): pass
        @staticmethod
        def loadFromData(data): pass
        class RenderHint(int): pass
        Antialiasing = RenderHint(1)
        TextAntialiasing = RenderHint(2)
        TextHinting = RenderHint(4)

    class Page(_noinst):
        class Orientation(int): pass
        Landscape = Orientation(0)
        Portrait = Orientation(1)
        Seascape = Orientation(2)
        UpsideDown = Orientation(3)

        class PageAction(int): pass
        Opening = PageAction(0)
        Closing = PageAction(1)

        class PainterFlag(int): pass
        DontSaveAndRestore = PainterFlag(1)

        class Rotation(int): pass
        Rotate0 = Rotation(0)
        Rotate90 = Rotation(1)
        Rotate180 = Rotation(2)
        Rotate270 = Rotation(3)

        class SearchDirection(int): pass
        NextResult = SearchDirection(0)
        PreviousResult = SearchDirection(1)

        class SearchMode(int): pass
        CaseSensitive = SearchMode(0)
        CaseInsensitive = SearchMode(1)

        class TextLayout(int): pass
        PhysicalLayout = TextLayout(0)
        RawOrderLayout = TextLayout(1)


    class LinkDestination(_noinst): pass

    class Link(_noinst): pass
    class LinkAction(Link): pass
    class LinkAnnotation(Link):pass
    class LinkBrowse(Link): pass
    class LinkExecute(Link): pass
    class LinkGoto(Link): pass
    class LinkJavaScript(Link): pass
    class LinkSound(Link): pass


