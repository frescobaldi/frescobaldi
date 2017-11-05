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
import os
import tempfile

from PyQt5.QtCore import QObject, QUrl, pyqtSignal

class Document(QObject):

    __metaclass__ = ABCMeta

    diff_updated = pyqtSignal(QObject)
    status_updated = pyqtSignal(QObject)

    _queue_class = None
    
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

    def __init__(self, root_path, relative_path, view):
        super(Document, self).__init__()
        self._view = view
        self._path = os.path.join(root_path, relative_path)
        self._root_path = root_path
        self._relative_path = relative_path
        self._status = None
        # tuple: ([inserted], [modified], [deleted])
        self._diff_lines = None
        self._diff_cache = None
        self._jobqueue = self._queue_class()
        self._create_tmp_files()
        self.update(repoChanged=True, fileChanged=True)
        self._view.textChanged.connect(self._file_changed_update)
        
    def __del__(self):
        """Do the clean job when destroy the instance or meet errors"""
        self._jobqueue.kill_all()
        self._clean_up_temp_files()
    
    @abstractmethod
    def _create_tmp_files(self):
        pass


    @abstractmethod
    def _clean_up_temp_files(self):
        pass

    @classmethod
    def _write_file(cls, path, content):
        """
        Write the content into the path's corresponding file.
        """
        with open(path, 'wb') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

    def _file_changed_update(self):
        self.update(fileChanged = True)

    def view(self):
        return self._view

    def status(self):
        return self._status

    def root(self):
        return self._root_path
    
    def relative_path(self):
        return self._relative_path

    def path(self):
        return self._path
    
    def url(self):
        return QUrl(self._path)
    
    @abstractmethod
    def status(self):
        """This function returns the vcs status of current file
        """
        pass

    def diff_lines(self):
        """Get current file's line-diff result

        Returns:
            tuple: (first, last, [inserted], [modified], [deleted])
                   first: the line number of first changed line
                   last: the line number of last changed line
                   [inserted]: a list contains the numbers of inserted lines
                   [modified]: a list contains the numbers of modified lines

        """
        # TODO: is it clear that when this is called there are already _diff_lines?
        # otherwise it may be necessary to conditionally retrieve them (caching)
        # in order to avoid uninitialized states (but I'm not fully sure if that
        # *is* an issue at all).
        return self._diff_lines


    @abstractmethod
    def diff_hunk(self, row):
        """Get specific diff hunk

        Args:
            row(int): a line number.

        Returns:
            A dictionary.

        """
        pass

    @abstractmethod
    def _update_status(self):
        pass
    
    @abstractmethod
    def _update_diff_lines(repoChanged, fileChanged):
        pass
    
    @abstractmethod
    def is_tracked(self):
        pass

    def update(self, repoChanged = False, fileChanged = False):
        if self.is_tracked():
            # TODO: implement a delay (e.g. 100-500 ms) like with automatic compilation
            # so the update is not called after *every* input but only in typing pauses
            self._update_status()
            self._update_diff_lines(repoChanged, fileChanged)

    def disable(self):
        """Disable tracking"""
        try: self.diff_updated.disconnect()
        except Exception: pass
        try: self.status_updated.disconnect()
        except Exception: pass
        self._clean_job()

