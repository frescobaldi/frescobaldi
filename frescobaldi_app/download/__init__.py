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
Everything regarding downloading and installing of resources
"""

import ssl
import urllib.request
import urllib.error


class DownloadException(Exception):
    pass


class ServerException(DownloadException):

    def __init__(self, e, url):
        super(ServerException, self).__init__(
            "{e}\nURL: {url}".format(
                e=e,
                url=url
            )
        )
        self.code = e.code


class NotFoundException(DownloadException):

    def __init__(self, url):
        # TODO: Make that translatable again after testing
        super(NotFoundException, self).__init__(
            "404: URL not found\n{url}".format(url=url)
        )


def fetch(url):
    """Download remote content and return the Response object"""
    # TODO:
    # - What can possibly go wrong?
    #   - authentication issue
    #   - no network connection (seems to come across as generic URLError
    #     ("Service not known" or so))
    #   - network connection but no internet access
    #     (is this a different issue from an application's perspective?)
    #    - download interrupted (is this a different issue?)
    # - already dealt with:
    #   - URL not found (handled explicitly)
    #   - server not available/doesn't exist (handled as URLError)
    #   - other server errors (response codes, probably handled)
    #   - download successful but incompatible (e.g. no valid JSON)
    #     => Should be handled by the caller

    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise NotFoundException(url)
        else:
            # This should catch other server side issues (like 500 etc.)
            raise ServerException(e, url)
    except (
        ssl.CertificateError,
        urllib.error.URLError
    ) as e:
        sys.exit()
        raise ServerException(e, url)
    return response

def fetch_content(url):
    """Download a resource and return the content as a string."""
    return fetch(url).read()
