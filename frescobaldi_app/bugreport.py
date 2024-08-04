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
Function for helping the user to report bugs.
"""

from PyQt6.QtCore import QUrl, QUrlQuery

import helpers
import appinfo
import debuginfo

def new_github_issue(title, body):
    """
    Open a web brower on a page to create a new issue on GitHub.

    Information about the versions of Frescobaldi and its dependencies will
    be appended to the body.

    The body will be sent in the query part of a URL. It is therefore advisable
    not to make it too long. As of this writing, GitHub imposes a limit around
    6000 characters.
    """
    body += "\n\n" + debuginfo.version_info_string()
    url = QUrl(appinfo.issues_url)
    query = QUrlQuery()
    query.addQueryItem("title", title)
    query.addQueryItem("body", body)
    url.setQuery(query)
    helpers.openUrl(url)

def email(subject, body, recipient=None):
    """Opens the e-mail composer with the given subject and body, with version information added to it."""
    subject = f"[{appinfo.appname} {appinfo.version}] {subject}"
    body = "{}\n\n{}\n\n".format(debuginfo.version_info_string('\n'), body)
    address = recipient or appinfo.maintainer_email
    url = QUrl("mailto:" + address)
    query = QUrlQuery()
    query.addQueryItem("subject", subject)
    query.addQueryItem("body", body)
    url.setQuery(query)
    helpers.openUrl(url, "email")
