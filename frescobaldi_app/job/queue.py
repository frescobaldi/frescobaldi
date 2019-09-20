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
A (multithreaded) Job queue.

This module manages the resources spent on external processes
within Frescobaldi, all jobs are handled through this manager.

A global job queue is available as app.job_queue(), holding a
requested number of total Runners. By default three JobQueue
items are present: "engrave", "generic" and "crawl", but custom
queues can be added, for example by extensions.
Job.start() will not start the job immediately but instead add
it to the queue, which will in turn check if it can be started
or has to be enqueued.

Queues can be CONTINUOUS or SINGLE, which basically determines
the behaviour when the last job has finished.

Queues can request a number of dedicated runners and may share
all or a specific number of shared runners. This ensures that
a queue can have exclusive access to a given number or runners
while avoiding to be overly agressive.

The global job queue emits signals related to the jobs (job_added,
job_enqueued etc.) which will occur *after* the corresponding
signals of the jobs themselves. Additionally the queues emit
signals when their states change.

TODO: Not implemented yet is an option that SINGLE queues can
request additional dedicated runners. These will be assigned
when starting and released when finished. That makes it possible
to use all resources for batch compilations.
"""

from enum import Enum
import collections
import time

from PyQt5.QtCore import QObject

import app
from signals import Signal


class RunnerBusyException(Exception):

    """Runner is busy

    Raised when a Runner is asked to start a job (without the force=True
    keyword argument) while having already a running job.

    """
    pass


class Runner(QObject):

    """A Runner in the stack of the global job queue.

    Responsible for executing a single job.Job instance.
    Receives a job through the start command from a job queuequeue,
    reports back about completion of the job. Any further actions
    are managed by the queue.

    Upon first use app.job_queue() instantiates the requested number
    of Runner objects. The runners originally populate a pool of
    *shared* runners but may be assigned as dedicated runners
    to specific job queues.
    The remaining shared runners are temporarily assigned to job queues
    and reclaimed after the job's completion.

    Runners in the shared pool have the GlobalJobQueue as parent()
    and are re-parented when assigned to a JobQueue as dedicated runner.
    This means: runner.parent() does not necessarily point to the
    queue the job has been enqued in. This can be retrieved through
    runner.job().queue()

    """

    def __init__(self, parent, index):
        super(Runner, self).__init__(parent)
        self._index = index
        self._job = None
        self._completed_jobs = 0

    def abort(self, silent=False):
        """Aborts a running job if any."""
        if self.is_running():
            self._job.abort()
        # TODO: Is job_done() still called or do I have to handle the
        # case manually?
        # (https://github.com/frescobaldi/frescobaldi/issues/1184)
        # Especially note that the runner has to be "released".
        #
        # if silent=True it must be ensured that there is *no*
        # call to JobQueue.job_completed. If the runner has to
        # abort a current job to force-start a new one we don't
        # want the runner handling from there. Maybe the signal
        # should be sent anyway?

    def completed_jobs(self):
        """Return the number of jobs completed during the Runner's lifetime."""
        return self._completed_jobs

    def index(self):
        """Return the index of the Runner in the global pool."""
        return self._index

    def is_running(self):
        return bool(self._job and self._job.is_running())

    def is_shared(self):
        """Returns True if the runner is part of the shared runner pool.
        This holds True even while the runner is stored within a queue."""
        return self.parent() == app.job_queue()

    def job(self):
        """Return the Job instance.
        Is None when idle."""
        return self._job

    def job_done(self, job):
        """Count job, remove reference to Job object and notify queue."""
        self._completed_jobs += 1
        job.set_runner(None)
        self._job = None
        job.queue().job_completed(self, job)

    def start(self, j, force=False):
        """Start a given job.
        If currently a job is running either abort that
        or raise an exception."""
        if self.is_running():
            if force:
                self.abort(silent=True)
            else:
                raise RunnerBusyException(
                    _(
                        "Runner {ind} in Job Queue {q} is already running.\n"
                        "Job: {title}".format(
                            ind=self.index(),
                            title=self._job.title(),
                            q=self._job.queue().title()
                        )))
        self._job = j
        j.set_runner(self)
        j._start()


class QueueException(Exception):
    """Base class for queue-related exceptions."""
    pass


class QueueFullException(QueueException):
    """Raised when trying to push to a full queue."""
    pass


