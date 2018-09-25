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
Produce a number of examples for final use.
"""

import codecs
import os
import time

from PyQt5.QtCore import (
    QObject,
    QSettings,
    Qt,
    QTimer
)
from PyQt5.QtGui import (
    QStandardItem,
    QStandardItemModel
)
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListView,
    QSizePolicy,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget
)

import job
import lilypondinfo
import signals
import widgets.dialog

def create_examples(examples, widget):
    """Take a list of example names and produce all the relevant
    output files. 'widget' is the QTabWidget holding the
    example_widget and config_widget tabs. 'examples' is a string list."""
    dlg = ProcessDialog(examples, widget, parent=widget.mainwindow())
    dlg.exec_()


class ProcessDialog(widgets.dialog.Dialog):

    def __init__(self, examples, widget, parent=None):
        super(ProcessDialog, self).__init__(
            buttons=('ok',),
            title="Erzeuge Beispiel(e)",
            #message="Hey, das ist die Message"
            )

        self.widget = widget
        ac = widget.action_collection

        self.examples = examples
        self.queue = JobQueue(
            self, QSettings().value('mozart/num-runners', 1, int))

        layout = QGridLayout()
        self.mainWidget().setLayout(layout)

        self.toolbar = QToolBar(self)
        self.toolbar.addAction(ac.mozart_process_abort)
        self.toolbar.addAction(ac.mozart_process_pause)
        self.toolbar.addAction(ac.mozart_process_resume)
        ac.mozart_process_resume.setEnabled(False)

        self.activities_view = ActivitiesView(self)
        self.results_view = ResultsView(examples, self)
        self.queue.create_job_configs(self.results_view.model())
        self.queue.start_processing()
        self.queue.finished.connect(self.slot_queue_finished)

        layout.addWidget(self.toolbar, 0, 0, 1, 2)
        layout.addWidget(self.activities_view, 1, 0, 1, 1)
        layout.addWidget(self.results_view, 1, 1, 1, 1)

    def slot_queue_finished(self):
        pass

class ActivitiesView(QTableView):
    """Fortschrittsanzeige der verschiedenen Runner."""
    def __init__(self, parent=None):
        super(ActivitiesView, self).__init__(parent)
        num_runners = QSettings().value('mozart/num-runners', 1, int)
        self.setModel(QStandardItemModel())
        self.setFixedWidth(230)
        self.model().setHorizontalHeaderLabels(
        ['Beispiel', 'Typ'])
        self.initialize(num_runners)
        self.model().setVerticalHeaderLabels(
            [str(i + 1) for i in range(num_runners)]
        )
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)


    def initialize(self, num_runners):
        """Erzeuge die initialen QStandardItems."""
        root = self.model().invisibleRootItem()
        for i in range(num_runners):
            root.appendRow([QStandardItem('--'), QStandardItem('--')])

    def stop_runner(self, runner):
        self.update_runner(runner, '--', '--')

    def update_runner(self, runner, example, type):
        """Zeige Beispiel und Typ in einem Runner an."""
        parent = self.model().invisibleRootItem()
        parent.child(runner, 0).setText(example)
        parent.child(runner, 1).setText(type)


class ResultsView(QTableView):
    """Stellt die Ergebnisse in einer Tabelle dar und
    hält sie in einem Datenmodell vor."""

    def __init__(self, examples, parent=None):
        super(ResultsView, self).__init__(parent)
        self.examples = examples
        self.types = ['PDF', 'PNG', 'SVG']
        self.setModel(QStandardItemModel())
        self.model().setHorizontalHeaderLabels(self.types)
        for col in range(len(self.types)):
            self.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeToContents)

        root = self.model().invisibleRootItem()
        for example in examples:
            items = []
            for type in self.types:
                items.append(QStandardItem())
                items[-1].setCheckable(False)
                items[-1].setCheckState(Qt.Unchecked)
            root.appendRow(items)
        self.model().setVerticalHeaderLabels(examples)


class JobConfiguration(QObject):
    """Konfigurationsobjekt für einen LilyPond-Job.
    (Kann noch erweitert werden)."""
    def __init__(self, example, type):
        super(JobConfiguration, self).__init__()
        self.example = example
        self.type = type

    def __repr__(self):
        return '{} - {}'.format(self.example, self.type)


class Runner(QObject):
    """Koordiniert einen einzelnen LilyPond-Job, holt sich die
    Jobkonfiguration von der JobQueue."""

    def __init__(self, queue):
        super(Runner, self).__init__()
        self.queue = queue
        self.job = None

        # Funktionen, die den LilyPond-Befehl entsprechend des Target-Typs
        # vervollständigen.
        self._command_funcs = {
            'PDF': self._pdf_command,
            'PNG': self._png_command,
            'SVG': self._svg_command
        }
        # Funktionen, die entsprechend des Target-Typs nach der Kompilierung
        # aufräumen.
        self._cleanup_funcs = {
            'PDF': self._cleanup_pdf,
            'PNG': self._cleanup_png,
            'SVG': self._cleanup_svg
        }

    def _export_files(self):
        """Gibt eine Liste von Dateien im Exportverzeichnis zurück,
        die von der Kompilierung erzeugt wurden."""
        example = self.job_config.example
        type_base = '{}-{}'.format(example, self.job_config.type)
        files = os.listdir(self.export_directory)
        return [file for file in files if file.startswith(type_base)]

    # TODO: Es könnte sein, dass man diese Cleanup-Dateien besser
    # vereinheitlichen könnte. Das hängt aber davon ab, welche Typen
    # noch erforderlich werden.
    def _cleanup_png(self):
        for file in self._export_files():
            file_name = os.path.join(self.export_directory, file)
            if not file.endswith('cropped.png'):
                os.remove(file_name)
            else:
                os.rename(file_name,
                    os.path.join(self.export_directory, '{}.png'.format(
                        self.job_config.example)))

    def _cleanup_pdf(self):
        for file in self._export_files():
            file_name = os.path.join(self.export_directory, file)
            if not file.endswith('cropped.pdf'):
                os.remove(file_name)
            else:
                os.rename(file_name,
                    os.path.join(self.export_directory, '{}.pdf'.format(
                        self.job_config.example)))

    def _cleanup_svg(self):
        for file in self._export_files():
            file_name = os.path.join(self.export_directory, file)
            if not file.endswith('cropped.svg'):
                os.remove(file_name)
            else:
                os.rename(file_name,
                    os.path.join(self.export_directory, '{}.svg'.format(
                        self.job_config.example)))

    def _png_command(self):
        return ['-dcrop', '--png', '-dresolution=300']

    def _pdf_command(self):
        return ['-dcrop']

    def _svg_command(self):
        return ['-dcrop', '-dbackend=svg']

    def command(self, job_config):
        """Erzeuge den LilyPond-Befehl für das aktuelle Beispiel,
        entsprechend dem Target-Typ."""
        info = self.queue.lilypond_info
        command = [
            info.abscommand() or info.command,
            '-ddelete-intermediate-files',
            '-I', self.project_root,
            '-I', self.openLilyLib_root,
            '-o', os.path.join(self.export_directory,
                '{}-{}'.format(job_config.example, job_config.type))]
        command.extend(self._command_funcs[job_config.type]())
        command.append(os.path.join(
            self.project_root, '{}.ly'.format(job_config.example)))
        return command

    def slot_job_done(self):
        """Wird aufgerufen, nachdem der Job erledigt ist.
        Erzeugt ein results-Dictionary aus dem Job,
        führt die entsprechenden Cleanup-Funktionen aus,
        benachrichtit die Queue,
        startet den nächsten Job."""
        j = self.job
        self.results = {
            'success': j.success,
            'error': j.error,
            'history': j.history()
        }
        self._cleanup_funcs[self.job_config.type]()
        self.queue.job_done(self)
        self.start()

    def start_job(self):
        """Startet einen LiyPond-Job."""
        j = self.job
        j.done.connect(self.slot_job_done)
        self.queue.job_started(self, job_config)
        j.start()

    def start(self):
        """Holt einen neuen Job und startet diesen.
        Wenn keine Jobs mehr in der Queue sind, melde mich ab."""
        self.job = self.queue.pop()
        if self.job:
            self.start_job()
        elif self.queue.state in [JobQueue.EMPTY, JobQueue.FINISHED]:
            self.queue.remove_runner(self)
        else:
            # in Pause
            pass


class JobQueue(QObject):
    """MultiThreaded Job Queue."""

    finished = signals.Signal()
    INACTIVE = 0
    STARTED = 1
    PAUSED = 2
    EMPTY = 3
    FINISHED = 4

    def __init__(self, count):
        super(JobQueue, self).__init__()
        self.state = JobQueue.INACTIVE
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.jobs = []
        self._runners = [Runner(self) for i in range(count)]

    def abort(self, force=True):
        """Abort the execution of the queued jobs.
        If force=True running jobs are aborted, otherwise
        only the queue is cleared, allowing running jobs to finish."""
        self.state = JobQueue.FINISHED
        self.jobs = []
        if force:
            for runner in self._runners:
                runner.job.abort()

    def job_done(self, runner):
        """Verarbeite die Ergebnisse eines geleisteten Jobs."""
        self._jobs_done += 1
        job_config = runner.job_config
        results = runner.results
        runner_index = self._runners.index(runner)
        self.dialog().activities_view.stop_runner(runner_index)

        example_index = self.dialog().examples.index(job_config.example)
        column = self.dialog().results_view.types.index(job_config.type)
        check_box = self._model.invisibleRootItem().child(example_index, column)
        if results['success']:
            check_box.setCheckState(2)
        else:
            check_box.setCheckState(1)
            log = [line[0] for line in results['history']]
            for line in log:
                print(line)
            #TODO: log speichern und im GUI zugänglich machen.
            #TODO: Von hier aus in Editor öffnen

    def job_started(self, runner, job_config):
        """Aktualisiere die Anzeige des laufenden Jobs."""
        self.dialog().activities_view.update_runner(
            self._runners.index(runner),
            job_config.example,
            job_config.type)

    def pause(self):
        self.state = JobQueue.PAUSED
        self.action_collection.mozart_process_pause.setEnabled(False)
        self.action_collection.mozart_process_resume.setEnabled(True)
        self.timer.stop()

    def pop(self):
        """Gebe einen Job heraus, sofern noch welche vorhanden sind."""
        if not self.job_configs or self.state != JobQueue.STARTED:
            return False
        new_jobconfig = self.job_configs.pop()
        if not self.job_configs:
            self.state = JobQueue.EMPTY
        return new_jobconfig

    def remove_runner(self, runner):
        """Setze einen Runner auf None, wenn er keine Jobs mehr hat.
        Wenn alle Runner None sind, ist der Prozess fertig."""
        self._runners[self._runners.index(runner)] = None
        for runner in self._runners:
            if runner:
                return
        self.timer.stop()
        self.finished.emit()

    def resume(self):
        if not self.state in [JobQueue.EMPTY, JobQueue.FINISHED]:
            self.action_collection.mozart_process_resume.setEnabled(False)
            self.action_collection.mozart_process_pause.setEnabled(True)
            self._start()


    def _start(self):
        self.state = JobQueue.STARTED
        self.timer.start(1000)
        for runner in self._runners:
            runner.start()

    def start_processing(self):
        """Beginne den Prozess, setze die Metadaten, starte den Timer
        (für die Status-Anzeige). Bitte alle Runner, die Bearbeitung zu
        starten."""
        self._starttime = time.time()
        self._job_count = len(self.job_configs)
        self._jobs_done = 0
        self._start()
