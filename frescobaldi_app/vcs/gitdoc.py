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

import os
import re
from enum import IntEnum
from functools import partial

from . import abstractdoc, gitjob, helper

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

    WorkingToHead = CompareTo.WorkingToHead
    WorkingToIndex = CompareTo.WorkingToIndex
    WorkingToCommit = CompareTo.WorkingToCommit
    IndexToHead = CompareTo.IndexToHead
    IndexToCommit = CompareTo.IndexToCommit

    def __init__(self, repo, relative_path, view):
        super().__init__()
        self._repo = repo
        self._view = view
        self._relative_path = relative_path
        self._status = None
        # tuple: ([inserted], [modified], [deleted])
        self._diff_lines = None
        self._diff_cache = None
        self._temp_committed_file = Document._create_tmp_file()
        self._temp_index_file = Document._create_tmp_file()
        self._temp_working_file = Document._create_tmp_file()
        self._jobqueue = gitjob.GitJobQueue()
        self._compare_to = Document.WorkingToHead
        self.update(repoChanged = True, fileChanged = True)
        self._view.textChanged.connect(lambda: self.update(fileChanged = True))

    def __del__(self):
        self._clean_job()

    def _clean_job(self):
        """Do the clean job when destroy the instance or meet errors"""
        self._jobqueue.kill_all()
        if self._temp_committed_file:
            os.unlink(self._temp_committed_file)
        if self._temp_index_file:
            os.unlink(self._temp_index_file)
        if self._temp_working_file:
            os.unlink(self._temp_working_file)

    def _error_handler(self, func_name, error_msg):
        file_name = self._view.document().documentName()
        if type(error_msg) is not str:
            error_msg = helper.GitHelper.error_message[error_msg]
        print("Git Error occurred during running "+ func_name + " on "
                    + file_name + "\n" + error_msg)
        self.disable()

    def disable(self):
        """Disable tracking"""
        self._view.vcsTracked = False
        try: self.diff_updated.disconnect()
        except Exception: pass
        try: self.status_updated.disconnect()
        except Exception: pass
        self._clean_job()

    def view(self):
        return self._view

    def update(self, repoChanged = False, fileChanged = False):
        if self._view.vcsTracked:
            self._update_status()
            self._update_diff_lines(repoChanged, fileChanged)

    def set_compare(self, compare_to):
        if not isinstance(compare_to, CompareTo):
            raise TypeError("Only Document.CompareTo can be passed in")
        self._compare_to = compare_to

    def status(self):
        return self._status

    def diff_lines(self):
        return self._diff_lines

    def diff_hunk(self, row):
        """
        Use cached diff result to extract the changes of the given row.

        Explanation:
            In this function we are looking for a hunk of lines that contains
            given row(int). And then extract its deleted lines, new added
            lines etc. We mainly care about the deleted lines here.

            In git diff, a diff hunk is displayed like this:

            @@ -24,4 +24 @@ Manage a Git repository
            -import os
            -import re
            -import gitjob
            -import tempfile
            +# add a new line

            "@@ -24,4 +24 @@ Manage a Git repository"
            contains the information of the starting position of this hunk.
            By iterating through all this kind of lines, we can locate the
            target hunk.

            The lines begin with '-' have been deleted from the current file.
            The lines begin with '+' are the new added lines in current file.
            Then we extract the deleted lines and the added lines respectively.

        Args:
            row (int): The row to find the diff-hunk for

        Returns:
            dictionary:
                        {
                            # a string array contains the deleted lines
                            'deleted_lines': [],

                            # a string array contains the added lines
                            'added_lines' : [],

                            # the start position of this hunk in original file
                            # -1 if failed to find the hunk
                            'old_start_pos': int,

                            # the number of lines of this hunk in original file
                            # -1 if failed to find the hunk
                            'old_size' : int

                            # the start position of this hunk in current file
                            # -1 if failed to find the hunk
                            'start_pos' : int,

                            # the number of lines of this hunk in current file
                            # -1 if failed to find the hunk
                            'size' : int,

                            # starting position of first hunk
                            # -1 if failed to find the hunk
                            'first_hunk_pos' : int,

                            # starting position of next hunk
                            # -1 if failed to find the hunk
                            'next_hunk_pos' : int,

                            # starting position of previous hunk
                            # -1 if failed to find the hunk
                            'prev_hunk_pos' : int,

                        }

        """
        if self._diff_cache is None:
            return None

        hunk_re = r'^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
        hunks = re.finditer(hunk_re, self._diff_cache, re.MULTILINE)
        # wrapping the hunk list to get surrounding hunks?
        wrap = True
        # extract the starting position of surrounding hunks
        first_hunk_pos = None
        prev_hunk_pos  = None
        next_hunk_pos  = None
        # If the last line of the old file ends with '\n' => False
        # If the last line of the old file ends without '\n' => True
        no_newline_at_end_of_old_file = False
        # If the last line of the new file ends with '\n' => False
        # If the last line of the new file ends without '\n' => True
        no_newline_at_end_of_new_file = False

        for hunk in hunks:
            old_start, old_size, start, size = hunk.groups()
            old_start = int(old_start)
            old_size  = int(old_size or 1)
            start     = int(start)
            size      = int(size or 1)
            if first_hunk_pos is None:
                first_hunk_pos = start
            # special handling to also match the line below deleted content
            if size == 0 and row == start + 1:
                pass
            # continue if the hunk is before the line
            elif start + size < row:
                prev_hunk_pos = start
                continue
            # break if the hunk is after the line
            elif row < start:
                break


            # now we have found the hunk that contains the given row
            try:
                next_hunk = next(hunks)
                hunk_end = next_hunk.start()
                next_hunk_pos = int(next_hunk.group(3))
            except:
                hunk_end = len(self._diff_cache)

            if not wrap:
                if prev_hunk_pos  is None:
                    prev_hunk_pos  = start
                if next_hunk_pos is None:
                    next_hunk_pos = start

            # if prev change is None set it to the wrap around the
            # document: prev -> last hunk, next -> first hunk
            if prev_hunk_pos is None:
                try:
                    remaining_hunks = list(hunks)
                    if remaining_hunks:
                        last_hunk = remaining_hunks[-1]
                        prev_hunk_pos = int(last_hunk.group(3))
                    elif next_hunk_pos is not None:
                        prev_hunk_pos = next_hunk_pos
                    else:
                        prev_hunk_pos = start
                except:
                    prev_hunk_pos = start
            if  next_hunk_pos is None:
                next_hunk_pos = first_hunk_pos

            # extract the content of the hunk
            hunk_content = self._diff_cache[hunk.start():hunk_end]
            # skip first line: '@@ -[OLD_START],[OLD_SIZE] +[START],[SIZE] @@'
            hunk_lines = hunk_content.splitlines()[1:]
            prev_line = None
            deleted_lines = []
            added_lines   = []

            for line in hunk_lines:
                if line.startswith("-"):
                    # store all added lines (starting with +)
                    deleted_lines.append(line[1:])
                elif line.startswith("+"):
                    # store all deleted lines (starting with -)
                    added_lines.append(line[1:])
                elif line == '\\ No newline at end of file':
                    if prev_line.startswith("-"):
                        # '\\ No newline at end of file' is behind a deleted
                        # line. So it means the last line of old file doesn't
                        # end with '\n'
                        no_newline_at_end_of_old_file = True
                    else:
                        # '\\ No newline at end of file' is behind a new added
                        # line. So it means the last line of the new file
                        # doesn't end with '\n'
                        no_newline_at_end_of_new_file = True
                # save the previous line
                prev_line = line

            res = {
                'deleted_lines'  : deleted_lines,
                'added_lines'    : added_lines,
                'old_start_pos'  : old_start,
                'old_size'       : old_size,
                'start_pos'      : start,
                'size'           : size,
                'first_hunk_pos' : first_hunk_pos,
                'next_hunk_pos'  : next_hunk_pos,
                'prev_hunk_pos'  : prev_hunk_pos,
                'no_newline_at_end_of_old_file' : no_newline_at_end_of_old_file,
                'no_newline_at_end_of_new_file' : no_newline_at_end_of_new_file
            }

            return res

        res = {
            'deleted_lines'  : [],
            'added_lines'    : [],
            'old_start_pos'  : -1,
            'old_size'       : -1,
            'start_pos'      : -1,
            'size'           : -1,
            'first_hunk_pos' : -1,
            'next_hunk_pos'  : -1,
            'prev_hunk_pos'  : -1,
            'no_newline_at_end_of_old_file' : False,
            'no_newline_at_end_of_new_file' : False
        }

        return res

    def _update_status(self):

        def set_status(gitprocess, exitcode):
            if exitcode == 0:
                output_lines = gitprocess.stdout()
                status_dict = {
                    ' M' : ('', (_('modified'))),
                    ' D' : ('', (_('deleted'))),
                    'A ' : ((_('added')), ''),
                    'AM' : ((_('added')), (_('modified'))),
                    'AD' : ((_('added')), (_('deleted'))),
                    'M ' : ((_('staged')), ''),
                    'MM' : ((_('staged')), (_('modified'))),
                    'MD' : ((_('staged')), (_('deleted'))),
                    '??' : ('', (_('untracked'))),
                    '!!' : ('', (_('ignored')))
                    }
                if not output_lines:
                    self._status = ('', (_('committed')))
                else:
                    try:
                        self._status = status_dict[output_lines[0][:2]]
                    except KeyError:
                    # return ('', '') when receive a status not listed in status_dict
                        self._status =  ('', '')
                self.status_updated.emit(self)

                # Special case handling
                if self._status[1] == 'ignored':
                    self._diff_lines = ([], [], [])
                    special_case_handle()
                if self._status[1] == 'untracked':
                    self._diff_lines = (list(range(1, self._view.blockCount()+1)), [], [])
                    special_case_handle()
                if self._status[0] == 'added' and self._compare_to & 3 > 0:
                    self._diff_lines = (list(range(1, self._view.blockCount()+1)), [], [])
                    special_case_handle()
                gitprocess.executed.emit(0)
            else:
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))

        def special_case_handle():
            self._diff_cache = ''
            self._jobqueue.kill_all()
            self.diff_updated.emit(self)

        # arguments to get file status
        args = [
            'status', '--porcelain', '--ignored', self._relative_path
        ]

        git = gitjob.Git(self._repo)
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_status')
        git.errorOccurred.connect(error_handler)
        git.finished.connect(set_status)
        self._jobqueue.enqueue(git)

    def _update_diff_lines(self, repoChanged, fileChanged):

        def result_parser(gitprocess, exitcode):
            if gitprocess.stderr():
                # git error is ignored here
                gitprocess.executed.emit(0)
                return
            self._diff_cache = str(gitprocess.stdout(isbinary = True), 'utf-8')
            set_linenum_diff()
            self.diff_updated.emit(self)
            gitprocess.executed.emit(0)

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
            hunk_re = r'^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
            for hunk in re.finditer(hunk_re, self._diff_cache, re.MULTILINE):
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

        if fileChanged and self._compare_to & 8 == 8:
            self._update_temp_working_file()

        if repoChanged:
            self._update_temp_index_file()
            self._update_temp_committed_file()

        if self._compare_to & 8 == 8:
            current = self._temp_working_file
        else:
            current = self._temp_index_file

        if self._compare_to == Document.WorkingToIndex:
            original = self._temp_index_file
        else:
            original = self._temp_committed_file

        args = ['diff', '-U0', '--no-color', '--no-index', original, current]
        git = gitjob.Git(self._repo)
        git.preset_args = args
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
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))

        args = [
           'cat-file',
            # smudge filters are supported with git 2.11.0+ only
            '--filters' if helper.GitHelper.vcs_version() >= (2, 11, 0) else '-p',
            ':'+self._relative_path
        ]
        git = gitjob.Git(self._repo)
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_temp_index_file')
        git.errorOccurred.connect(error_handler)
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
                error_handler(str(gitprocess.stderr(isbinary = True), 'utf-8'))

        if self._compare_to & 2 == 2:
            commit = 'HEAD'
        args = [
           'cat-file',
            # smudge filters are supported with git 2.11.0+ only
            '--filters' if helper.GitHelper.vcs_version() >= (2, 11, 0) else '-p',
            commit + ':'+self._relative_path
        ]

        git = gitjob.Git(self._repo)
        git.preset_args = args
        error_handler = partial(self._error_handler, '_update_temp_committed_file')
        git.errorOccurred.connect(error_handler)
        git.finished.connect(write_temp_committed_file)
        self._jobqueue.enqueue(git)
