# process.py -- A very simple wrapper around QProcess
#
# Copyright (c) 2012 by Wilbert Berendsen
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
A (multithreaded) Job queue
"""

from enum import Enum
import collections
import time

from PyQt5.QtCore import QObject

import app
import job
import signals

class RunnerBusyException(Exception):
    pass

class Runner(QObject):
    """A Runner in the stack of a JobQueue.

    Responsible for executing a single job.Job instance.
    Gets a job and the start command from the queue, reports
    back about completion of the job. Any further actions are
    managed by the queue.
    """

    def __init__(self, queue):
        self._queue = queue
        self._job = None
        self._completed = 0
        self._idle = True

    def abort(self):
        self._job.abort()

    def completed(self):
        """Return the number of completed jobs during the Runner's lifetime."""
        return self._completed

    def idle(self):
        return self._idle

    def running(self):
        return self._job.is_running()

    def job_done(self):
        """Count job, remove reference to Job object, notify queue."""
        self._completed += 1
        self._job = None
        self._queue.job_completed(self)

    def set_idle(self):
        """Set own state to 'idle', have the queue check its IDLE state."""
        self._idle = True
        self._queue.set_idle()

    def start(self, j, force=False):
        """Start a given job.
        If currently a job is running either abort that
        or raise an exception."""
        if self._job and self.running():
            if force:
                self.abort()
            else:
                raise RunnerBusyException(
                    _("Job is already running. Wait for completion."))
        self._job = j
        self._idle = False
        j.done.connect(self.job_done)
        j.start()


class AbstractQueue(QObject):
    """Common interface for the different queue types used in the JobQueue."""

    def clear(self):
        """Remove all entries from the queue."""
        raise NotImplementedError

    def length(self):
        return len(self._queue)

    def push(self, j):
        """Add a job to the queue."""
        raise NotImplementedError

    def pop(self):
        """Remove and return the next job."""
        raise NotImplementedError

class FIFOQueue(AbstractQueue):
    """First-in-first-out queue (default operation)."""

    def __init__(self):
        self._queue = collections.deque()

    def clear(self):
        """Remove all entries from the queue."""
        self._queue.clear()

    def push(self, j):
        self._queue.appendleft(j)

    def pop(self):
        return self._queue.pop()

class LIFOQueue(AbstractQueue):
    """Last-in-first-out queue, or stack."""

    def __init__(self):
        self._queue = collections.deque()

    def clear(self):
        """Remove all entries from the queue."""
        self._queue.clear()

    def push(self, j):
        self._queue.append(j)

    def pop(self):
        return self._queue.pop()


class PriorityQueue(AbstractQueue):
    """Priority queue, always popping the job with the highest priority.

    Uses Job's priority() property (which defaults to 0) and a transparent
    insert count to determine order of popping jobs. If jobs have the same
    priority they will be served first-in-first-out."""

    def __init__(self):
        from heapq import heappush, heappop
        self._queue = []
        self._insert_count = 0

    def clear(self):
        """Remove all entries from the queue."""
        self._queue = []

    def push(self, j):
        """Add a job to the queue. retrieve the priority from the job,
        add an autoincrement value for comparing jobs with identical
        priority."""
        heappush(self._queue, (j.priority(), self._insert_count, j))
        self._insert_count += 1

    def pop(self):
        """Return the correct part of the tuplet
        (1st: priority, 2nd: insert order)."""
        return heappop(self._queue)[2]


class JobQueueException(Exception):
    pass

class JobQueueStateException(JobQueueException):
    pass

class QueueStatus(Enum):
    INACTIVE = 0
    STARTED = 1
    PAUSED = 2
    EMPTY = 3
    IDLE = 4
    FINISHED = 5
    ABORTED = 6

class QueueMode(Enum):
    CONTINUOUS = 0
    SINGLE = 1


