# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2016 - 2019 by Wilbert Berendsen
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
This is a generic paged view widget.

Its main design goal is to display the pages of a PDF document, but it can
display any set of images or pages, originating from different documents.

Every page is represented by a Page instance, which encompasses all logic
for the document type, i.e. drawing etc.

Pages are managed by a PageLayout.

A PageLayout can be set to a View so the pages are displayed.

The images from a PDF, SVG of possibly other document are cached, and rendering
is tile-based, to support zooming in at great detail.  Also a magnifier is
available, which by default pops up at Ctrl+click.

Because the qpageview is built on Qt, we use the Qt convention
to have camelCase method names and CamelCase class names.

"""

from .constants import (
    # rotation:
    Rotate_0,
    Rotate_90,
    Rotate_180,
    Rotate_270,


    # viewModes:
    FixedScale,
    FitWidth,
    FitHeight,
    FitBoth,


    # orientation:
    Horizontal,
    Vertical,

)

from . import link
from . import highlight
from . import shadow
from . import view
from . import util
from .pkginfo import version_string



class View(
        link.LinkViewMixin,
        highlight.HighlightViewMixin,
        shadow.ShadowViewMixin,
        util.LongMousePressMixin,
        view.View,
    ):
    """Paged view component based on view.View, with all enhancements."""
    pass


def loadPdf(filename, renderer=None):
    """Convenience function to create a Document with the specified PDF file.

    The filename can also be a QByteArray or an already loaded
    popplerqt5.Poppler.Document instance.

    """
    from . import poppler
    return poppler.PopplerDocument(filename, renderer)


def loadSvgs(filenames, renderer=None):
    """Convenience function to create a Document with the specified SVG files.

    Each SVG file is loaded in one Page. A filename can also be a
    QByteArray.

    """
    from . import svg
    return svg.SvgDocument(filenames, renderer)


def loadImages(filenames, renderer=None):
    """Convenience function to create a Document with images from files.

    Each image is loaded in one Page. A filename can also be a
    QByteArray.

    """
    from . import image
    return image.ImageDocument(filenames, renderer)


def diffDocument(documents, renderer=None):
    """Convenience function to create a diff.DiffDocument from other documents.

    The difference works best with documents that are similar and mostly black
    and white.

    """
    from . import diff
    return diff.DiffDocument(documents, renderer)
