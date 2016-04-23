# -*- coding: utf-8 -*-
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
version = "3.0.0"
description = "LilyPond Music Editor"
long_description = \
    "Frescobaldi is an advanced text editor to edit LilyPond sheet music files. " \
    "Features include an integrated PDF preview and a powerful Score Wizard."
maintainer = "Wilbert Berendsen"
maintainer_email = "info@frescobaldi.org"
domain = "frescobaldi.org"
url = "http://www.{0}/".format(domain)
license = "GPL"

# this one is used everywhere in the application
appname = "Frescobaldi"
