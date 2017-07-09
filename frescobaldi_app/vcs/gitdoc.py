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

from . import abstractdoc, gitjob

class Document(abstractdoc.Document):

    def __init__(self, repo, view):
        self._repo = repo
        self._view = view
        self._relative_path = None
        self._temp_committed_file = None
        self._temp_index_file = None
        self._temp_working_file = None
        self._jobqueue = gitjob.GitJobQueue()

    def __del__(self):
        """Caller is responsible for clean up the temp files"""
        if self._temp_committed_file:
            os.unlink(self._temp_committed_file)
        if self._temp_index_file:
            os.unlink(self._temp_index_file)
        if self._temp_working_file:
            os.unlink(self._temp_working_file)




