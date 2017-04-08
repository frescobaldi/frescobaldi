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
The Header (titles) widget.
"""


from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QTextBrowser, QWidget)

import app
import qutil
import textformats
import completionmodel

from . import __path__


class HeaderWidget(QWidget):
    def __init__(self, parent):
        super(HeaderWidget, self).__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # The html view with the score layout example
        t = self.htmlView = QTextBrowser()
        t.setOpenLinks(False)
        t.setOpenExternalLinks(False)
        t.setSearchPaths(__path__)
        t.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        t.setFocusPolicy(Qt.NoFocus)

        # ensure that the full HTML example page is displayed
        t.setContentsMargins(2, 2, 2, 2)
        t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        t.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        t.setMinimumSize(QSize(350, 350))
        layout.addWidget(t)

        t.anchorClicked.connect(self.slotAnchorClicked)

        grid = QGridLayout()
        layout.addLayout(grid)

        grid.setVerticalSpacing(1)
        grid.setColumnMinimumWidth(1, 200)

        self.labels = {}
        self.edits = {}
        for row, (name, desc) in enumerate(headers()):
            l = QLabel()
            e = QLineEdit()
            l.setBuddy(e)
            grid.addWidget(l, row, 0)
            grid.addWidget(e, row, 1)
            self.labels[name] = l
            self.edits[name] = e
            completionmodel.complete(e, "scorewiz/completion/header/"+name)
            e.completer().setCaseSensitivity(Qt.CaseInsensitive)

        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        app.translateUI(self)

    def translateUI(self):
        msg = _("Click to enter a value.")
        self.htmlView.setHtml(titles_html.format(
            copyrightmsg = _("bottom of first page"),
            taglinemsg = _("bottom of last page"),
            imgurl = QUrl.fromLocalFile(__path__[0]).toString(),
            **dict((name, "<a title='{0}' href='{1}'>{2}</a>".format(msg, name, desc))
                    for name, desc in headers())))
        for name, desc in headers():
            self.labels[name].setText(desc + ":")
        # add accelerators to names, avoiding the tab names
        tabwidget = self.window().tabs
        used = filter(None, (qutil.getAccelerator(tabwidget.widget(i).title())
                             for i in range(tabwidget.count())))
        qutil.addAccelerators([self.labels[name] for name, desc in headers()], used)

    def readSettings(self):
        p = self.htmlView.palette()
        p.setColor(QPalette.Base, textformats.formatData('editor').baseColors['paper'])
        self.htmlView.setPalette(p)

    def slotAnchorClicked(self, url):
        try:
            e = self.edits[url.toString()]
        except KeyError:
            return
        e.setFocus()

    def clear(self):
        """Empties all text entries."""
        for edit in self.edits.values():
            edit.clear()

    def headers(self):
        """Yields two-tuples (headername, entered text) for the headers that are non-empty."""
        for name, desc in headers():
            text = self.edits[name].text().strip()
            if text:
                yield name, text



def headers():
    """Yields two-tuples (headername, translated name) in a sensible order."""
    yield 'dedication',  _("Dedication")
    yield 'title',       _("Title")
    yield 'subtitle',    _("Subtitle")
    yield 'subsubtitle', _("Subsubtitle")
    yield 'instrument',  _("Instrument")
    yield 'composer',    _("Composer")
    yield 'arranger',    _("Arranger")
    yield 'poet',        _("Poet")
    yield 'meter',       _("Meter")
    yield 'piece',       _("Piece")
    yield 'opus',        _("Opus")
    yield 'copyright',   _("Copyright")
    yield 'tagline',     _("Tagline")


titles_html = r"""<html><head><style type='text/css'>
body {{
  color: black;
}}
a {{
  text-decoration: none;
  color: black;
}}
</style></head>
<body><table width='100%' style='font-family:serif;'>
<tr><td colspan=3 align=center>{dedication}</td></tr>
<tr><td colspan=3 align=center style='font-size:20pt;'><b>{title}</b></td></tr>
<tr><td colspan=3 align=center style='font-size:12pt;'><b>{subtitle}</b></td></tr>
<tr><td colspan=3 align=center><b>{subsubtitle}</b></td></tr>
<tr>
    <td align=left width='25%'>{poet}</td>
    <td align=center><b>{instrument}</b></td>
    <td align=right width='25%'>{composer}</td>
</tr>
<tr>
    <td align=left>{meter}</td>
    <td> </td>
    <td align=right>{arranger}</td>
</tr>
<tr>
    <td align=left>{piece}</td>
    <td> </td>
    <td align=right>{opus}</td>
</tr>
<tr><td colspan=3 align=center><img src="{imgurl}/scorewiz.png"></td></tr>
<tr><td colspan=3 align=center>{copyright} <i>({copyrightmsg})</i></td></tr>
<tr><td colspan=3 align=center>{tagline} <i>({taglinemsg})</i></td></tr>
</table></body></html>
"""
