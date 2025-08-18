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
Information about the Frescobaldi application.
"""


# these variables are also used by the distutils setup
name = "frescobaldi"
# https://packaging.python.org/en/latest/discussions/versioning/
version = "4.0.5.dev1"
extension_api = "0.9.0"
description = "LilyPond Music Editor"
long_description = \
    "Frescobaldi is an advanced text editor to edit LilyPond sheet music files. " \
    "Features include an integrated PDF preview and a powerful Score Wizard."
maintainer = "Wilbert Berendsen"
maintainer_email = "frescobaldi@googlegroups.com"
domain = "frescobaldi.org"
url = f"http://www.{domain}/"
issues_url = "https://github.com/frescobaldi/frescobaldi/issues/new"
license = "GPL"

# this one is used everywhere in the application
appname = "Frescobaldi"

desktop_file_name = "org.frescobaldi.Frescobaldi"

# required versions of important dependencies
required_python_version = (3, 8)
required_python_ly_version = (0, 9, 4)
required_qt_version = (6, 6)

# LilyPond doc URLs to be used in lilydoc/manager.py
# see also lilypondinfo.LilyPondInfo.lilydoc_url()
lilydoc_stable = "http://lilypond.org/doc/v2.24"
lilydoc_development = "http://lilypond.org/doc/v2.25"