class AbstractQueue(QObject):

    """Common interface for the different queue types used in the JobQueue.

    The various queue classes are very lightweight wrappers around the
    corresponding concepts and base objects, with the only reason to
    provide a transparent interface for used in JobQueue.

    parent should be the JobQueue using the queue.

    If a capacity is given this limits the number of items that can be
    added to the queue before raising an exception.
    TODO: It *may* be of interest to add an option not to raise the exception
    but rather to push out an element at the other end.

    """

    def __init__(
        self,
        parent=None,
        capacity=None
    ):
        super(AbstractQueue, self).__init__(parent)
        self._capacity = capacity

    def clear(self):
        """Remove all entries from the queue."""
        raise NotImplementedError

    def full(self):
        """Return True if the capacity - if set - is complete."""
        return (
            self._capacity is not None
            and self.length() >= self._capacity
        )

    def empty(self):
        """Return True if there are no queued items."""
        return self.length() == 0

    def length(self):
        """Return the length of the queue. Has to be overridden
        if the data structure doesn't support len()."""
        return len(self._queue)

    def peek(self):
        """Return a reference to the next element
        that would be removed by pop()."""
        raise NotImplementedError

    def _push(self, j):
        raise NotImplementedError

    def push(self, j):
        """Add a job to the queue.

        Tests if the queue is full and calls self._push().
        Override _push() in subclasses.
        """
        if self.full():
            raise QueueFullException(_("Trying to add item to full queue"))
        self._push(j)

    def _pop(self):
        """Remove and return the next job."""
        raise NotImplementedError

    def pop(self):
        return None if self.empty() else self._pop()


class AbstractStackQueue(AbstractQueue):
    """Common ancestor for LIFO and FIFO queues"""

    def __init__(
        self,
        job_queue=None,
        capacity=None
    ):
        super(AbstractStackQueue, self).__init__(job_queue, capacity)
        self._queue = collections.deque()

    def clear(self):
        """Remove all entries from the queue."""
        self._queue.clear()

    def peek(self):
        """
        Return a reference to the next element
        to be popped, but without removing it.
        """
        return None if self.empty() else self._queue[-1]

    def _pop(self):
        return self._queue.pop()


class Queue(AbstractStackQueue):
    """First-in-first-out queue (default operation)."""

    def _push(self, j):
        self._queue.appendleft(j)


class Stack(AbstractStackQueue):
    """Last-in-first-out queue, or stack."""

    def _push(self, j):
        self._queue.append(j)


class PriorityQueue(AbstractQueue):
    """Priority queue, always popping the job with the lowest priority.

    Uses Job's priority() property (which defaults to o) and a transparent
    insert count to determine order of popping jobs. If jobs have the same
    priority they will be served first-in-first-out."""

    def __init__(
        self,
        job_queue=None,
        capacity=None
    ):
        super(PriorityQueue, self).__init__(job_queue, capacity)
        self._queue = []
        self._insert_count = 0

    def clear(self):
        """Remove all entries from the queue."""
        self._queue = []

    def _push(self, j):
        """Add a job to the queue. retrieve the priority from the job,
        add an autoincrement value for comparing jobs with identical
        priority."""
        from heapq import heappush
        heappush(self._queue, (j.priority(), self._insert_count, j))
        self._insert_count += 1

    def peek(self):
        """Return the third element (the job) in the "lowest"/next entry."""
        return self._queue[0][2] if not self.empty() else None

    def _pop(self):
        """Return the correct part of the tuple
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


class JobQueueNotFoundException(JobQueueException):
    """Raised when a non-existent named JobQueue is requested
    from the global JobQueue."""
    pass


class QueueStatus(Enum):
    """ Possible Queue states.

    INACTIVE: Before even started, only interesting in SINGLE queues
    STARTED:  Contains running and queued jobs, not paused
    PAUSED:   Further jobs will not be started, but there may
              be currently running or queued jobs
    EMPTY:    No queued jobs, but there may be some still running
    IDLE:     No queued or running jobs, but ready to start new ones
    FINISHED: After the last job in a SINGLE queue has completed
    ABORTED:  Queue has been aborted, but there may still be jobs running

    """
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
    SINGLE means that it will be considered finished when running empty.

    """
    CONTINUOUS = 0
    SINGLE = 1


