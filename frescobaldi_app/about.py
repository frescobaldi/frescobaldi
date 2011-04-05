# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
About dialog.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSvg import *

import app
import info



class AboutDialog(QDialog):
    def __init__(self, mainwindow):
        super(AboutDialog, self).__init__(mainwindow)
        
        self.setWindowTitle(_("About {name}").format(name = info.appname))
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # large icon size
        size = QSize(100, 100)
        
        # draw SVG
        r = QSvgRenderer("icons:frescobaldi.svg")
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        r.render(QPainter(pixmap))
        
        pic = QLabel()
        pic.setPixmap(pixmap)
        pic.setFixedSize(size)
        
        layout.addWidget(pic, 0, Qt.AlignHCenter)

        # Html
        html = """<html>
        <body><div align="center">
        <h1>{appname}</h1>
        <h3>{version}</h3>
        <p>{description}</p>
        <p>{copyright}</p>
        <p>{license}</p>
        <p><a href="{homepage}">{homepage}</a></p>
        </div></body>
        </html>
        """.format(
            appname = info.appname,
            version = _("Version {version}").format(version = info.version),
            description = _("A LilyPond Music Editor"),
            copyright = _("Copyright (c) {year} by {author}").format(
                year = "2008-2011",
                author = """<a href="mailto:{0}" title="{1}">{2}</a>""".format(
                    info.maintainer_email,
                    _("Send an e-mail message to the maintainers."),
                    info.maintainer)),
            license = _("Licensed under the {gpl}").format(
                gpl = """<a href="http://www.gnu.org/licenses/gpl.html">GNU GPL</a>"""),
            homepage = info.url,
        )
        
        text = QLabel()
        text.setText(html)
        text.setOpenExternalLinks(True)
        layout.addWidget(text)

        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.setCenterButtons(True)
        button.accepted.connect(self.accept)
        layout.addWidget(button)
        layout.setSizeConstraint(QLayout.SetFixedSize)


