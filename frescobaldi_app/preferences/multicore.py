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
Multicore support and job handling
"""


from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout
)

import app
import userguide
import preferences

from job import queue

class Multicore(preferences.ScrolledGroupsPage):
    def __init__(self, dialog):
        super(Multicore, self).__init__(dialog)

        layout = QVBoxLayout()
        self.scrolledWidget.setLayout(layout)

        layout.addWidget(Cores(self))
        layout.addWidget(Queues(self))
        layout.addStretch()


class Cores(preferences.Group):
    """Number of available CPU cores."""

    def __init__(self, page):
        super(Cores, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.coresLabel = QLabel()
        layout.addWidget(self.coresLabel)
        self.numCores = QSpinBox(valueChanged=self.changed)
        self.numCores.setRange(1, app.max_cores())

        box = QHBoxLayout()
        box.addWidget(self.numCores)
        box.addStretch()
        layout.addLayout(box)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Available CPU Cores/Threads"))
        self.coresLabel.setText(_(
                "The system reports {num} available cores or threads\n"
                "Maximum number of cores to be used by Frescobaldi:"
            ).format(num=app.max_cores(fallback=False) or '---')
        )
        self.coresLabel.setToolTip(_(
            "The system has determined that this\n"
            "is the number of threads or cores in\n"
            "the CPU that can run in parallel."
        ))

    def loadSettings(self):
        s = app.settings("multicore")
        self.numCores.setValue(app.available_cores())

    def saveSettings(self):
        s = app.settings("multicore")
        s.setValue('num-cores', self.numCores.value())


class Queues(preferences.Group):
    """Distribution of resources among job queues.
    Thoughts:
    - There is one global job queue which is assigned the requested number
      of runners (TODO: Will runners be instantiated by sub-queues or
      by the global queue and then assigned to a queue. The latter might
      reduce complications when changing anything at runtime)
    - The 'crawler' queue should always be separate with exactly one runner
      -- except when only two cores are available in total.
    - The 'generic' queue should generally be separate with exactly one runner.
      This will be assigned jobs separate from the regular engraving, such
      as import/exports or previews.
      - When few cores are available this might better be merged with the
        'engrave' queue.
      - The merging could be unconditional or in a way that actual runners
        are shared but that the 'generic' jobs are inserted with a higher
        priority than engraving jobs. That way the 'generic' job will not
        be started immediately but before the next engraving job gets started.
      - The question is: this should *not* be allowed to swallow more slots
        than assigned to the 'generic' queue. That is: If many engraving jobs
        are queued and two generic jobs are added the second should only be
        allowed to start after the first has completed.
    - It is not clear how arbitrary additional queues (as created by extensions)
      should be handled.
      Maybe there should be a set of predefined "sharing strategies", from which
      a queue has to choose one. Extensions should then choose an appropriate
      strategy based on the available number of cores. It should make both the
      strategy and the requested number of runners configurable, but it's
      important to provide reasonable defaults.
    - I *think* we should think of the 'engrave' queue as the center that is
      always there, with all the other queues opting in to share with that pool
      or requesting to take away from it.
      At some point (when the engrave queue is requested to give away its last
      runner) there will be an error message.

    [EDIT:]
    I think the best way to go is:
    - have a shared pool of (all) available runners
    - a new queue has a number of dedicated and a number of shared runners
    - when creating a queue dedicated runners are popped from the shared pool
    - in queue.available_slot (or so?) the queue will have to "know" whether
      it may or may not use a shared runner, based on the max number
    """

    def __init__(self, page):
        super(Queues, self).__init__(page)

        layout = QVBoxLayout()
        self.setLayout(layout)

        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_("Job Queues"))

    def loadSettings(self):
        s = app.settings("multicore")
        # To be continued

    def saveSettings(self):
        s = app.settings("multicore")
        # To be continued
