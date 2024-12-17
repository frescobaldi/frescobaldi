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

This API was primarily intended to offload repeated operations
like updating the music position that would cause lag if run in
the main thread. Some specific design features to be aware of:

  * There is a single instance of each worker type, which is
    accessed through its instance() class method.

  * All workers live in the same thread, app.worker_thread(),
    which persists until the application exits. This reduces
    overhead compared to starting a new thread for each worker.

  * A worker is started by calling its start() class method.
    Mixing the worker and controller roles like this is
    conceptually messy but allows for simpler code, especially
    when a worker is created in a class like plugin.Plugin
    that is not derived from QObject.

"""

from PyQt6.QtCore import Qt, QObject, pyqtSignal

import weakref

import app


_instances = weakref.WeakKeyDictionary()
_controllers = weakref.WeakKeyDictionary()


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
    def start(cls, data):
        """Starts performing work."""
        # The controller, which lives in the calling thread, signals
        # to the worker to start in its own thread.
        _Controller.instance(cls.instance()).start(data)

    # argument: result
    resultReady = pyqtSignal('PyQt_PyObject')


class _Controller(QObject):
    """Controller used to start a worker.

    Each worker has a single associated controller instance. The
    controller lives in the main thread and signals the worker when
    it's time to perform work in its own thread.

    Use the instance() class method to get/create the Controller
    instance for a given worker.

    """
    def __init__(self, worker):
        super().__init__()
        self._started.connect(worker.work,
                              Qt.ConnectionType.QueuedConnection)

    def start(self, data):
        """Start the worker."""
        self._started.emit(data)

    @classmethod
    def instance(cls, worker):
        """Returns the Controller instance for a worker.

        The controller is created if it did not exist.

        """
        try:
            controller = _controllers[worker]
        except KeyError:
            controller = _controllers[worker] = cls(worker)
        return controller

    # argument: data
    _started = pyqtSignal('PyQt_PyObject')