class JobQueue(QObject):

    """A (multiThreaded) Job Queue.

    Manages external resources for a specific purpose, assigning
    jobs to dedicated and/or shared Runner objects.

    Runners can be requested to be dedicated to a queue.
    This makes sure that the resources are exclusively avaiable to
    the queue (e.g. the "crawler" will always have one runner
    available) - but this also implies that the runner is *not*
    available to others.

    All runners that are not dedicated to a queue are in a pool of
    shared runners and will be assigned to the next queued job.
    TODO:
    Right now GlobalJobQueue.reclaim_shared_runner has a trivial
    approach to deciding which queue will get a free runner. This
    has to be reconsidered and also (stress-)tested.

    When calling Job.start() the job will be added to its assigned
    job queue ("generic" by default, and "engrave" by default for
    LilyPond jobs). The queue will then decide whether the job can
    be started immediately or has to be enqueued.

    A special case is a queue with only one runner. This can be used
    to ensure that asynchronous jobs can run in sequence, either to
    ensure that only one such job runs at a time (e.g. to force
    long-running stuff to the background) or to ensure that subsequent
    jobs can use the results of earlier ones.

    The queue supports pause(), resume() and abort() operations.
    start() has only to be called explicitly for SINGLE mode queues.

    If a 'capacity' is passed to the queue it has the notion of "full",
    otherwise an unlimited number of jobs can be enqueued.

    By default an internal FIFO (First in, first out) Queue is used
    as the underlying data structure, but Stack and PriorityQueue are
    available through the keyword command as well.
    """

    # Signals relating to the queue as a whole
    started = Signal()
    paused = Signal()
    resumed = Signal()
    empty = Signal()  # emitted when last job is popped
    idle = Signal()     # emitted when waiting for new jobs
                        # after the last job has been completed
    finished = Signal()
    aborted = Signal()

    def __init__(
        self,
        parent=None,
        name='',
        title='',
        queue_class=Queue,
        queue_mode=QueueMode.CONTINUOUS,
        runners=[],
        max_shared=False,
        capacity=None
    ):
        super(JobQueue, self).__init__(parent)
        self._name = name
        self._title = title or name
        self._state = QueueStatus.INACTIVE
        self._queue_mode = queue_mode
        self._starttime = None
        self._endtime = None
        self._completed = 0
        self._queue = queue_class(self, capacity=capacity)
        self._runners = runners
        for r in runners:
            r.setParent(self)
        self._running = []
        self._shared_running = []
        self._max_shared = max_shared
        self.signals = {
            QueueStatus.STARTED: self.started,
            QueueStatus.PAUSED: self.paused,
            QueueStatus.EMPTY: self.empty,
            QueueStatus.IDLE: self.idle,
            QueueStatus.FINISHED: self.finished,
            QueueStatus.ABORTED: self.aborted
        }

        if queue_mode == QueueMode.CONTINUOUS:
            self.start()

    def abort(self, force=True):
        """Abort the execution of the queued jobs.

        If force=True running jobs are aborted, otherwise
        only the queue is cleared, allowing running jobs to finish.

        """
        if self.state() in [
            QueueStatus.FINISHED,
            QueueStatus.ABORTED
        ]:
            raise JobQueueStateException(
                _("Inactive Job Queue can't be aborted")
            )
        # do not use set_state because we don't want
        # to send the signal already now
        self._state = QueueStatus.ABORTED
        self._queue.clear()
        if force:
            for runner in self._running + self._shared_running:
                runner.abort()

    def enqueue_job(self, job):
        """Enqueue a job

        Called by add_job when the job can't be started immediately.
        Push it to the internal queue, let job acknowledge the new state
        and announce it.
        """
        self._queue.push(job)
        job.enqueue()
        app.job_queue().job_enqueued(job)

    def add_job(self, job):
        """Add a new job to the queue (enqueue/start).

        Some checks are made to determine the validity of adding a new job.
        If the queue hasn't started yet or is in pause the job is simply
        pushed to the queue, otherwise it will be determined whether an
        idle runner is available to start with the job immediately.
        """

        if self.full():
            raise IndexError(_("Job Queue '{}' full").format(self.title()))
        elif self.state() in [QueueStatus.FINISHED, QueueStatus.ABORTED]:
            raise JobQueueStateException(_(
                "Can't add job '{job}' to finished/aborted queue '{queue}'."
            ).format(
                job=job.title(),
                queue=self.title()
            ))
        else:
            # The job can be added to the queue
            app.job_queue().job_added(job)
            if self.is_running():
                self.set_state(QueueStatus.STARTED)
                runner = self.idle_runner()
                if runner:
                    self.start_job(runner, job)
                    return
            # Queue is not running or no idle runner is available
            self.enqueue_job(job)

    def add_shared_runner(self, runner):
        """Temporarily claim a shared runner.

        The list is empty when no shared runners are used.
        """
        self._shared_running.append(runner)

    def full(self):
        """Returns True if a maximum capacity is set and used."""
        return self._queue.full()

    def is_empty(self):
        """Returns True if there are no queued jobs."""
        return self._queue.empty()

    def is_idle(self):
        """Returns True if no Runners are in the _running lists
        """
        return not self._running + self._shared_running

    def is_running(self):
        """Return True if the queue is 'live'.

        This doesn't mean that there are running jobs, though.
        """
        return self.state() not in ([
            QueueStatus.INACTIVE,
            QueueStatus.PAUSED,
            QueueStatus.FINISHED,
            QueueStatus.ABORTED
        ])

    def idle_runner(self):
        """
        Tries to locate an idle Runner object,
        first in the queue's dedicated runners,
        then requesting one from the shared pool.
        """
        # Find an idle dedicated runner and return it
        if self._runners:
            runner = self._runners.pop()
            self._running.append(runner)
            return runner
        # If none is found and our limit to shared runners
        # hasn't been reached, request one from the shared pool.
        # Returns None if no shared runner is available.
        if (
            self.max_shared() == False
            or len(self._shared_running) < self.max_shared()
        ):
            shared_runner = app.job_queue().idle_runner()
            if shared_runner:
                self.add_shared_runner(shared_runner)
                return shared_runner

    def job_completed(self, runner, job):
        """Called by a runner once its job has completed.

        NOTE: runner.job() is already None at that point,
        that's why the job is passed separately.
        """

        new_state = None
        cur_state = self.state()
        cur_mode = self.queue_mode()
        self.release_runner(runner)
        # First update the state (if necessary)
        if self.is_empty():
            # there are no further jobs to add
            if self.is_idle():
                # and none running either
                if cur_state == QueueStatus.STARTED:
                    new_state = QueueStatus.IDLE
                elif cur_state == QueueStatus.ABORTED:
                    # We only signal this here because we didn't
                    # do so in abort() (because abort may or may
                    # not abort the individual jobs)
                    self.job_aborted()
                elif cur_mode == QueueMode.SINGLE:
                    new_state = QueueStatus.FINISHED
            else:
                # empty but other runners are still running
                pass
        else:
            # There are further jobs in the queue, no need to do anything
            pass

        if new_state:
            self.set_state(new_state)
        app.job_queue().job_finished(job)

        if runner.is_shared():
            # Allow the global queue to start a job from an arbitrary queue
            app.job_queue().reclaim_shared_runner(runner)
        elif self.state() == QueueStatus.STARTED:
            # Allow the next queued job to start
            runner.start(self.pop())

    def length(self):
        """Return the number of unstarted jobs."""
        return self._queue.length()

    def max_shared(self):
        """
        Returns the maximum number of shared runners
        this queue is allowed to request.
        False if not limited.
        """
        return self._max_shared

    def name(self):
        """The name (key) of the job queue. See also title()"""
        return self._name

    def pause(self):
        """Pauses the execution of the queue.
        Running jobs are allowed to finish, but no new jobs will be started.
        (The actual behaviour is implemented in job_completed().)

        TODO: This has to be properly tested.
        """
        if not self.is_running():
            raise JobQueueStateException(
                _("Non-running Job Queue can't be paused.")
            )
        self.set_state(QueueStatus.PAUSED)

    def peek(self):
        """Return a reference to the next job
        that would be popped from this queue.
        """
        return self._queue.peek()

    def pop(self):
        """Return and remove the next Job.
        Raises Exception if empty."""
        if self.is_empty():
            raise IndexError("Job Queue is empty.")
        if self.state() != QueueStatus.STARTED:
            raise JobQueueStateException(
                _("Can't pop job from non-started Job Queue")
            )
        j = self._queue.pop()
        if self.is_empty():
            self.set_state(QueueStatus.EMPTY)
        return j

    def queue_mode(self):
        return self._queue_mode

    def release_runner(self, runner):
        """Release a runner from the shared or dedicated
        runners reference list."""
        try:
            i = self._running.index(runner)
            self._runners.append(self._running.pop(i))
        except:
            self._shared_running.remove(runner)

    def resume(self):
        """Resume the queue from PAUSED state by trying to start
        all runners.

        TODO: This has to be properly tested.
        """
        if not self.state() == QueueStatus.PAUSED:
            raise JobQueueStateException(
                _("Job Queue not paused, can't resume.")
            )
        self._start()
        self.resumed(self)

    def _start(self):
        """(Re)start the queue, also through resume().

        Set the state to started and ask all runners to start.
        """

        def check_exceptions():
            no_restart = JobQueueStateException(
                _("Can't (re)start a finished/aborted Job Queue.")
            )
            already_started = JobQueueStateException(
                _("Queue already started.")
            )
            empty_single = IndexError(
                _("Can't start SINGLE-mode empty queue")
            )
            exceptions = {
                QueueStatus.FINISHED: no_restart,
                QueueStatus.ABORTED: no_restart,
                QueueStatus.STARTED: already_started,
            }
            exception = exceptions.get(self.state(), None)
            if (
                self.state() == QueueStatus.EMPTY
                and self.queue_mode() == QueueMode.SINGLE
            ):
                exception = empty_single
            if exception:
                raise exception

        check_exceptions()
        self.set_state(QueueStatus.STARTED)
        if self.is_empty():
            self.set_state(QueueStatus.IDLE)
        else:
            runner = self.idle_runner()
            while runner:
                if self.is_empty():
                    self.set_state(QueueStatus.EMPTY)
                    break
                runner.start(self.pop())
                runner = self.idle_runner()

    def start(self):
        """Start processing of the queue."""
        if self.is_running():
            raise JobQueueStateException(
                _("Can't 'start' an active Job Queue."))
        self._starttime = time.time()
        self._start()
        self.started()

    def start_job(self, runner, job):
        """Start a specific job.

        Availability of job and runner have been determined before.
        """
        runner.start(job)
        self.set_state(
            QueueStatus.EMPTY if self.is_empty()
            else QueueStatus.STARTED
        )
        app.job_queue().job_started(job)

    def set_state(self, state):
        """Set the queue's state.

        Set the state, and send the signal if this implies a change.
        """
        if self._state != state:
            self._state = state
            self.signals[state](self)

    def state(self):
        """Return the queue's QueueStatus value."""
        return self._state

    def title(self):
        """Return the queue's title."""
        return self._title


