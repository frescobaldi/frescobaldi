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
Git Repository of the Frescobaldi application.
Also manages a live list of repository branches for use in the Versioning menu.
"""


from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QMenu,
    QMessageBox
)

import app
import icons
from . import gitrepo

class Repo(gitrepo.Repo):
    """
    Subclass to be used for the Frescobaldi Versioning repository.
    Offers methods exclusively useful for this specific repo.
    """
    def __init__(self, root):
        super(Repo, self).__init__(root)
        self._activeBranch = self.current_branch()
        self._mainwindow = app.activeWindow()
        self._branch_actions = BranchActions(self)
        self._branch_menu = m = QMenu(self._mainwindow)
        m.aboutToShow.connect(self._populate_branch_menu)
        m.setIcon(icons.get('frescobaldi'))
        app.translateUI(self)
        
    def translateUI(self):
        self._branch_menu.setTitle(_('menu title', '&Frescobaldi Branches'))

    def _populate_branch_menu(self):
        """
        Populates the "Frescobaldi Branches" submenu with a live list of
        branches in the Frescobaldi repository. Current branch is highlighted
        while the other actions trigger switching the branch.
        """
        m = self._branch_menu
        m.clear()
        for a in self._branch_actions.actions():
            m.addAction(a)

    def active_branch(self):
        """
        Returns the name of the branch that was current_branch
        when the application has started.
        current_branch() may of course change during the
        runtime of the application
        """
        return self._activeBranch

    def branch_menu(self):
        return self._branch_menu
    
    def mainwindow(self):
        return self._mainwindow


class BranchActions(QActionGroup):
    """
    Maintains a list of actions to switch the branch
    Frescobali is run from.

    The actions are added to the Git menu in order to be able
    to switch the branch Frescobaldi is run from.
    The actions also get accelerators that are kept
    during the application's lifetime.

    """
    def __init__(self, app_repo):
        QActionGroup.__init__(self, app_repo.mainwindow())
        self._repo = app_repo
        self._acts = {}
        self._accels = {}
        self.setExclusive(True)
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
        for branch in self._repo.branches():
            if not branch in self._acts:
                self.addBranch(branch)
            result.append(self._acts[branch])
        return result

    def addBranch(self, branch):
        a = QAction(self)
        a.setCheckable(True)
        if branch == self._repo.current_branch():
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
        name = name + " ({0})".format(self._repo.tracked_remote_label(branch))
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
            self._repo.checkout(new_branch)
            msgBox.setText(_("Checkout Successful"))
            msgBox.setInformativeText(_("Successfully checked out branch {name}.\n"
                "Changes will take effect after restart.\n"
                "Do you want to restart now?").format(name=new_branch))
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msgBox.exec_() == QMessageBox.Ok:
                self.parent().restart()
        except gitrepo.GitError as giterror:
            msgBox.setText(_("Git Checkout Error"))
            msgBox.setInformativeText(str(giterror))
            msgBox.exec_()
            action.setChecked(False)
            self._acts[vcs.App.repo.current_branch()].setChecked(True)
