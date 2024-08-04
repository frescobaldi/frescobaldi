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

"""The splash screen, displayed on startup."""

import os

from PyQt6.QtCore import QEventLoop, QTimer, Qt
from PyQt6.QtGui import QGuiApplication, QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

import app
import appinfo

def show():

    message = f"{appinfo.appname}  {appinfo.version} "
    pixmap = QPixmap(os.path.join(__path__[0], 'splash.png'))
    if QGuiApplication.primaryScreen().geometry().height() < 640:
        fontsize = 23
        pixmap = pixmap.scaledToHeight(240, Qt.SmoothTransformation)
    else:
        fontsize = 40

    splash = QSplashScreen(pixmap, Qt.WindowType.SplashScreen)

    font = splash.font()
    font.setPixelSize(fontsize)
    font.setWeight(QFont.Weight.Bold)
    splash.setFont(font)

    splash.showMessage(message,
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                       Qt.GlobalColor.white)
    splash.show()
    QApplication.processEvents()

    def hide():
        splash.deleteLater()
        app.appStarted.disconnect(hide)

    app.appStarted.connect(hide)
