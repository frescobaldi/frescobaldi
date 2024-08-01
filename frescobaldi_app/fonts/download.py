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

def list_available_fonts():
    from github import (
        repo
    )
    print("Downloading font list from")
    print("openlilylib-resources/lilypond-notation-fonts")
    try:
        remote = repo.Repo('openlilylib-resources/lilypond-notation-fonts')
        raw_catalogue = remote.fetch('catalogue.json')
        import json
        catalogue = json.loads(raw_catalogue)
        names = [k for k in catalogue.keys()]
        names.sort()
        for name in names:
            f = catalogue[name]
            print('- {}: version {}'.format(f['display-name'], f['version']))
        print("Done, 1")
        import download
        target_file = os.path.join(os.getenv('HOME'), 'catalogue.json')
        try:
            remote.download_file('catalogue.json', target_file)
        except download.FileExistsException as fe:
            print(fe)
            print("Download anyway ...")
            remote.download_file('catalogue.json', target_file, overwrite=True)
            print("... done")

    except Exception as e:
        print("There has been a problem:")
        print(e.__class__)
        print(e)

list_available_fonts()
