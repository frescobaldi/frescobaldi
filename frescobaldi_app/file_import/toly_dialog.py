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
Generic import dialog. Presuppose a child instance for the specific import.
"""


import os

from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
    QGridLayout, QLabel, QTabWidget, QTextEdit, QWidget)

import lilychooser
import userguide
import util
import widgets
import job


class ToLyDialog(QDialog):
    """Dialog base class for all file import jobs.

    Basically the whole dialog is identical for all file types, the only
    part of the dialog that is specific is the widget with *input* options.
    These are created in a subclass's __init__ function and added to the
    self.impChecks list. Only then super() is called.
    """

    def __init__(self,
                 parent=None,
                 job_class=job.Job,
                 imp_prgm='',
                 input=None,
                 userg=''):
        super(ToLyDialog, self).__init__(parent)
        self._info = None
        self._imp_prgm = imp_prgm
        self._userg = userg
        self._input = input
        self._path = None
        self._job_class = job_class
        self._job = None

        self.addAction(parent.actionCollection.help_whatsthis)
        self.setWindowModality(Qt.WindowModal)
        mainLayout = QGridLayout()
        self.setLayout(mainLayout)

        tabs = QTabWidget()

        import_tab = QWidget()
        post_tab = QWidget()

        itabLayout = QGridLayout(import_tab)
        ptabLayout = QGridLayout(post_tab)

        tabs.addTab(import_tab, self._imp_prgm)
        tabs.addTab(post_tab, _("After Import"))

        self.formatCheck = QCheckBox()
        self.trimDurCheck = QCheckBox()
        self.removeScalesCheck = QCheckBox()
        self.runEngraverCheck = QCheckBox()

        self.postChecks = [self.formatCheck,
                           self.trimDurCheck,
                           self.removeScalesCheck,
                           self.runEngraverCheck]

        self.versionLabel = QLabel()
        self.lilyChooser = lilychooser.LilyChooser()

        self.formatCheck.setObjectName("reformat")
        self.trimDurCheck.setObjectName("trim-durations")
        self.removeScalesCheck.setObjectName("remove-scaling")
        self.runEngraverCheck.setObjectName("engrave-directly")

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        userguide.addButton(self.buttons, self._userg)

        row = 0
        for r, w in enumerate(self.impChecks):
            row += r
            itabLayout.addWidget(w, row, 0, 1, 2)
        row += 1
        for r, w in enumerate(self.impExtra):
            row += r
            itabLayout.addWidget(w, row, 0, 1, 2)

        itabLayout.addWidget(widgets.Separator(), row + 1, 0, 1, 2)
        itabLayout.addWidget(self.versionLabel, row + 2, 0, 1, 0)
        itabLayout.addWidget(self.lilyChooser, row + 3, 0, 1, 2)
        itabLayout.setRowStretch(row + 4, 10)

        ptabLayout.addWidget(self.formatCheck, 0, 0, 1, 2)
        ptabLayout.addWidget(self.trimDurCheck, 1, 0, 1, 2)
        ptabLayout.addWidget(self.removeScalesCheck, 2, 0, 1, 2)
        ptabLayout.addWidget(self.runEngraverCheck, 3, 0, 1, 2)
        ptabLayout.setRowStretch(4, 6)

        mainLayout.addWidget(tabs, 0, 0, 6, 2)
        mainLayout.addWidget(self.buttons, 7, 0, 1, 2)

        self.buttons.accepted.connect(self.about_to_accept)
        self.buttons.rejected.connect(self.reject)

        self.lilyChooser.currentIndexChanged.connect(self.slot_lilypond_version_changed)
        self.slot_lilypond_version_changed()

    def translateUI(self):
        self.versionLabel.setText(_("LilyPond version:"))
        self.formatCheck.setText(_("Reformat source"))
        self.trimDurCheck.setText(_("Trim durations (Make implicit per line)"))
        self.removeScalesCheck.setText(_("Remove fraction duration scaling"))
        self.runEngraverCheck.setText(_("Engrave directly"))

    def about_to_accept(self):
        """Configure the job and close the dialog."""
        self.configure_job()
        self.accept()

    def configure_job(self):
        """Create and configure the job to be run.
        Has to be completed by the subclasses."""
        output = os.path.splitext(
            os.path.join(util.tempdir(), os.path.basename(self._input))
            )[0] + '.ly'
        self._job = j = self._job_class(
            command=self._info.toolcommand(self._imp_prgm),
            input=self._input,
            output='--output={}'.format(output),
            directory=os.path.dirname(self._input),
            encoding='utf-8')
        j._output_file = output

    def get_post_settings(self):
        """Returns settings in the post import tab."""
        post = []
        for p in self.postChecks:
            post.append(p.isChecked())
        return post

    def job(self):
        """Return the current job."""
        if not self._job:
            self.configure_job()
        return self._job

    def set_input(self, path):
        """Set the full path to the input document."""
        self._input = path

    def slot_lilypond_version_changed(self):
        self._info = self.lilyChooser.lilyPondInfo()

    def loadSettings(self):
        """Get users previous settings."""
        post_default = [True, False, False, True]
        for i, d in zip(self.impChecks, self.imp_default):
            i.setChecked(self.settings.value(i.objectName(), d, bool))
        for p, f in zip(self.postChecks, post_default):
            p.setChecked(self.settings.value(p.objectName(), f, bool))

    def saveSettings(self):
        """Save users last settings."""
        for i in self.impChecks:
            self.settings.setValue(i.objectName(), i.isChecked())
        for p in self.postChecks:
            self.settings.setValue(p.objectName(), p.isChecked())