class GlobalJobQueue(QObject):
    """The application-wide Job Queue that dispatches jobs to runners
    and subordinate queues.
    """

    # Signals related to individual queues, passing the queue as argument.
    queue_started = Signal()
    queue_paused = Signal()
    queue_resumed = Signal()
    queue_empty = Signal()
    queue_idle = Signal()
    queue_finished = Signal()
    queue_aborted = Signal()

    # Signals related to individual jobs, passing the job as argument.
    # From there the queue may be retrieved, while the runner is
    # already detached.
    # Whenever a job is added the job_added signal is emitted,
    # after that there may be job_enqueued. job_started is emitted
    # when the job has actually started
    job_added = Signal()
    job_enqueued = Signal()
    job_started = Signal()
    job_finished = Signal() # emitted when a job has been completed.
                        # When this is emitted, the queue's state has been
                        # updated (other than with the *job's* signal)

    def __init__(self, parent=None):
        super(GlobalJobQueue, self). __init__(parent)

        # Create the globally available runners
        self._runners = [Runner(self, i) for i in range(app.available_cores())]
        # assign all runners to the pool of shared runners
        self._shared_runners = [r for r in self._runners]

        self.load_settings()
        self._queue_order = []
        self._next_queue = -1
        self._create_queues()
        app.settingsChanged.connect(self.settings_changed)
        app.aboutToQuit.connect(self.about_to_quit)

    def about_to_quit(self):
        # TODO:
        # - is any queue active?
        # - should jobs be aborted?
        # - or only the queues be emptied?
        # - crawler can always be aborted immediately
        pass

    def available_cores(self):
        """
        Returns the number of cores that are available
        within Frescobaldi.
        """
        return len(self._runners)

    def available_shared(self):
        """
        Returns the number of shared runners.
        Must not get below 0.
        """
        return len(self._shared_runners)

    def completed_jobs(self, runner=-1):
        """Return the number of completed jobs,
        either for a given runner or the sum of all runners."""
        if runner >= 0:
            return self._runners[runner].completed_jobs()
        else:
            result = 0
            for runner in self._runners:
                result += runner.completed_jobs()
            return result

    def create_queue(self, name, title, dedicated=0, max_shared=False):
        """Create a new queue.

        TODO: This is totally preliminary while the resource sharing
        has to be thought through:
        - handling of shared runners must be dealt with in the queue
        - it should be possible to change the behaviour at runtime:
          a build tool might reserve a number of runners for a specific
          run and give them back afterwards.

        """

        if name in self._queue_order:
            raise Exception("Queue of that name already exists.")
        elif self.available_shared() - dedicated < 1:
            # TODO: Discuss if there really must be one shared runner left
            # or if we could instead check whether all queues have at least
            # one dedicated runner.
            raise Exception("No shared runners left to be assigned")
        self._queues[name] = queue = JobQueue(
            self,
            name=name,
            title=title,
            runners=([self._runners.pop() for i in range(dedicated)]),
            max_shared=max_shared
        )
        self._queue_order.append(name)

        queue.started.connect(self.queue_started)
        queue.paused.connect(self.queue_paused)
        queue.resumed.connect(self.queue_resumed)
        queue.empty.connect(self.queue_empty)
        queue.idle.connect(self.queue_idle)
        queue.finished.connect(self.queue_finished)
        queue.aborted.connect(self.queue_aborted)

    def _create_queues(self):
        """Create the initial main queues.

        Frescobaldi itself maintains three queues:
        - 'engrave' (mainly for engraving jobs)
        - 'generic' (for arbitrary jobs like imports or previews)
        - 'crawler' (for background jobs)
        Additional queues may be created by extensions.

        TODO: Has to use the settings

        """

        # TODO: This is an initial implementation where all three
        # JobQueue objects share all available Runner instances.
        # For thoughts about the distribution see the class comment in
        # preferences.multicore.Queues

        self._queues = {}
        self.create_queue(
            'engrave',
            _('Engraver Queue'),
            dedicated=0,
            max_shared=False
        )
        self.create_queue(
            'generic',
            _('Generic Queue'),
            dedicated=0,
            max_shared=False
        )
        self.create_queue(
            'crawl',
            _('Background Crawler'),
            dedicated=0,
            max_shared=False
        )

    def get_next_job(self):
        """Poll all queues for their next job.
        If there are any, decide which one to start.
        """

        def next_queue_index():
            """Return the index of the next queue

            ... in a list that behaves like a ring buffer.
            Used to index self._queue_order, which is populated
            in the order of adding new queues.

            """
            self._next_queue = (self._next_queue + 1) % len(self._queue_order)
            return self._next_queue

        # retrieve the next job of each queue
        # (or None if there is no job in the queue)
        next_jobs = [self.queue(q).peek() for q in self._queue_order]
        # Determine the next job to be executed.
        # TODO: This is a naive approach:
        #       cycle through the queues
        #       and expect all queues to be served justly that way
        # We need to discuss whether queues can be prioritized
        # or whether/how the job's priorities can be respected
        # while still giving all queues a fair share.
        # E.g. respect priority but only everyt n-th turn ...
        for i in range(len(next_jobs)):
            next_queue = next_queue_index()
            if next_jobs[next_queue]:
                return self.queue(self._queue_order[next_queue]).pop()

    def idle_runner(self):
        """Return an idle runner from the shared pool,
        or None if no runner is idle."""
        if self._shared_runners:
            return self._shared_runners.pop()

    def load_settings(self):
        # TODO: Load settings and create the JobQueues accordingly
        pass

    def queue(self, name):
        """
        Return a JobQueue of the given name.
        Raises an exception if no such queue exists.
        """
        try:
            return self._queues[name]
        except:
            raise JobQueueNotFoundException(
                _(
                    "Requested non-present JobQueue '{name}' "
                    "from the global JobQueue."
                ).format(name=name)
            )

    def reclaim_shared_runner(self, runner):
        """Process a completed shared runner.

        If a shared runner has completed its job
        the global job queue tries to find a new job for it
        (from an arbitrary job queue).

        """
        self._shared_runners.append(runner)
        next_job = self.get_next_job()
        if next_job:
            self._shared_runners.pop()
            queue = next_job.queue()
            queue.add_shared_runner(runner)
            queue.start_job(runner, next_job)

    def settings_changed(self):
        """Called when the application settings have been changed.

        We can't handle a changed number of runners at runtime
        and have to require a restart in that case.

        """
        s = app.settings('multicore')
        new_cores = s.value('num-cores', app.default_cores(), int)
        if new_cores != self.available_cores():
            from widgets.restartmessage import suggest_restart
            suggest_restart(_(
                "The number of requested CPU cores has been changed. "
            ))
