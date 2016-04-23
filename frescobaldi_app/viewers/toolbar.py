# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
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
Abstract base class for a viewer's toolbar.
Provides a consistent but configurable infrastructure for toolbars.
"""


from PyQt5.QtWidgets import (
    QWidget,
    QToolBar,
    QHBoxLayout,
)

class ToolBar(QToolBar):
    """Improved toolbar for use when not child of a QMainWindow.
    For now this is only a stub."""
    pass

class AbstractViewerToolbar(QWidget):
    """Base class for viewers' toolbars.
    Each toolbar contains a main and a help toolbar element.
    The main toolbar can be configured by overriding individual
    add...() methods, and a completely new configuration can be
    achieved by passing a list of methods to the constructor.
    Suppressing individual actions is most easily achieved by
    overriding add...() methods with `pass`.
    """

    def __init__(self, parent, methods = None):
        super(AbstractViewerToolbar, self).__init__(parent)
        self.actionCollection = ac = parent.actionCollection
        self.createComponents()
        self.createLayout()
        self.populate(methods)
        # show or hide toolbar upon creation
        self.setVisible(self.actionCollection.viewer_show_toolbar.isChecked())

    def createComponents(self):
        # TODO: If it would become necessary to
        # subclass the ToolBar class the following Two
        # instantiations must be replaced by factory methods.
        self.main_toolbar = ToolBar(self)
        self.help_toolbar = ToolBar(self)

    def createLayout(self):
        self.layout = layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_toolbar)
        layout.addStretch()
        layout.addWidget(self.help_toolbar)
        self.setLayout(layout)

    def populate(self, methods = None):
        """Defines a template for the population of the viewer's toolbar.
        Subclasses can configure the toolbar by overriding individual
        add...() methods or by passing a list of methods."""
        ac = self.actionCollection

        # add help button to the help toolbar (right-aligned)
        # this is not intended to be configured
        self.help_toolbar.addAction(ac.viewer_help)

        if not methods:
            # default order of actions
            self.addOpenAction()
            self.addCloseAction()
            self.addSeparator()
            self.addViewdocChooserAction()
            self.addSeparator()
            self.addPrintAction()
            self.addSeparator()
            self.addZoomActions()
            self.addSeparator()
            self.addPagerActions()
        else:
            # process the given order of actions
            for m in methods:
                m()

    def addSeparator(self):
        """Add a separator to the toolbar."""
        self.main_toolbar.addSeparator()

    def addOpenAction(self):
        """Add actions to open viewer documents."""
        t = self.main_toolbar
        ac = self.actionCollection
        t.addAction(ac.viewer_open)

    def addCloseAction(self):
        """Add actions to close the current viewer document."""
        t = self.main_toolbar
        ac = self.actionCollection
        t.addAction(ac.viewer_close)

    def addViewdocChooserAction(self):
        """Add the document chooser to the toolbar."""
        t = self.main_toolbar
        ac = self.actionCollection
        t.addAction(ac.viewer_document_select)

    def addPrintAction(self):
        """Add the print action."""
        t = self.main_toolbar
        ac = self.actionCollection
        t.addAction(ac.viewer_print)

    def addZoomActions(self):
        """Add different zoomer actions."""
        t = self.main_toolbar
        ac = self.actionCollection
        t.addAction(ac.viewer_zoom_in)
        t.addAction(ac.viewer_zoom_combo)
        t.addAction(ac.viewer_zoom_out)

    def addPagerActions(self):
        """Add navigational actions."""
        t = self.main_toolbar
        ac = self.actionCollection
        t.addAction(ac.viewer_prev_page)
        t.addAction(ac.viewer_pager)
        t.addAction(ac.viewer_next_page)
