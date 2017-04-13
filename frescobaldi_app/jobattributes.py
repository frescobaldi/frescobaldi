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
Manages a collection of attributes that can be set on a Job.

E.g. from which mainwindow it was started, etc.
"""

import plugin


def get(job):
    """Returns the JobAttributes for the specified Job."""
    return JobAttributes.instance(job)


class JobAttributes(plugin.AttributePlugin):
    """Manages attributes of a Job.

    The attributes can be set simply as instance attributes.
    If possible, weak references are made so the attributes do not keep
    references to the objects they refer to.

    If an attribute is requested but not set, None is returned.

    Usage e.g.:

    attrs = jobattributes.get(job)
    attrs.mainwindow = mainwindow

    """
    def job(self):
        return self._parent()