class JobQueue(QObject):
    """A (multiThreaded) Job Queue.

    Manages a given number of "runners" which can process one job
    at a time each.

    An arbitrary number of job.Job() instances (or any descendants)
    can be added to the queue, which are distributed in parallel
    to the runners.

    A special case is a queue with only one runner. This can be used
    to ensure that asynchronous jobs can run in sequence, either to
    ensure that only one such job runs at a time (e.g. to force long-running
    stuff to the background) or to ensure subsequent jobs can use the results
    of earlier ones.

    The queue supports pause(), resume() and abort() operations.

    """

    emptied = signals.Signal() # emitted when last job is popped
    finished = signals.Signal()
    idle = signals.Signal() # emitted when waiting for new jobs

    # behaviour when finished (wait for future jobs or finish completely)
    #
    # put (how to handle "block"? I'd say when 1 runner is present
    # jobs block, otherwise not)
    # (raise Exception)
    # get (raise Exception)
    # task_done
    #
    # event handlers (individual job done: handler in Runner, calls into queue)

    def __init__(self,
                 queue_class=FIFOQueue,
                 queue_mode=QueueMode.CONTINUOUS,
                 num_runners=1,
                 tick_interval=1000,
                 capacity=None):
        super(JobQueue, self).__init__()
        self._state = QueueStatus.INACTIVE
        self._queue_mode = queue_mode
        self._starttime = None
        self._endtime = None
        self._completed = 0
        self._queue = queue_class()
        self._capacity = capacity
        self._runners = [Runner(self) for i in range(num_runners)]

        if queue_mode == QueueMode.CONTINUOUS:
            self.start()

    def abort(self, force=True):
        """Abort the execution of the queued jobs.
        If force=True running jobs are aborted, otherwise
        only the queue is cleared, allowing running jobs to finish."""
        if not self.state() in [QueueStatus.STARTED, QueueStatus.PAUSED]:
            raise JobQueueStateException(_("Inactive Job Queue can't be aborted"))
        self.set_state(QueueStatus.ABORTED)
        self.set_queue_mode(QueueMode.SINGLE)
        self._queue.clear()
        if force:
            for runner in self._runners:
                runner.abort()

    def add_job(self, job):
        self._queue.push(job)
        if (self.state() == QueueStatus.IDLE
            or (self.size() == 1 and self.state() == QueueStatus.STARTED)):
            self._start()

    def completed(self, runner=-1):
        """Return the number of completed jobs,
        either for a given runner or the sum of all runners."""
        if runner >= 0:
            return self._runners[runner].completed()
        else:
            result = 0
            for i in range(len(self._runners)):
                result += self._runners[i].completed()
            return result

    def empty(self):
        return self._queue.length() == 0

    def full(self):
        if not self._capacity:
            return False
        return self._queue.length() == self._capacity

    def job_completed(self, runner):
        """Called by a runner once its job has completed."""
        if self.empty():
            if self.queue_mode() == QueueMode.CONTINUOUS:
                runner.set_idle()
            else:
                # also true when ABORTED
                self.remove_runner(runner)
        elif self.state() == QueueStatus.STARTED:
            runner.start(self.pop())
        else:
            # can (?) only happen when PAUSED
            runner.set_idle()

    def pause(self):
        """Pauses the execution of the queue.
        Running jobs are allowed to finish, but no new jobs are started."""
        if not self.state() == QueueStatus.STARTED:
            raise JobQueueStateException(_("Non-running Job Queue can't be paused."))
        self.set_state(QueueStatus.PAUSED)

    def pop(self):
        """Return and remove the next Job.
        Raises Exception if empty."""
        if self.empty():
            raise IndexError("Job Queue is empty.")
        if self.state() != QueueStatus.STARTED:
            raise JobQueueStateException(_("Can't pop job from non-started Job Queue"))
        j = self._queue.pop()
        if self.empty():
            self.set_state(QueueStatus.EMPTY)
            self.emptied.emit()
        return j

    def queue_finished(self):
        if self.state() != QueueStatus.ABORTED:
            self.set_state(QueueStatus.FINISHED)
        self.finished.emit()

    def queue_mode(self):
        return self._queue_mode

    def remove_runner(self, runner):
        """Remove a runner by setting it to None. This is done when
        processing is finished (EMPTY and SINGLE) or after the queue
        has been aborted."""
        self._runners[self._runners.index(runner)] = None
        for runner in self._runners:
            if runner:
                return
        self.queue_finished()

    def resume(self):
        """Resume the queue from PAUSED state by trying to start
        all runners."""
        if not self.state() == QueueStatus.PAUSED:
            raise JobQueueStateException(_("Job Queue not paused, can't resume."))
        self._start()

    def set_idle(self):
        """Set status to IDLE if all runners are in idle mode."""
        for runner in self._runners:
            if not runner.idle():
                return
        self.set_state(QueueStatus.IDLE)
        self.idle.emit()

    def set_queue_mode(self, mode):
        self._queue_mode = mode

    def size(self):
        """Return the number of unstarted jobs."""
        return self._queue.length()

    def _start(self):
        """Set the state to started and ask all runners to start."""
        if self.state() in [QueueStatus.FINISHED, QueueStatus.ABORTED]:
            raise JobQueueStateException(_("Can't (re)start a finished/aborted Job Queue."))
        if self.empty() and self.queue_mode() == QueueMode.SINGLE:
            raise IndexError(_("Can't start empty queue"))
        self.set_state(QueueStatus.STARTED)
        if self.empty():
            return
        else:
            for runner in self._runners:
                if runner.idle() and not self.empty():
                    runner.start(self.pop())

    def start(self):
        """Start processing of the queue."""
        if self.started():
            raise JobQueueStateException(
                _("Can't 'start' an active Job Queue."))
        self._starttime = time.time()
        self._start()

    def started(self):
        return self.state() not in (
            [QueueStatus.INACTIVE,
            QueueStatus.FINISHED,
            QueueStatus.ABORTED])

    def set_state(self, state):
        self._state = state

    def state(self):
        return self._state


class GlobalJobQueue(QObject):
    """The application-wide Job Queue that dispatches jobs to runners
    and subordinate queues.
    """

    def __init__(self):
        self.load_settings()
        self._crawler = JobQueue()
        self._engraver = JobQueue()
        self._generic = JobQueue()
        self._queues = {
            'crawl': self._crawler,
            'engrave': self._engraver,
            'generic': self._generic
        }
        app.settingsChanged.connect(self.settings_changed)
        app.aboutToQuit.connect(self.about_to_quit)

    def about_to_quit(self):
        #TODO:
        # - is any queue active?
        # - should jobs be aborted?
        # - or only the queues be emptied?
        # - _crawer can always be aborted immediately
        pass

    def add_job(self, j, target='engrave'):
        """Add a job to the specified job queue."""
        target_queue = self._queues.get(target, None)
        if not target_queue:
            raise ValueError(_("Invalid job queue target: {}".format(target)))
        target_queue.add_job(j)

    def load_settings(self):
        #TODO: Load settings and create the JobQueues accordingly
        pass

    def settings_changed(self):
        #TODO: If multicore-related settings have changed update the queues
        pass
