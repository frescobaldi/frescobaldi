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

from enum import IntEnum

from . import abstractdoc, gitjob

class Document(abstractdoc.Document):

    class CompareTo(IntEnum):
        """

                             Working Index Head Commit
        WorkingToHead   10 =    1      0     1    0
        WorkingToIndex  12 =    1      1     0    0
        WorkingToCommit 9  =    1      0     0    1
        IndexToHead     6  =    0      1     1    0
        IndexToCommit   5  =    0      1     0    1

        """
        WorkingToHead   = 10
        WorkingToIndex  = 12
        WorkingToCommit = 9
        IndexToHead     = 6
        IndexToCommit   = 5

    def __init__(self, repo, view):
        self._repo = repo
        self._view = view
        self._status = None
        # tuple: ([inserted], [modified], [deleted])
        self._diff_lines = None
        self._diff_cache = None
        self._relative_path = None
        self._temp_committed_outdated = True
        self._temp_committed_file = None
        self._temp_index_outdated = True
        self._temp_index_file = None
        self._temp_working_outdated = True
        self._temp_working_file = None
        self._jobqueue = gitjob.GitJobQueue()
        self._compare_to = CompareTo.WorkingToHead

        # forward enum CompareTo
        self.WorkingToHead = CompareTo.WorkingToHead
        self.WorkingToIndex = CompareTo.WorkingToIndex
        self.WorkingToCommit = CompareTo.WorkingToCommit
        self.IndexToHead = CompareTo.IndexToHead
        self.IndexToCommit = CompareTo.IndexToCommit

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

    def diff_lines(self):
        return self._diff_lines

    def _update_status(self):

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
        self._jobqueue.enqueue(git)

    def _update_diff_lines(self):

        def result_parser(gitprocess, exitcode):
            if exitcode == 0:
                binary_content = gitprocess.stdout(isbinary == True)
                self._diff_cache = binary_content
                set_linenum_diff()
                gitprocess.executed.emit(0)
            else:
                #TODO

        def set_linenum_diff():
            """
            Parse unified diff with 0 lines of context.

            Hunk range info format:
              @@ -3,2 +4,0 @@
                Hunk originally starting at line 3, and occupying 2 lines, now
                starts at line 4, and occupies 0 lines, i.e. it was deleted.
              @@ -9 +10,2 @@
                Hunk size can be omitted, and defaults to one line.

            Dealing with ambiguous hunks:
              "A\nB\n" -> "C\n"
              Was 'A' modified, and 'B' deleted? Or 'B' modified, 'A' deleted?
              Or both deleted? To minimize confusion, let's simply mark the
              hunk as modified.

            """
            # first and last changed line in the view
            first, last = 0, 0
            # lists with inserted, modified and deleted lines
            inserted, modified, deleted = [], [], []
            hunk_re = r'^@@ \-(\d+), ?(\d*) \+(\d+),?(\d*) @@'
            for hunk in re.finditer(hunk_re, self._git_diff_cache, re.MULTILINE):
                # We don't need old_start in this function
                _, old_size, start, new_size = hunk.groups()
                start = int(start)
                # old_size and new_size can be null string
                # means only 1 line has been changed
                old_size = int(old_size or 1)
                new_size = int(new_size or 1)
                if first == 0:
                    first = max(1, start)
                if not old_size:
                    # this is a new added hunk
                    last = start + new_size
                    # [start, last)
                    inserted += range(start, last)
                elif not new_size:
                    # the original hunk has been deleted
                    # only save the starting line number
                    last = start + 1
                    deleted.append(last)
                else:
                    last = start + new_size
                    modified += range(start, last)
            self._diff_lines = (inserted, modified, deleted)

        if self._temp_working_outdated and self._compare_to & 8 == 8:
            self._update_temp_working_file()
        if self._temp_index_outdated and self._compare_to & 4 == 4:
            self._update_temp_index_file()
        if self._temp_committed_outdated and self._compare_to & 3 > 0:
            self._update_temp_committed_file()

        if self._compare_to & 8 == 8:
            current = self._temp_working_file
        else:
            current = self._temp_index_file

        if self._compare_to == self.WorkingToIndex:
            original = self._temp_index_file
        else:
            original = self._temp_committed_file

        args = ['diff', '-U0', '--no-color', '--no-index', original, current]
        git = gitjob.Git(self._repo)
        git.preset_args = args
        # git.errorOccurred.connect()
        git.finished.connect(result_parser)
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




