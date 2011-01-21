#! python

"""
A Page is resposible for drawing a page of a Poppler document
inside a layout.
"""

import weakref
import popplerqt4

from PyQt4.QtCore import *
from PyQt4.QtGui import *

_cache = weakref.WeakKeyDictionary()


def image(document, pageNumber, size, rotation=popplerqt4.Poppler.Page.Rotate0):
    """Returns a rendered image in size."""
    key = (pageNumber, size.width(), size.height(), rotation)
    try:
        return _cache[document][key]
    except KeyError:
        page = document.page(pageNumber)
        if rotation & 1:
            size.transpose()
        xres = 72.0 * size.width() / page.pageSizeF().width()
        yres = 72.0 * size.height() / page.pageSizeF().height()
        image = page.renderToImage(xres, yres, -1, -1, -1, -1, rotation)
        _cache.setdefault(document, {})[key] = image
        return image


