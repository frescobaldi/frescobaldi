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
Download music fonts from the openlilylib-resources Github repository
"""

CATALOGUE_URL = (
    "https://raw.githubusercontent.com/openlilylib-resources/"
    "lilypond-notation-fonts/master/catalogue.json"
)

# import urllib.request
# import json
# try:
#     response = urllib.request.urlopen(CATALOGUE_URL)
#     data = repsonse.read()
#     catalogue = json.loads(data.decode('utf-8'))
# ...

# TODO:
# - only works when there's a music font repository set
# - download catalogue
# - compare available fonts with installed fonts (incl. version check)
# - open a dialog with a list of check boxes for all available fonts
#   (fonts that don't need to be updated are initially unchecked,
#    but it's possible to overwrite them)
#
# - download to temp dir first,
#   and when that's successful copy/overwrite to the local repository
# - install any newly downloaded font (in *this* case not skipping
#   but overwriting existing fonts)
