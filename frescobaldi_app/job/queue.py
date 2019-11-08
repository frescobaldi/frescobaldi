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
import signals


class RunnerBusyException(Exception):
    """Raised when a Runner is asked to start a job (without the force=True
    keyword argument) while having already a running job."""
    pass


class Runner(QObject):
    """A Runner in the stack of a JobQueue.

    Responsible for executing a single job.Job instance.
    Receives a job through the start command from the queue, reports
    back about completion of the job. Any further actions are
    managed by the queue.

    References are kept to the queue and the job as well as the index
    in the queue.
    """

    def __init__(self, queue, index):
        super(Runner, self).__init__()
        self._queue = queue
        self._index = index
        self._job = None
        self._completed = 0

    def abort(self):
        """Aborts a running job if any."""
        if self._job and self._job.is_running():
            self._job.abort()

    def completed(self):
        """Return the number of jobs completed during the Runner's lifetime."""
        return self._completed

    def index(self):
        """Return the index of the Runner in the JobQueue."""
        return self._index

    def is_running(self):
        return self._job and self._job.is_running()

    def job(self):
        return self._job

    def job_done(self):
        """Count job, notify queue, remove reference to Job object."""
        self._completed += 1
        job = self._job
        self._job = None
        self._queue.job_completed(self, job)

    def start(self, j, force=False):
        """Start a given job.
        If currently a job is running either abort that
        or raise an exception."""
        if self._job and self.is_running():
            if force:
                self.abort()
            else:
                raise RunnerBusyException(
                    _("Job is already running. Wait for completion."))
        self._job = j
        j.set_runner(self)
        j.done.connect(self.job_done)
        j.start()


class AbstractQueue(QObject):
    """Common interface for the different queue types used in the JobQueue.
    The various queue classes are very lightweight wrappers around the
    corresponding concepts and base objects, with the only reason to
    provide a transparent interface for used in JobQueue."""

    def __init__(self):
        super(AbstractQueue, self).__init__()

    def clear(self):
        """Remove all entries from the queue."""
        raise NotImplementedError

    def empty(self):
        """Return True if there are no queued items."""
        return self.length() == 0

    def length(self):
        """Return the length of the queue. Only has to be overridden
        when the data structure doesn't support len()."""
        return len(self._queue)

    def push(self, j):
        """Add a job to the queue."""
        raise NotImplementedError

    def pop(self):
        """Remove and return the next job."""
        raise NotImplementedError


class AbstractStackQueue(AbstractQueue):
    """Common ancestor for LIFO and FIFO queues"""

    def __init__(self):
        super(AbstractStackQueue, self).__init__()
        self._queue = collections.deque()

    def clear(self):
        """Remove all entries from the queue."""
        self._queue.clear()

    def pop(self):
        return self._queue.pop()


class Queue(AbstractStackQueue):
    """First-in-first-out queue (default operation)."""

    def push(self, j):
        self._queue.appendleft(j)


class Stack(AbstractStackQueue):
    """Last-in-first-out queue, or stack."""

    def push(self, j):
        self._queue.append(j)


class PriorityQueue(AbstractQueue):
    """Priority queue, always popping the job with the highest priority.

    Uses Job's priority() property (which defaults to 1) and a transparent
    insert count to determine order of popping jobs. If jobs have the same
    priority they will be served first-in-first-out."""

    def __init__(self):
        super(PriorityQueue, self).__init__()
        self._queue = []
        self._insert_count = 0

    def clear(self):
        """Remove all entries from the queue."""
        self._queue = []

    def push(self, j):
        """Add a job to the queue. retrieve the priority from the job,
        add an autoincrement value for comparing jobs with identical
        priority."""
        from heapq import heappush
        heappush(self._queue, (j.priority(), self._insert_count, j))
        self._insert_count += 1

    def pop(self):
        """Return the correct part of the tuplet
        (1st: priority, 2nd: insert order)."""
        from heapq import heappop
        return heappop(self._queue)[2]


class JobQueueException(Exception):
    """Abstract base exception for JobQueue related exceptions."""
    pass


