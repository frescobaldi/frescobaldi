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
The Git menu.
Currently only list local branches, allowing one to switch to that branch.
"""


from PyQt5.QtWidgets import QAction, QActionGroup, QMenu, QMessageBox

import app
import mainwindow
import plugin
import vcs
from .gitrepo import GitError

class GitMenu(QMenu):
    def __init__(self, mainwindow):
        super(GitMenu, self).__init__(mainwindow)
        self.aboutToShow.connect(self.populate)
        app.translateUI(self)

    def translateUI(self):
        self.setTitle(_('menu title', '&Git'))

    def populate(self):
        self.clear()
        mainwindow = self.parentWidget()
        for a in GitBranchGroup.instance(mainwindow).actions():
            self.addAction(a)


class GitBranchGroup(plugin.MainWindowPlugin, QActionGroup):
    """
    Maintains a list of actions to switch the branch
    Frescobali is run from.

    The actions are added to the Git menu in order to be able
    to switch the branch Frescobaldi is run from.
    The actions also get accelerators that are kept
    during their lifetime.

    """
    def __init__(self, mainwindow):
        QActionGroup.__init__(self, mainwindow)
        self._acts = {}
        self._accels = {}
        self.setExclusive(True)
        for branch in vcs.app_repo.branches():
            self.addBranch(branch)
        self.triggered.connect(self.slotTriggered)

    def actions(self):
        """
        Returns a list with actions for each branch.
        If a branch has been externally created since
        the last run of this function a new action
        is added to self._acts.
        If a branch has been removed the action is kept,
        so if the branch is reintroduced later the action
        will have the same accelerator.
        """
        result = []
        for branch in vcs.app_repo.branches():
            if not branch in self._acts:
                self.addBranch(branch)
            result.append(self._acts[branch])
        return result

    def addBranch(self, branch):
        a = QAction(self)
        a.setCheckable(True)
        if branch == vcs.app_repo.current_branch():
            a.setChecked(True)
            a.setEnabled(False)
        self._acts[branch] = a
        self.setBranchStatus(branch)

    def setBranchStatus(self, branch):
        # create accels
        accels = [self._accels[b] for b in self._accels if b != branch]
        name = branch
        for index, char in enumerate(name):
            if char.isalnum() and char.lower() not in accels:
                name = name[:index] + '&' + name[index:]
                self._accels[branch] = char.lower()
                break
        else:
            self._accels[branch] = ''
        name = name + " ({0})".format(vcs.app_repo.tracked_remote_label(branch))
        self._acts[branch].setText(name)

    def slotTriggered(self, action):
        msgBox = QMessageBox()
        for branch, act in self._acts.items():
            if act == action:
                new_branch = branch
                break
        if not new_branch:
            return
        try:
            vcs.app_repo.checkout(new_branch)
            msgBox.setText(_("Checkout Successful"))
            msgBox.setInformativeText(_("Successfully checked out branch {name}.\n"
                "Changes will take effect after restart.\n"
                "Do you want to restart now?").format(name=new_branch))
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msgBox.exec_() == QMessageBox.Ok:
                self.parent().restart()
        except GitError as giterror:
            msgBox.setText(_("Git Checkout Error"))
            msgBox.setInformativeText(str(giterror))
            msgBox.exec_()
            action.setChecked(False)
            self._acts[vcs.app_repo.current_branch()].setChecked(True)
