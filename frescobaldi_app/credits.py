# -*- coding: utf-8 -*-
# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2013 - 2013 by Wilbert Berendsen
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
All the credits and THANKS information.
"""

from __future__ import unicode_literals


import info


# mapping from language code to list of translator names
translators = {
    'nl': (
        "Wilbert Berendsen",
    ),
    'fr': (
        "Raphaël Doursenaud",
        "Denis Bitouzé",
        "Philippe Massart",
        "Valentin Villenave",
        "Yann Collette",
        "David Bouriaud",
        "Ryan Kavanagh",
        "Richard Cognot",
    ),
    'tr': (
        "Server ACİM",
    ),
    'es': (
        "Francisco Vila",
    ),
    'ru': (
        "Sergey Poltavski",
        "Artem Zolochevskiy",
        "Mikhail Iglizky",
    ),
    'it': (
        "Gianluca D'Orazio",
    ),
    'de': (
        "Henrik Evers",
        "Georg Hennig",
        "Markus W. Kropp",
        "Urs Liska",
    ),
    'cs': (
        "Pavel Fric",
    ),
    'pl': (
        "Piotr Komorowski",
    ),
    'gl': (
        "Manuel A. Vázquez",
    ),
    'pt_BR': (
        "Édio Mazera",
    ),
    'uk': (
        "Dmytro O. Redchuk",
    ),
}


def authors():
    """Yields (name, contributions) tuples.
    
    contributions is a tuple of things the author has done.
    
    """
    yield "Wilbert Berendsen", (
        _("Main author and core developer"),
    )
        
    yield "Richard Cognot", (
        _("Kinetic Scrolling for the Music View"),
    )
    
    yield "Nicolas Malarmey", (
        _("Improved highlighting and auto-completion of Scheme code"),
    )
	
    yield "Urs Liska", (
        _("Preview modes"),
        _("Various contributions"),
    )
	
    yield "Christopher Bryan", (
        _("Modal Transpose"),
    )
	
    yield "Peter Bjuhr", (
        _("Quick Insert buttons for grace notes"),
        _("MusicXML import"),
    )


def credits():
    """Yield lines describing third-party libraries, incorporated or linked."""
    yield _(
        "{appname} is written in {python} and uses the {qt} toolkit.").format(
        appname=info.appname,
        # L10N: the Python programming language
        python='<a href="http://www.python.org/">{0}</a>'.format(_("Python")),
        # L10N: the Qt4 application framework
        qt='<a href="http://qt.nokia.com/">{0}</a>'.format(_("Qt4")))
    yield _(
        "The Music View is powered by the {poppler} library by "
        "{authors} and others.").format(
        poppler='<a href="http://poppler.freedesktop.org/">{0}</a>'.format(
            # L10N: the Poppler PDF library
            _("Poppler")),
        authors='Kristian Høgsberg, Albert Astals Cid')
    yield _(
        "Most of the bundled icons are created by {tango}.").format(
        tango='<a href="http://tango.freedesktop.org/">{0}</a>'.format(_(
            "The Tango Desktop Project")))


