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
        self._status = None
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

    def status(self):
        if self._status is None:
            self._update_status(blocking = True)
        return self._status

    def _update_status(self, blocking = False):

        def set_status(gitprocess, exitcode):
            if exitcode == 0:
                output_strs = gitprocess.stdout()

                status_dict = {
                    ' M' : ('', (_('modified'))),
                    ' D' : ('', (_('deleted'))),
                    'A ' : ((_('newly added')), ''),
                    'AM' : ((_('newly added')), (_('modified'))),
                    'AD' : ((_('newly added')), (_('deleted'))),
                    'M ' : ((_('staged')), ''),
                    'MM' : ((_('staged')), (_('modified'))),
                    'MD' : ((_('staged')), (_('deleted'))),
                    '??' : ('', (_('untracked'))),
                    '!!' : ('', (_('ignored')))
                    }
                if not output_strs:
                    self._status = ('', (_('committed')))

                try:
                    self._status = status_dict[output_strs[0][:2]]
                except KeyError:
                # return ('', '') when receive a status not listed in status_dict
                    self._status =  ('', '')

                gitprocess.executed.emit(0)
            else:
                # TODO

        # arguments to get file status
        args = [
            'status', '--porcelain', '--ignored', self._relative_path
        ]

        git = gitjob.Git(self._repo)
        git.preset_args = args
        # git.errorOccurred.connect()
        git.finished.connect(set_status)
        if blocking:
            git.run_blocking()
        else:
            self._jobqueue.enqueue(git)

    def _update_temp_index_file(self):

        def write_temp_index_file(gitprocess, exitcode):
            if exitcode == 0:
                # Create temp file
                if not self._temp_index_file:
                    self._temp_index_file = Document._create_tmp_file()
                content = gitprocess.stdout(isbinary = True)
                Document._write_file(self._temp_index_file, content)
                gitprocess.executed.emit(0)
            else:
                # TODO

        args = [
           'cat-file',
            # smudge filters are supported with git 2.11.0+ only
            '--filters' if self._repo.git_ver() >= (2, 11, 0) else '-p',
            ':'+self._relative_path
        ]
        git = gitjob.Git(self._repo)
        git.preset_args = args
        # git.errorOccurred.connect()
        git.finished.connect(write_temp_index_file)
        self._jobqueue.enqueue(git)

    def _update_temp_working_file(self):
        if not self._temp_working_file:
            self._temp_working_file = Document._create_tmp_file()
        content = self._view.document().encodedText()
        Document._write_file(self._temp_working_file, content)

    def _update_temp_committed_file(self):

        def write_temp_committed_file(gitprocess, exitcode):
            if exitcode == 0:
                # Create temp file
                if not self._temp_committed_file:
                    self._temp_committed_file = Document._create_tmp_file()
                content = gitprocess.stdout(isbinary = True)
                Document._write_file(self._temp_committed_file, content)
                gitprocess.executed.emit(0)
            else:
                # TODO

        args = [
           'cat-file',
            # smudge filters are supported with git 2.11.0+ only
            '--filters' if self._git.version() >= (2, 11, 0) else '-p',
            commit + ':'+self._relative_path
        ]

        git = gitjob.Git(self._repo)
        git.preset_args = args
        # git.errorOccurred.connect()
        git.finished.connect(write_temp_committed_file)
        self._jobqueue.enqueue(git)




