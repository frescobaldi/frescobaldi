# -*- coding: utf-8 -*-
# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Information about the Frescobaldi application.
"""

from __future__ import unicode_literals

# these variables are also used by the distutils setup
name = "frescobaldi"
version = "2.0.7"
description = "LilyPond Music Editor"
long_description = \
    "Frescobaldi is an advanced text editor to edit LilyPond sheet music files. " \
    "Features include an integrated PDF preview and a powerful Score Wizard."
maintainer = "Wilbert Berendsen"
maintainer_email = "info@frescobaldi.org"
url = "http://www.frescobaldi.org/"
license = "GPL"

# these are used in the application
appname = "Frescobaldi"

# mapping from language code to list of translator names
translators = {
    'nl': [
        "Wilbert Berendsen",
    ],
    'fr': [
        "Raphaël Doursenaud",
        "Philippe Massart",
        "Valentin Villenave",
        "Yann Collette",
        "David Bouriaud",
        "Ryan Kavanagh",
        "Richard Cognot",
    ],
    'tr': [
        "Server ACİM",
    ],
    'es': [
        "Francisco Vila",
    ],
    'ru': [
        "Sergey Poltavski",
        "Artem Zolochevskiy",
        "Mikhail Iglizky",
    ],
    'it': [
        "Gianluca D'Orazio",
    ],
    'de': [
        "Henrik Evers",
        "Georg Hennig",
        "Markus W. Kropp",
    ],
    'cs': [
        "Pavel Fric",
    ],
    'pl': [
        "Piotr Komorowski",
    ],
    'gl': [
        "Manuel A. Vázquez",
    ],
    'pt_BR': [
        "Édio Mazera",
    ],
    'uk': [
        "Dmytro O. Redchuk",
    ],
}

