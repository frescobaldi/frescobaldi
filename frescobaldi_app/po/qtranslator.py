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
Translation of some parts of Qt (like dialog buttons) via our PO files.

The strings that are needed are in the qtmessages.py file in this directory.

"""

from __future__ import print_function

from PyQt5.QtCore import QCoreApplication, QTranslator

import app


_translator = None

class Translator(QTranslator):
    """Subclass of QTranslator that gets its messages via the _() function."""
    def translate(self, context, sourceText, disambiguation="", n=-1):
        #_debug(context, sourceText)
        return _(context, sourceText)


def installTranslator():
    """Install a QTranslator so Qt's own texts are also translated."""
    global _translator
    if _translator is not None:
        QCoreApplication.removeTranslator(_translator)
    _translator = Translator()
    QCoreApplication.installTranslator(_translator)

def initialize():
    # just install again on change, so the widgets get a LanguageChange event
    app.languageChanged.connect(installTranslator)
    installTranslator()

# DEBUG: show translatable Qt messages once
_debugmessages = set()
def _debug(context, sourceText):
    l = len(_debugmessages)
    _debugmessages.add((context, sourceText))
    if len(_debugmessages) > l:
        print('_' + repr((context, sourceText)))

