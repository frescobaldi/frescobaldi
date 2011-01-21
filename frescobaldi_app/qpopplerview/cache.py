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
        pageSize = page.pageSize()
        if rotation & 1:
            pageSize.transpose()
        xres = 72.0 * size.width() / pageSize.width()
        yres = 72.0 * size.height() / pageSize.height()
        image = page.renderToImage(xres, yres, 0, 0, size.width(), size.height(), rotation)
        _cache.setdefault(document, {})[key] = image
        return image


