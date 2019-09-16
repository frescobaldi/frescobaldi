# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2015 - 2015 by Wilbert Berendsen
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
Provides an icon for a Document.
"""


import plugin
import signals
import job
import engrave
import icons


def icon(doc, mainwindow=None):
    """Provides a QIcon for a Document.

    If a MainWindow is provided, the sticky icon can be returned, if the
    Document is sticky for that main window.

    """
    return DocumentIconProvider.instance(doc).icon(mainwindow)


class DocumentIconProvider(plugin.DocumentPlugin):
    """Provides an icon for a Document."""
    iconChanged = signals.Signal()

    def __init__(self, doc):
        doc.modificationChanged.connect(self._send_icon)
        mgr = job.manager.manager(doc)
        mgr.started.connect(self._send_icon)
        mgr.finished.connect(self._send_icon)

    def _send_icon(self):
        self.iconChanged()

    def icon(self, mainwindow=None):
        doc = self.document()
        j = job.manager.job(doc)
        if j and j.is_running() and not job.attributes.get(j).hidden:
            icon = 'lilypond-run'
        elif mainwindow and doc is engrave.Engraver.instance(mainwindow).stickyDocument():
            icon = 'pushpin'
        elif doc.isModified():
            icon = 'document-save'
        elif j and not j.is_running() and not j.is_aborted() and j.success():
            icon = 'document-compile-success'
        elif j and not j.is_running() and not j.is_aborted():
            icon = 'document-compile-failed'
        else:
            icon = 'text-plain'
        return icons.get(icon)
