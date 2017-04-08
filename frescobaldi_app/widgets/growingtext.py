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
Provides a QTextEdit subclass that grows vertically to accommodate document size.

You should set maximumHeight to restrict its vertical size.
"""


from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QPlainTextEdit, QStyle, QTextEdit


__all__ = ["GrowingPlainTextEdit", "GrowingTextEdit"]


class _GrowingTextEditBase(object):
    """Base class."""
    def __init__(self, parent=None):
        super(_GrowingTextEditBase, self).__init__(parent)
        self.setLineWrapMode(self.NoWrap)
        self.document().documentLayout().documentSizeChanged.connect(self.updateVerticalSize)
        self.updateVerticalSize()

    def updateVerticalSize(self):
        # can vertical or horizontal scrollbars appear?
        vcan = self.verticalScrollBarPolicy() == Qt.ScrollBarAsNeeded
        hcan = self.horizontalScrollBarPolicy() == Qt.ScrollBarAsNeeded

        # width a scrollbar takes off the viewport size
        framewidth = 0
        if self.style().styleHint(QStyle.SH_ScrollView_FrameOnlyAroundContents, None, self):
            framewidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth) * 2
        scrollbarextent = self.style().pixelMetric(QStyle.PM_ScrollBarExtent, None, self) + framewidth

        margin = framewidth + self.document().documentMargin()
        size = self.documentSize() + QSize(margin, margin)
        width = size.width()
        height = size.height()

        max_width = self.width()
        max_height = self.maximumHeight()

        # will scrollbars appear?
        hwill, vwill = False, False
        if hcan and width > max_width:
            hwill = True
        if vcan and height > max_height:
            vwill = True
        if vcan and hwill and height + scrollbarextent > max_height:
            vwill = True
        if hcan and vwill and width + scrollbarextent > max_width:
            hwill = True
        if hwill:
            height += scrollbarextent
        self.resize(self.width(), min(max_height, height))

    def documentSize(self):
        """Implemented differently for QTextEdit and QPlainTextEdit."""
        raise NotImplementedError

    def setLineWrapMode(self, mode):
        """Reimplemented to avoid WidgetWidth wrap mode, which causes resize loops."""
        if mode == self.WidgetWidth:
            raise ValueError("cannot use WidgetWidth wrap mode")
        else:
            super(_GrowingTextEditBase, self).setLineWrapMode(mode)


class GrowingTextEdit(_GrowingTextEditBase, QTextEdit):
    """Growing QTextEdit"""
    def documentSize(self):
        return self.document().documentLayout().documentSize().toSize()


class GrowingPlainTextEdit(_GrowingTextEditBase, QPlainTextEdit):
    """Growing QPlainTextEdit"""
    def documentSize(self):
        doc = self.document()
        layout = doc.documentLayout()
        size = layout.documentSize().toSize()
        block = doc.firstBlock()
        line_height = layout.blockBoundingRect(block).height() / block.lineCount()
        return QSize(size.width(), size.height() * line_height + 2 * doc.documentMargin())


