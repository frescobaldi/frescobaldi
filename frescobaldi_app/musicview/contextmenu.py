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
The PDF preview panel context menu.
"""


from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMenu


import icons


def show(position, panel, link, cursor):
    """Shows a context menu.

    position: The global position to pop up
    panel: The music view panel, giving access to mainwindow and view widget
    link: a popplerqt5 LinkBrowse instance or None
    cursor: a QTextCursor instance or None

    """
    m = QMenu(panel)

    # selection? -> Copy
    if panel.widget().view.surface().hasSelection():
        if panel.widget().view.surface().selectedText():
            m.addAction(panel.actionCollection.music_copy_text)
        m.addAction(panel.actionCollection.music_copy_image)

    if cursor:
        a = m.addAction(icons.get("document-edit"), _("Edit in Place"))
        @a.triggered.connect
        def edit():
            import editinplace
            editinplace.edit(panel.widget(), cursor, position)
    elif link:
        a = m.addAction(icons.get("window-new"), _("Open Link in &New Window"))
        @a.triggered.connect
        def open_in_browser():
            import helpers
            helpers.openUrl(QUrl(link.url()))

        a = m.addAction(icons.get("edit-copy"), _("Copy &Link"))
        @a.triggered.connect
        def copy_link():
            QApplication.clipboard().setText(link.url())

    # no actions yet? insert Fit Width/Height
    if not m.actions():
        m.addAction(panel.actionCollection.music_fit_width)
        m.addAction(panel.actionCollection.music_fit_height)
        m.addAction(panel.actionCollection.music_zoom_original)
        m.addSeparator()
        m.addAction(panel.actionCollection.music_sync_cursor)

    # help
    m.addSeparator()
    a = m.addAction(icons.get("help-contents"), _("Help"))
    @a.triggered.connect
    def help():
        import userguide
        userguide.show("musicview")

    # show it!
    if m.actions():
        m.exec_(position)
    m.deleteLater()



