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
Custom engraving dialog.
"""


import os
import collections

from PyQt5.QtCore import QSettings, QSize, Qt
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QSpinBox, QTextEdit)

import app
import documentinfo
import userguide
import icons
import job
import jobmanager
import jobattributes
import panelmanager
import lilychooser
import listmodel
import widgets
import qutil
import util

from . import command


class Dialog(QDialog):
    def __init__(self, mainwindow):
        super(Dialog, self).__init__(mainwindow)
        self._document = None

        layout = QGridLayout()
        self.setLayout(layout)

        self.versionLabel = QLabel()
        self.lilyChooser = lilychooser.LilyChooser()

        self.outputLabel = QLabel()
        self.outputCombo = QComboBox()

        self.resolutionLabel = QLabel()
        self.resolutionCombo = QComboBox(editable=True)

        self.antialiasLabel = QLabel()
        self.antialiasSpin = QSpinBox(minimum=1, maximum=128, value=1)

        self.modeLabel = QLabel()
        self.modeCombo = QComboBox()

        self.deleteCheck = QCheckBox()
        self.embedSourceCodeCheck = QCheckBox()
        self.englishCheck = QCheckBox()

        self.commandLineLabel = QLabel()
        self.commandLine = QTextEdit(acceptRichText=False)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setIcon(icons.get("lilypond-run"))
        userguide.addButton(self.buttons, "engrave_custom")

        self.resolutionCombo.addItems(['100', '200', '300', '600', '1200'])
        self.resolutionCombo.setCurrentIndex(2)

        self.modeCombo.addItems(['preview', 'publish', 'debug', 'incipit'])
        layout.addWidget(self.versionLabel, 0, 0)
        layout.addWidget(self.lilyChooser, 0, 1, 1, 3)
        layout.addWidget(self.outputLabel, 1, 0)
        layout.addWidget(self.outputCombo, 1, 1, 1, 3)
        layout.addWidget(self.resolutionLabel, 2, 0)
        layout.addWidget(self.resolutionCombo, 2, 1)
        layout.addWidget(self.antialiasLabel, 2, 2, Qt.AlignRight)
        layout.addWidget(self.antialiasSpin, 2, 3)
        layout.addWidget(self.modeLabel, 3, 0)
        layout.addWidget(self.modeCombo, 3, 1, 1, 3)
        layout.addWidget(self.deleteCheck, 4, 0, 1, 4)
        layout.addWidget(self.embedSourceCodeCheck, 5, 0, 1, 4)
        layout.addWidget(self.englishCheck, 6, 0, 1, 4)
        layout.addWidget(self.commandLineLabel, 7, 0, 1, 4)
        layout.addWidget(self.commandLine, 8, 0, 1, 4)
        layout.addWidget(widgets.Separator(), 9, 0, 1, 4)
        layout.addWidget(self.buttons, 10, 0, 1, 4)

        app.translateUI(self)
        qutil.saveDialogSize(self, "engrave/custom/dialog/size", QSize(480, 260))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        model = listmodel.ListModel(formats, display=lambda f: f.title(),
            icon=lambda f: icons.file_type(f.type))
        self.outputCombo.setModel(model)

        s = QSettings()
        s.beginGroup("lilypond_settings")
        self.englishCheck.setChecked(
            s.value("no_translation", False, bool))
        self.deleteCheck.setChecked(
            s.value("delete_intermediate_files", True, bool))

        if s.value("default_output_target", "pdf", str) == "svg":
            self.outputCombo.setCurrentIndex(3)

        app.jobFinished.connect(self.slotJobFinished)
        self.outputCombo.currentIndexChanged.connect(self.makeCommandLine)
        self.modeCombo.currentIndexChanged.connect(self.makeCommandLine)
        self.deleteCheck.toggled.connect(self.makeCommandLine)
        self.embedSourceCodeCheck.toggled.connect(self.makeCommandLine)
        self.resolutionCombo.editTextChanged.connect(self.makeCommandLine)
        self.antialiasSpin.valueChanged.connect(self.makeCommandLine)
        self.makeCommandLine()
        panelmanager.manager(mainwindow).layoutcontrol.widget().optionsChanged.connect(self.makeCommandLine)

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Engrave custom")))
        self.versionLabel.setText(_("LilyPond Version:"))
        self.outputLabel.setText(_("Output Format:"))
        self.resolutionLabel.setText(_("Resolution:"))
        self.antialiasLabel.setText(_("Antialias Factor:"))
        self.modeLabel.setText(_("Engraving mode:"))
        self.modeCombo.setItemText(0, _("Preview"))
        self.modeCombo.setItemText(1, _("Publish"))
        self.modeCombo.setItemText(2, _("First System Only"))
        self.modeCombo.setItemText(3, _("Layout Control"))
        self.deleteCheck.setText(_("Delete intermediate output files"))
        self.embedSourceCodeCheck.setText(_("Embed Source Code (LilyPond >= 2.19.39)"))
        self.englishCheck.setText(_("Run LilyPond with English messages"))
        self.commandLineLabel.setText(_("Command line:"))
        self.buttons.button(QDialogButtonBox.Ok).setText(_("Run LilyPond"))
        self.outputCombo.update()

    def slotJobFinished(self, doc):
        if doc == self._document:
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
            self._document = None

    def setDocument(self, doc):
        self.lilyChooser.setLilyPondInfo(command.info(doc))
        job = jobmanager.job(doc)
        if job and job.is_running() and not jobattributes.get(job).hidden:
            self._document = doc
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def makeCommandLine(self):
        """Reads the widgets and builds a command line."""
        f = formats[self.outputCombo.currentIndex()]
        self.resolutionCombo.setEnabled('resolution' in f.widgets)
        self.antialiasSpin.setEnabled('antialias' in f.widgets)
        cmd = ["$lilypond"]

        if self.modeCombo.currentIndex() == 0:   # preview mode
            cmd.append('-dpoint-and-click')
        elif self.modeCombo.currentIndex() == 1: # publish mode
            cmd.append('-dno-point-and-click')
        elif self.modeCombo.currentIndex() == 2: # incipit mode
            cmd.extend(['-dpreview', '-dno-print-pages'])
        else:                                    # debug mode
            args = panelmanager.manager(self.parent()).layoutcontrol.widget().preview_options()
            cmd.extend(args)

        if self.deleteCheck.isChecked():
            cmd.append('-ddelete-intermediate-files')
        else:
            cmd.append('-dno-delete-intermediate-files')

        if self.embedSourceCodeCheck.isChecked():
            cmd.append('-dembed-source-code')

        d = {
            'version': self.lilyChooser.lilyPondInfo().version,
            'resolution': self.resolutionCombo.currentText(),
            'antialias': self.antialiasSpin.value(),
        }
        cmd.append("$include")
        cmd.extend(f.options(d))
        cmd.append("$filename")
        self.commandLine.setText(' '.join(cmd))

    def getJob(self, document):
        """Returns a Job to start."""
        filename, includepath = documentinfo.info(document).jobinfo(True)
        i = self.lilyChooser.lilyPondInfo()
        cmd = []
        for t in self.commandLine.toPlainText().split():
            if t == '$lilypond':
                cmd.append(i.abscommand() or i.command)
            elif t == '$filename':
                cmd.append(filename)
            elif t == '$include':
                cmd.extend('-I' + path for path in includepath)
            else:
                cmd.append(t)
        j = job.Job()
        j.directory = os.path.dirname(filename)
        j.command = cmd
        j.environment['LD_LIBRARY_PATH'] = i.libdir()
        if self.englishCheck.isChecked():
            j.environment['LANG'] = 'C'
            j.environment['LC_ALL'] = 'C'
        j.set_title("{0} {1} [{2}]".format(
            os.path.basename(i.command), i.versionString(), document.documentName()))
        return j

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Return and ev.modifiers() == Qt.ControlModifier:
            self.accept()
        else:
            super(Dialog, self).keyPressEvent(ev)


Format = collections.namedtuple("Format", "type title options widgets")

formats = [
    Format(
        "pdf",
        lambda: _("PDF"),
        lambda d: ['--pdf'],
        (),
    ),
    Format(
        "ps",
        lambda: _("PostScript"),
        lambda d: ['--ps'],
        (),
    ),
    Format(
        "png",
        lambda: _("PNG"),
        lambda d: [
            '--png',
            '-dresolution={resolution}'.format(**d),
            '-danti-alias-factor={antialias}'.format(**d),
        ],
        ('resolution', 'antialias'),
    ),
    Format(
        "svg",
        lambda: _("SVG"),
        lambda d: ['-dbackend=svg'],
        (),
    ),
    Format(
        "pdf",
        lambda: _("PDF (EPS Backend)"),
        lambda d: ['--pdf', '-dbackend=eps'],
        (),
    ),
    Format(
        "eps",
        lambda: _("Encapsulated PostScript (EPS Backend)"),
        lambda d: ['--ps', '-dbackend=eps'],
        (),
    ),
    Format(
        "png",
        lambda: _("PNG (EPS Backend)"),
        lambda d: [
            '--png',
            '-dbackend=eps',
            '-dresolution={resolution}'.format(**d),
            '-danti-alias-factor={antialias}'.format(**d),
        ],
        ('resolution', 'antialias'),
    ),
]


