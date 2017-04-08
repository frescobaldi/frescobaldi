# qsettings.py -- utility functions related to QSettings
#
# Copyright (c) 2014 - 2014 by Wilbert Berendsen
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
Generic helper functions regarding QSettings
"""


from PyQt5.QtCore import QUrl


def get_string_list(settings, key):
    """Makes sure a list of strings is returned for the key.

    You can write the value with settings.setValue(key, ['bla', 'bla',]), but
    when you need to read the value with settings.value(key, [], str), things
    go wrong when an empty list was stored. So please use this function when
    reading a list of strings from QSettings.

    """
    try:
        value = settings.value(key, [], str)
    except TypeError:
        value = []
    else:
        if not isinstance(value, list):
            if not value:
                value = []
            else:
                value = [value]
    return value


def get_url_list(settings, key):
    """Makes sure a list of QUrl instances is returned for the key.

    You can write the value with settings.setValue(key, [url, url]), but
    when you need to read the value with settings.value(key, [], QUrl), things
    go wrong when an empty list was stored. So please use this function when
    reading a list of strings from QSettings.

    """
    try:
        value = settings.value(key, [], QUrl)
    except TypeError:
        value = []
    else:
        if isinstance(value, QUrl):
            value = []
    return value