class JobQueueStateException(JobQueueException):
    """Raised when an operation is not allowed in the current
    state of the queue."""
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
    """Running mode of the JobQueue.
    CONTINUOUS means that the queue can be idle, waiting for new jobs,
    SINGLE means that it will be considered finished when running empty."""
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
    ensure that only one such job runs at a time (e.g. to force
    long-running stuff to the background) or to ensure subsequent
    jobs can use the results of earlier ones.

    The queue supports pause(), resume() and abort() operations.
    It iterates through the states
    QueueStatus.INACTIVE
                STARTED
                PAUSED (remaining jobs won't be started)
                EMPTY (no *new* jobs are queued)
                IDLE (no new jobs available, all jobs completed)
                FINISHED
                ABORTED

    A Queue can work in two modes: QueueMode.CONTINUOUS (default) and
    QueueMode.SINGLE. In single mode the queue is considered finished once
    there are no jobs available while a continuous queue switches to
    IDLE in that case. A CONTINUOUS queue is always considered to be
    active (idle when empty) and doesn't have to be explicitly started.

    If a 'capacity' is passed to the queue it has the notion of "full",
    otherwise an unlimited number of jobs can be enqueued.

    By default an internal FIFO (First in, first out) Queue is used
    as the underlying data structure, but Stack and PriorityQueue are
    available through the keyword command as well.
    """

    started = signals.Signal()
    paused = signals.Signal()
    resumed = signals.Signal()
    emptied = signals.Signal()  # emitted when last job is popped
    idle = signals.Signal()  # emitted when waiting for new jobs
                             # after the last job has been completed
    finished = signals.Signal()
    aborted = signals.Signal()
    # The following three signals emit the corresponding job as argument.
    job_added = signals.Signal()
    job_done = signals.Signal()  # emitted when a job has been completed.
               # When this is emitted, the queue's state has been
               # updated (other than with the *job's* signal)
    job_started = signals.Signal()

    def __init__(self,
                 queue_class=Queue,
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
        self._runners = [Runner(self, i) for i in range(num_runners)]

        if queue_mode == QueueMode.CONTINUOUS:
            self.start()

    def abort(self, force=True):
        """Abort the execution of the queued jobs.
        If force=True running jobs are aborted, otherwise
        only the queue is cleared, allowing running jobs to finish."""
        if self.state() in [
            QueueStatus.FINISHED,
            QueueStatus.ABORTED
        ]:
            raise JobQueueStateException(
                _("Inactive Job Queue can't be aborted")
            )
        self.set_state(QueueStatus.ABORTED)
        self.set_queue_mode(QueueMode.SINGLE)
        self._queue.clear()
        if force:
            for runner in self._runners:
                if runner:
                    # ignore runners that have already been set to None
                    runner.abort()
        self.aborted.emit()

    def add_job(self, job):
        """Enqueue a new job to the queue.

        Some checks are made to determine the validity of adding a new job.
        If the queue hasn't started yet or is in pause the job is simply
        pushed to the queue, otherwise it will be determined whether an
        idle runner is available to start with the job immediately.
        """
        if self.full():
            raise IndexError(_("Job Queue full"))
        if self.state() in [QueueStatus.FINISHED, QueueStatus.ABORTED]:
            raise JobQueueStateException(
                _("Can't add job to finished/aborted queue.")
            )
        elif self.state() in [QueueStatus.INACTIVE, QueueStatus.PAUSED]:
            self._queue.push(job)
            self.job_added.emit(job)
        else:
            runner = self.idle_runner()
            if runner:
                self.job_added.emit(job)
                runner.start(job)
                self.job_started.emit(job)
            else:
                self._queue.push(job)
                self.job_added.emit(job)
            self.set_state(
                QueueStatus.EMPTY if self._queue.empty()
                else QueueStatus.STARTED)

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

    def full(self):
        """Returns True if a maximum capacity is set and used."""
        if not self._capacity:
            return False
        return self._queue.length() == self._capacity

    def is_idle(self):
        """Returns True if all Runners are idle."""
        for runner in self._runners:
            if runner.is_running():
                return False
        return True

    def is_running(self):
        """Return True if the queue is 'live'."""
        return self.state() not in ([
            QueueStatus.INACTIVE,
            QueueStatus.FINISHED,
            QueueStatus.ABORTED
        ])

    def idle_runner(self):
        """Returns the first idle Runner object,
        or None if all are busy."""
        for runner in self._runners:
            if not runner.is_running():
                return runner
        return None

    def job_completed(self, runner, job):
        """Called by a runner once its job has completed.

        Manage behaviour at that point, depending on the
        queue's state and mode.
        """
        if self.state() == QueueStatus.STARTED:
            runner.start(self.pop())
        elif self.state() == QueueStatus.PAUSED:
            # If a SINGLE queue completes the last job while in PAUSE mode
            # it can be considered finished.
            if (
                self._queue.empty()
                and self.is_idle()
                and self.queue_mode() == QueueMode.SINGLE
            ):
                self.queue_finished()
        elif self.is_idle():
            # last runner has completed its job and queue is empty.
            # Either finish queue or set to IDLE.
            if self.queue_mode() == QueueMode.SINGLE:
                self.queue_finished()
            else:
                self.set_state(QueueStatus.IDLE)
                self.idle.emit()
        self.job_done.emit(job)

    def pause(self):
        """Pauses the execution of the queue.
        Running jobs are allowed to finish, but no new jobs will be started.
        (The actual behaviour is implemented in job_completed().)"""
        if self.state() in [
            QueueStatus.INACTIVE,
            QueueStatus.FINISHED,
            QueueStatus.ABORTED
        ]:
            raise JobQueueStateException(
                _("Non-running Job Queue can't be paused.")
            )
        self.set_state(QueueStatus.PAUSED)
        self.paused.emit()

    def pop(self):
        """Return and remove the next Job.
        Raises Exception if empty."""
        if self.state() == QueueStatus.EMPTY:
            raise IndexError("Job Queue is empty.")
        if self.state() != QueueStatus.STARTED:
            raise JobQueueStateException(
                _("Can't pop job from non-started Job Queue")
            )
        j = self._queue.pop()
        if self._queue.empty():
            self.set_state(QueueStatus.EMPTY)
            self.emptied.emit()
        return j

    def queue_finished(self):
        """Called when the last job has been completed and the queue
        is in SINGLE mode."""
        if self.state() != QueueStatus.ABORTED:
            self.set_state(QueueStatus.FINISHED)
        self.finished.emit()

    def queue_mode(self):
        return self._queue_mode

    def resume(self):
        """Resume the queue from PAUSED state by trying to start
        all runners."""
        if not self.state() == QueueStatus.PAUSED:
            raise JobQueueStateException(
                _("Job Queue not paused, can't resume.")
            )
        self._start()
        self.resumed.emit()

    def set_idle(self):
        """Set status to IDLE if all runners are in idle mode."""
        for runner in self._runners:
            if runner.is_running():
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
            raise JobQueueStateException(
                _("Can't (re)start a finished/aborted Job Queue.")
            )
        elif self.state() == QueueStatus.STARTED:
            raise JobQueueStateException(_("Queue already started."))
        if self.state() in [
            QueueStatus.INACTIVE,
            QueueStatus.PAUSED
        ]:
            self.set_state(QueueStatus.STARTED)

        if (
            self.state() == QueueStatus.EMPTY
            and self.queue_mode() == QueueMode.SINGLE
        ):
            raise IndexError(_("Can't start SINGLE-mode empty queue"))
        if self._queue.empty():
            self.set_state(QueueStatus.IDLE)
        else:
            self.set_state(QueueStatus.STARTED)
            for runner in self._runners:
                if self._queue.empty():
                    break
                if not runner.is_running():
                    runner.start(self.pop())

    def start(self):
        """Start processing of the queue."""
        if self.is_running():
            raise JobQueueStateException(
                _("Can't 'start' an active Job Queue."))
        self._starttime = time.time()
        self._start()
        self.started.emit()

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
        # TODO:
        # - is any queue active?
        # - should jobs be aborted?
        # - or only the queues be emptied?
        # - _crawer can always be aborted immediately
        pass

    def add_job(self, j, target='engrave'):
        """Add a job to the specified job queue."""
        target_queue = self._queues.get(target, None)
        if not target_queue:
            raise ValueError(_("Invalid job queue target: {name}").format(name=target))
        target_queue.add_job(j)

    def load_settings(self):
        # TODO: Load settings and create the JobQueues accordingly
        pass

    def settings_changed(self):
        # TODO: If multicore-related settings have changed update the queues
        pass
