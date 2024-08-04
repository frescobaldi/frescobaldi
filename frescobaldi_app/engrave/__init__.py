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
Actions to engrave the music in the documents.
"""


import os

from PyQt6.QtCore import QSettings, Qt, QUrl
from PyQt6.QtGui import QAction, QKeySequence, QTextCursor
from PyQt6.QtWidgets import QApplication, QMessageBox

import app
import actioncollection
import actioncollectionmanager
import documentinfo
import job.attributes
import job.lilypond
import plugin
import icons
import reformat
import signals
import panelmanager
import variables


def engraver(mainwindow):
    return Engraver.instance(mainwindow)


class Engraver(plugin.MainWindowPlugin):

    stickyChanged = signals.Signal()    # Document

    def __init__(self, mainwindow):
        self._currentStickyDocument = None
        ac = self.actionCollection = Actions()
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.engrave_sticky.triggered.connect(self.stickyToggled)
        ac.engrave_runner.triggered.connect(self.engraveRunner)
        ac.engrave_preview.triggered.connect(self.engravePreview)
        ac.engrave_publish.triggered.connect(self.engravePublish)
        ac.engrave_debug.triggered.connect(self.engraveLayoutControl)
        ac.engrave_custom.triggered.connect(self.engraveCustom)
        ac.engrave_abort.triggered.connect(self.engraveAbort)
        ac.engrave_autocompile.toggled.connect(self.engraveAutoCompileToggled)
        ac.engrave_open_lilypond_datadir.triggered.connect(self.openLilyPondDatadir)
        mainwindow.currentDocumentChanged.connect(self.updateActions)
        app.jobStarted.connect(self.updateActions)
        app.jobFinished.connect(self.updateActions)
        app.jobFinished.connect(self.checkLilyPondInstalled)
        app.jobFinished.connect(self.openDefaultView)
        app.sessionChanged.connect(self.slotSessionChanged)
        app.saveSessionData.connect(self.slotSaveSessionData)
        app.documentClosed.connect(self.slotDocumentClosed)
        mainwindow.aboutToClose.connect(self.saveSettings)
        self.loadSettings()
        app.languageChanged.connect(self.updateStickyActionText)
        self.updateStickyActionText()

    def document(self):
        """Return the Document that should be engraved."""
        doc = self.stickyDocument()
        if not doc:
            doc = self.mainwindow().currentDocument()
            if doc and not doc.url().isEmpty():
                master = variables.get(doc, "master")
                if master:
                    url = doc.url().resolved(QUrl(master))
                    try:
                        doc = app.openUrl(url)
                    except OSError:
                        pass
        return doc

    def runningJob(self):
        """Returns a Job for the sticky or current document if that is running."""
        doc = self.document()
        j = job.manager.job(doc)
        if j and j.is_running() and not job.attributes.get(j).hidden:
            return j

    def updateActions(self):
        j = job.manager.job(self.document())
        running = bool(j and j.is_running())
        visible = running and not job.attributes.get(j).hidden
        ac = self.actionCollection
        ac.engrave_preview.setEnabled(not visible)
        ac.engrave_publish.setEnabled(not visible)
        ac.engrave_debug.setEnabled(not visible)
        ac.engrave_abort.setEnabled(running)
        ac.engrave_runner.setIcon(icons.get('process-stop' if visible else 'lilypond-run'))
        ac.engrave_runner.setToolTip(_("Abort engraving job") if visible else
                    _("Engrave (preview; press Shift for custom)"))

    def openDefaultView(self, document, j, success):
        """Called when a job finishes.

        Open the default viewer for the created files if the user has the
        preference for this set.

        """
        if (success and job.attributes.get(j).mainwindow is self.mainwindow()
                and QSettings().value("lilypond_settings/open_default_view", True, bool)):

            # which files were created by this job?
            import resultfiles
            extensions = {os.path.splitext(filename)[1].lower()
                for filename in resultfiles.results(document).files_lastjob()}

            mgr = panelmanager.manager(self.mainwindow())
            if '.svg' in extensions or '.svgz' in extensions:
                mgr.svgview.activate()
            elif '.pdf' in extensions:
                mgr.musicview.activate()

    def engraveRunner(self):
        j = self.runningJob()
        if j:
            j.abort()
        elif QApplication.keyboardModifiers() & Qt.Modifier.SHIFT:
            self.engraveCustom()
        else:
            self.engravePreview()

    def engravePreview(self):
        """Starts an engrave job in preview mode (with point and click turned on)."""
        self.engrave('preview')

    def engravePublish(self):
        """Starts an engrave job in publish mode (with point and click turned off)."""
        self.engrave('publish')

    def engraveLayoutControl(self):
        """Starts an engrave job in debug mode (using the settings in the debug tool)."""
        self.engrave('layout-control')

    def engraveCustom(self):
        """Opens a dialog to configure the job before starting it."""
        try:
            dlg = self._customDialog
        except AttributeError:
            from . import custom
            dlg = self._customDialog = custom.Dialog(self.mainwindow())
            dlg.addAction(self.mainwindow().actionCollection.help_whatsthis)
            dlg.setWindowModality(Qt.WindowType.WindowModal)
        doc = self.document()
        dlg.setDocument(doc)
        if dlg.exec_():
            self.saveDocumentIfDesired()
            self.runJob(dlg.getJob(doc), doc)

    def engrave(self, mode='preview', document=None, may_save=True):
        """Starts an engraving job.

        The mode can be 'preview', 'publish', or 'layout-control'. The last
        one uses the settings in the Layout Control Options panel. The
        default mode is 'preview'.

        If document is not specified, it is either the sticky or current
        document.

        If may_save is False, the document will not be saved before running
        LilyPond, even if the preference setting "save document before LilyPond
        is run" is enabled.

        """
        job_class = (
            job.lilypond.PreviewJob if mode == 'preview'
            else job.lilypond.PublishJob if mode == 'publish'
            else job.lilypond.LayoutControlJob
        )
        # TODO: Try to move this argument creation into
        # LayoutControlJob's constructor. However, somehow this has to
        # obtain access to the mainwindow.
        args = (
            panelmanager.manager(
                self.mainwindow()).layoutcontrol.widget().preview_options()
            if mode == 'layout-control' else None)
        doc = document or self.document()
        if may_save:
            self.saveDocumentIfDesired()
        self.runJob(job_class(doc, args), doc)

    def engraveAbort(self):
        j = job.manager.job(self.document())
        if j and j.is_running():
            j.abort()

    def saveDocumentIfDesired(self):
        """Saves the current document if desired and it makes sense.

        (i.e. the document is modified and has a local filename)

        """
        s = QSettings()
        if s.value("lilypond_settings/save_on_run", False, bool):
            doc = self.mainwindow().currentDocument()
            if doc.isModified() and doc.url().toLocalFile():
                try:
                    if s.value("strip_trailing_whitespace", False, bool):
                        reformat.remove_trailing_whitespace(QTextCursor(doc))
                    if s.value("format", False, bool):
                        reformat.reformat(QTextCursor(doc))
                    doc.save()
                except OSError:
                    pass ## saving was not possible (e.g. happens when read only)

    def queryCloseDocument(self, doc):
        """Return True whether a document can be closed.

        When no job is running, True is immediately returned.
        When a job is running, the user is asked whether to abort the job (not
        for autocompile ("hidden") jobs).

        """
        j = job.manager.job(doc)
        if not j or not j.is_running() or job.attributes.get(j).hidden:
            return True
        msgbox = QMessageBox(QMessageBox.Icon.Warning,
            _("Warning"),
            _("An engrave job is running for the document \"{name}\".\n"
              "Do you want to abort the running job?").format(name=doc.documentName()),
            QMessageBox.StandardButton.Abort | QMessageBox.StandardButton.Cancel,
            self.mainwindow())
        abort_button = msgbox.button(QMessageBox.StandardButton.Abort)
        signal = lambda: abort_button.click()
        j.done.connect(signal)
        msgbox.exec_()
        j.done.disconnect(signal)
        return msgbox.clickedButton() == abort_button

    def runJob(self, j, document):
        """Runs the engraving job on behalf of document."""
        job.attributes.get(j).mainwindow = self.mainwindow()
        # cancel running job, that would be an autocompile job
        rjob = job.manager.job(document)
        if rjob and rjob.is_running():
            rjob.abort()
        job.manager.manager(document).start_job(j)

    def stickyToggled(self):
        """Called when the user toggles the 'Sticky' action."""
        self.setStickyDocument(None if self.stickyDocument() else self.mainwindow().currentDocument())

    def setStickyDocument(self, doc=None):
        """Sticks to the given document or removes the 'stick' when None."""
        cur = self._currentStickyDocument
        self._currentStickyDocument = doc
        if cur:
            cur.closed.disconnect(self.slotUnStickDocument)
            cur.urlChanged.disconnect(self.slotUnStickDocument)
            self.stickyChanged(cur)
        if doc:
            doc.closed.connect(self.slotUnStickDocument)
            doc.urlChanged.connect(self.slotUnStickDocument)
            self.stickyChanged(doc)
        self.actionCollection.engrave_sticky.setChecked(bool(doc))
        self.updateStickyActionText()
        self.updateActions()

    def stickyDocument(self):
        """Returns the document currently marked as 'Sticky', if any."""
        return self._currentStickyDocument

    def slotUnStickDocument(self):
        """Called when the document that is currently sticky closes or reloads."""
        self.setStickyDocument(None)

    def updateStickyActionText(self):
        """Called when the sticky action toggles or when the language is changed."""
        doc = self.stickyDocument()
        if doc:
            text = _("&Always Engrave [{docname}]").format(docname = doc.documentName())
        else:
            text = _("&Always Engrave This Document")
        self.actionCollection.engrave_sticky.setText(text)

    def engraveAutoCompileToggled(self, enabled):
        """Called when the user toggles autocompile on/off."""
        from . import autocompile
        autocompile.AutoCompiler.instance(self.mainwindow()).setEnabled(enabled)

    def openLilyPondDatadir(self):
        """Menu action Open LilyPond Data Directory."""
        info = documentinfo.lilyinfo(self.mainwindow().currentDocument())
        datadir = info.datadir()
        if datadir:
            import helpers
            helpers.openUrl(QUrl.fromLocalFile(datadir))

    def slotDocumentClosed(self, doc):
        """Called when the user closes a document. Aborts a running Job."""
        j = job.manager.job(doc)
        if j and j.is_running():
            j.abort()

    def slotSessionChanged(self):
        """Called when the session is changed."""
        import sessions
        g = sessions.currentSessionGroup()
        if g:
            url = g.value("sticky_url", QUrl())
            if not url.isEmpty():
                d = app.findDocument(url)
                if d:
                    self.setStickyDocument(d)

    def slotSaveSessionData(self):
        """Called when a session needs to save data."""
        import sessions
        d = self.stickyDocument()
        g = sessions.currentSessionGroup()
        if g:
            if d and not d.url().isEmpty():
                g.setValue("sticky_url", d.url())
            else:
                g.remove("sticky_url")

    def saveSettings(self):
        """Save the state of some actions."""
        ac = self.actionCollection
        s = QSettings()
        s.beginGroup("engraving")
        s.setValue("autocompile", ac.engrave_autocompile.isChecked())

    def loadSettings(self):
        """Load the state of some actions."""
        ac = self.actionCollection
        s = QSettings()
        s.beginGroup("engraving")
        ac.engrave_autocompile.setChecked(s.value("autocompile", False, bool))

    def checkLilyPondInstalled(self, document, j, success):
        """Called when LilyPond is run for the first time.

        Displays a helpful dialog if the process failed to start.

        """
        app.jobFinished.disconnect(self.checkLilyPondInstalled)
        if not success and j.failed_to_start():
            QMessageBox.warning(self.mainwindow(),
                _("No LilyPond installation found"), _(
                "Frescobaldi uses LilyPond to engrave music, "
                "but LilyPond is not installed in the default locations "
                "and it cannot be found in your PATH.\n\n"
                "Please install LilyPond or, if you have already installed it, "
                "add it in the Preferences dialog."))



class Actions(actioncollection.ActionCollection):
    name = "engrave"

    def createActions(self, parent=None):
        self.engrave_sticky = QAction(parent)
        self.engrave_sticky.setCheckable(True)
        self.engrave_runner = QAction(parent)
        self.engrave_preview = QAction(parent)
        self.engrave_publish = QAction(parent)
        self.engrave_debug = QAction(parent)
        self.engrave_custom = QAction(parent)
        self.engrave_abort = QAction(parent)
        self.engrave_autocompile = QAction(parent)
        self.engrave_autocompile.setCheckable(True)
        self.engrave_open_lilypond_datadir = QAction(parent)

        self.engrave_preview.setShortcut(QKeySequence(Qt.Modifier.CTRL + Qt.Key.Key_M))
        self.engrave_publish.setShortcut(QKeySequence(Qt.Modifier.CTRL + Qt.Modifier.SHIFT + Qt.Key.Key_P))
        self.engrave_custom.setShortcut(QKeySequence(Qt.Modifier.CTRL + Qt.Modifier.SHIFT + Qt.Key.Key_M))
        self.engrave_abort.setShortcut(QKeySequence(Qt.Modifier.CTRL + Qt.Key.Key_Pause))

        self.engrave_sticky.setIcon(icons.get('pushpin'))
        self.engrave_preview.setIcon(icons.get('lilypond-run'))
        self.engrave_publish.setIcon(icons.get('lilypond-run'))
        self.engrave_debug.setIcon(icons.get('lilypond-run'))
        self.engrave_custom.setIcon(icons.get('lilypond-run'))
        self.engrave_abort.setIcon(icons.get('process-stop'))


    def translateUI(self):
        self.engrave_runner.setText(_("Engrave"))
        self.engrave_runner.setToolTip(_("Engrave (preview; Shift-click for custom)"))
        self.engrave_preview.setText(_("&Engrave (preview)"))
        self.engrave_publish.setText(_("Engrave (&publish)"))
        self.engrave_debug.setText(_("Engrave (&layout control)"))
        self.engrave_custom.setText(_("Engrave (&custom)..."))
        self.engrave_abort.setText(_("Abort Engraving &Job"))
        self.engrave_autocompile.setText(_("Automatic E&ngrave"))
        self.engrave_open_lilypond_datadir.setText(_("Open LilyPond &Data Directory"))
