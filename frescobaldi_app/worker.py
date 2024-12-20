# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2024 by Benjamin Johnson
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
Simple API for creating worker objects.

Workers are used to run slow operations in a background thread.
To create one, subclass Worker and implement your logic in its
work() method. Upon successful completion, emit the resultReady
signal to pass the results back to your initial thread.

A worker is started by calling its start() class method with
some data and the slot to be executed upon successful completion.
There is a single instance of each worker type which is created
the first time start() is called. You can also access the worker
instance directly using its instance() class method, though it
normally should not be necessary to do so.

Because each worker type's one instance may have multiple users,
a worker should not store state in its instance attributes.

All workers live in the same thread, app.worker_thread(), which
persists until the application exits. This reduces overhead
compared to starting a new thread for each worker but does mean
that workers may block one another.

"""

from PyQt6.QtCore import Qt, QObject, pyqtSignal

import weakref

import app


_instances = weakref.WeakKeyDictionary()
_starters = weakref.WeakKeyDictionary()


class Worker(QObject):
    """Base class for worker objects.

    Subclass this and implement your logic in its work() method.

    Use the instance() class method to get/create a Worker instance.

    """
    def work(self, data):
        """Override this in your subclass to perform work.

        Emit the resultReady signal upon successful completion to
        pass the results back to the main thread.

        """
        pass

    @classmethod
    def instance(cls):
        """Returns the instance of this worker type.

        If it did not already exist, the worker is created, moved to
        the global worker thread, and scheduled for deletion when that
        thread exits.

        """
        try:
            worker = _instances[cls]
        except KeyError:
            worker = _instances[cls] = cls()
            worker.moveToThread(app.worker_thread())
            app.worker_thread().finished.connect(worker.deleteLater)
        return worker

    @classmethod
    def start(cls, data, onResultReady):
        """Starts performing work.

        The onResultReady argument is the slot that will be called
        when the resultReady signal is emitted.

        The worker is created if it did not already exist.

        """
        _Starter.instance(cls.instance()).start(data, onResultReady)

    def _start(self, data, onResultReady):
        try:
            # We can't rely on a single-shot connection because it would
            # still be connected next time if resultReady was not emitted.
            # This way ensures only one slot is connected at a time.
            self.resultReady.disconnect()
        except TypeError:
            pass    # no previous connection
        self.resultReady.connect(onResultReady,
                                 Qt.ConnectionType.QueuedConnection)
        self.work(data)

    # argument: result
    resultReady = pyqtSignal('PyQt_PyObject')


class _Starter(QObject):
    """The thing that signals a worker to start.

    To start a worker in another thread we have to use signals
    and slots. This class exists so we don't have to connect and
    emit those signals manually, which is especially handy in
    classes like plugin.Plugin that are not derived from QObject.

    Use the instance() class method to get/create the starter
    instance for a given worker.

    """
    def __init__(self, worker):
        super().__init__()
        self._started.connect(worker._start,
                              Qt.ConnectionType.QueuedConnection)

    def start(self, data, onResultReady):
        """Start the worker. See Worker.start()."""
        self._started.emit(data, onResultReady)

    @classmethod
    def instance(cls, worker):
        """Returns the starter instance for a worker.

        The starter is created if it did not exist.

        """
        try:
            starter = _starters[worker]
        except KeyError:
            starter = _starters[worker] = cls(worker)
        return starter

    # argument: data, onResultReady
    _started = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
