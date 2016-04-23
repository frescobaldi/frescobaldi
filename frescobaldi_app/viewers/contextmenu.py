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
Base class for viewers' context menus.
"""


from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QActionGroup

import icons


class AbstractViewerContextMenu(QObject):
    """Base class for viewers' context menus.
    It provides the template method pattern to generate the menu.
    Subclasses can override individual parts of the menu this way."""

    def __init__(self, panel):
        self._panel = panel
        self._actionCollection = panel.actionCollection
        self._surface = None
        self._menu = QMenu(self._panel)

    def surface(self):
        """Return the (cached) surface"""
        result = self._surface or self._panel.widget().view.surface()
        return result

    def addSeparator(self):
        """Add a separator to the menu."""
        self._menu.addSeparator()

    def addCopyImageAction(self):
        """Add action to copy image if available"""
        if self.surface().hasSelection():
            self._menu.addAction(self._actionCollection.viewer_copy_image)

    def addEditInPlaceAction(self, cursor, position):
        """Add action to edit snippet if on a textedit link"""
        a = self._menu.addAction(icons.get("document-edit"), _("Edit in Place"))
        @a.triggered.connect
        def edit():
            import editinplace
            editinplace.edit(self._panel.widget(), cursor, position)

    def addLinkAction(self, link):
        """Add action if on an arbitrary link"""
        m = self._menu
        a = m.addAction(icons.get("window-new"), _("Open Link in &New Window"))
        @a.triggered.connect
        def open_in_browser():
            import helpers
            helpers.openUrl(QUrl(link.url()))

        a = m.addAction(icons.get("edit-copy"), _("Copy &Link"))
        @a.triggered.connect
        def copy_link():
            QApplication.clipboard().setText(link.url())

    def addCursorLinkActions(self):
        """Add actions if on a textedit or arbitrary link"""
        if self._cursor:
            self.addEditInPlaceAction(self._cursor, self._position)
        elif self._link:
            self.addLinkAction(self._link)

    def addShowActions(self):
        """Adds a submenu giving access to the (other)
        opened viewer documents"""
        mds = self._actionCollection.viewer_document_select
        docs = mds.viewdocs()
        document_actions = {}
        multi_docs = len(docs) > 1
        if self._panel.widget().currentViewdoc():
            current_doc_filename = self._panel.widget().currentViewdoc().filename()

        m = self._menu
        sm = QMenu(m)
        sm.setTitle(_("Show..."))
        sm.setEnabled(multi_docs)
        ag = QActionGroup(m)
        ag.triggered.connect(self._panel.slotShowViewdoc)

        for d in docs:
            action = QAction(sm)
            action.setText(d.name())
            action._document_filename = d.filename()
            # TODO: Tooltips aren't shown by Qt (it seems)
            action.setToolTip(d.filename())
            action.setCheckable(True)
            action.setChecked(d.filename() == current_doc_filename)

            ag.addAction(action)
            sm.addAction(action)

        m.addSeparator()
        m.addMenu(sm)

    def addOpenCloseActions(self):
        """Add actions to close documents.
        This is not implemented in the base class"""
        m = self._menu
        ac = self._actionCollection
        m.addAction(ac.viewer_open)
        docs = self._actionCollection.viewer_document_select.viewdocs()
        if docs:
            sm = QMenu(m)
            sm.setTitle(_("Close..."))
            m.addMenu(sm)
            sm.addAction(ac.viewer_close)
            multi_docs = len(docs) > 1
            ac.viewer_close_other.setEnabled(multi_docs)
            ac.viewer_close_all.setEnabled(multi_docs)
            sm.addAction(ac.viewer_close_other)
            sm.addAction(ac.viewer_close_all)

    def addReloadAction(self):
        """Add action to reload document."""
        current_document = self._panel.widget().currentViewdoc()
        if current_document:
            m = self._menu
            ac = self._actionCollection
            m.addAction(ac.viewer_reload)

    def addZoomActions(self):
        """Add actions to zoom the viewer"""
        m = self._menu
        m.addSeparator()
        sm = QMenu(m)
        sm.setTitle(_("Zoom"))
        m.addMenu(sm)
        ac = self._actionCollection
        sm.addAction(ac.viewer_fit_width)
        sm.addAction(ac.viewer_fit_height)
        sm.addAction(ac.viewer_fit_both)
        sm.addSeparator()
        sm.addAction(ac.viewer_zoom_in)
        sm.addAction(ac.viewer_zoom_out)
        sm.addAction(ac.viewer_zoom_original)

    def addSynchronizeAction(self):
        """Add an action telling the viewer to
        always try syncing with the input editor."""
        m = self._menu
        ac = self._actionCollection
        m.addAction(ac.viewer_sync_cursor)

    def addShowToolbarAction(self):
        """Add action to toggle the visibility of
        the viewer's toolbar"""
        m = self._menu
        ac = self._actionCollection
        m.addAction(ac.viewer_show_toolbar)

    def addHelpAction(self):
        """Add help menu item"""
        m = self._menu
        ac = self._actionCollection
        m.addSeparator()
        m.addAction(ac.viewer_help)

    def show(self, position, link, cursor, methods = None):
        """Build the panel's context menu dynamically.
        Implements the template method pattern to allow
        subclasses to override each step.
        If methods passes a list of methods these will be
        called instead to construct the menu, making it
        possible to change order or add methods not
        available in the base class."""

        self._position = position
        self._link = link
        self._cursor = cursor

        self._menu.clear()

        if not methods:
            # Actions affecting the current link(selection)
            self.addCopyImageAction()
            self.addCursorLinkActions()
            # Actions affecting the currently opened documents
            self.addShowActions()
            self.addOpenCloseActions()
            self.addReloadAction()
            # Actions affecting the viewer's state
            self.addZoomActions()
            self.addSynchronizeAction()
            self.addShowToolbarAction()
        else:
            for m in methods:
                m()
        # The help action is added always
        self.addHelpAction()

        # show it!
        if self._menu.actions():
            self._menu.exec_(position)
        # TODO: Can this really be removed?
        # it had to be commented out because in the documents submenu
        # there popped up issues with deleted objects (the menu was already
        # deleted when the signal was emitted)
#        self._menu.deleteLater()
