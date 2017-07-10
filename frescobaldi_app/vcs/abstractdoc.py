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
VCS interface - Document() in Repo()
"""

from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QObject, pyqtSignal

class Document(QObject):

    __metaclass__ = ABCMeta

    updated = pyqtSignal()

    @classmethod
    def _create_tmp_file(cls, dir = None, prefix = 'Frescobaldi_vcs_'):
        """Creates a new tmp file and return the path to it.

        CAUTION: Caller is responsible for clean up

        Args:
            dir(string): If dir is specified, the file will be created in that
                directory, otherwise a default directory is used.
            prefix(string): the prefix of new created tmp file

        Returns:
            Return a absolute path to the new tmp file.

        """
        file, filepath = tempfile.mkstemp(prefix = prefix, dir = dir)
        os.close(file)
        return filepath

    @classmethod
    def _write_file(cls, path, content):
        """
        Write the content into the path's corresponding file.
        """
        with open(path, 'wb') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

    @abstractmethod
    def status(cls):
        """This function returns the vcs status of current file
        """
        pass

    @abstractmethod
    def diff_lines(self):
        """Get current file's line-diff result

        Returns:
            tuple: (first, last, [inserted], [modified], [deleted])
                   first: the line number of first changed line
                   last: the line number of last changed line
                   [inserted]: a list contains the numbers of inserted lines
                   [modified]: a list contains the numbers of modified lines

        """
        pass

    @abstractmethod
    def diff_hunk(self, row):
        """Get specific diff hunk

        Args:
            row(int): a line number.

        Returns:
            A dictionary.

        """
        pass
