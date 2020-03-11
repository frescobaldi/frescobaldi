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
Functions to compose a bugreport via e-mail and to get version information.
"""


from PyQt5.QtCore import QUrl, QUrlQuery

import helpers
import appinfo
import debuginfo


def email(subject, body, recipient=None):
    """Opens the e-mail composer with the given subject and body, with version information added to it."""
    subject = "[{0} {1}] {2}".format(appinfo.appname, appinfo.running_version(), subject)
    body = "{0}\n\n{1}\n\n".format(debuginfo.version_info_string('\n'), body)
    address = recipient or appinfo.maintainer_email
    url = QUrl("mailto:" + address)
    query = QUrlQuery()
    query.addQueryItem("subject", subject)
    query.addQueryItem("body", body)
    url.setQuery(query)
    helpers.openUrl(url, "email")
