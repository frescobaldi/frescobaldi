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
The Score Wizard dialog.
"""


from PyQt5.QtCore import pyqtSignal, QSettings, QUrl
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QTabWidget, QVBoxLayout, QWidget)

import app
import indent
import qutil
import userguide
import ly.document


class ScoreWizardDialog(QDialog):

    pitchLanguageChanged = pyqtSignal(str)

    def __init__(self, mainwindow):
        super(ScoreWizardDialog, self).__init__(mainwindow)
        self.addAction(mainwindow.actionCollection.help_whatsthis)
        self._pitchLanguage = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QTabWidget()
        b = self.dialogButtons = QDialogButtonBox()
        b.setStandardButtons(
            QDialogButtonBox.Reset
            | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "scorewiz")
        b.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.previewButton = b.addButton('', QDialogButtonBox.ActionRole)
        self.previewButton.clicked.connect(self.showPreview)
        layout.addWidget(self.tabs)
        layout.addWidget(b)

        self.header = Header(self)
        self.tabs.addTab(self.header, '')
        self.parts = Parts(self)
        self.tabs.addTab(self.parts, '')
        self.settings = Settings(self)
        self.tabs.addTab(self.settings, '')

        self.tabs.setCurrentIndex(0)
        self.tabs.widget(0).widget() # activate it
        self.tabs.currentChanged.connect(self.slotCurrentChanged)
        qutil.saveDialogSize(self, "scorewiz/dialog/size")
        app.translateUI(self)
        self.accepted.connect(self.slotAccepted)

    def translateUI(self):
        self.setWindowTitle(app.caption(_("Score Setup Wizard")))
        for i in range(self.tabs.count()):
            self.tabs.setTabText(i, self.tabs.widget(i).title())
        self.dialogButtons.button(QDialogButtonBox.Reset).setText(_("Clear"))
        self.dialogButtons.button(QDialogButtonBox.Reset).setToolTip(_(
            "Clears the current page of the Score Wizard."))
        self.previewButton.setText(_("Preview"))

    def slotCurrentChanged(self, i):
        """Lazy-loads the tab's page if shown for the first time."""
        self.tabs.widget(i).widget()

    def reset(self):
        self.tabs.currentWidget().widget().clear()

    def setPitchLanguage(self, language):
        if language != self._pitchLanguage:
            self._pitchLanguage = language
            self.pitchLanguageChanged.emit(language)

    def pitchLanguage(self):
        if self._pitchLanguage is None:
            # load setting; saving occurs in .settings.py
            lang = QSettings().value('scorewiz/lilypond/pitch_language', '', str)
            from .scoreproperties import keyNames
            if lang not in keyNames:
                lang = ''
            self._pitchLanguage = lang
        return self._pitchLanguage

    def slotAccepted(self):
        """Makes the score and puts it in the editor."""
        from . import build
        builder = build.Builder(self)       # get the builder
        text = builder.text()               # get the source text
        lydoc = ly.document.Document(text)  # temporarily store it in a lydoc
        cursor = ly.document.Cursor(lydoc)  # make a cursor selecting it
        indent.indenter().indent(cursor)    # indent it according to user prefs
        doc = app.openUrl(QUrl())           # get a new Frescobaldi document
        doc.setPlainText(lydoc.plaintext()) # write the text in it
        doc.setModified(False)              # make it "not modified"
        self.parent().setCurrentDocument(doc)

    def showPreview(self):
        """Shows a preview."""
        # get the document and fill in some example music
        from . import preview, build
        builder = build.Builder(self)
        doc = builder.document()
        preview.examplify(doc)
        # preview it
        import musicpreview
        dlg = musicpreview.MusicPreviewDialog(self)
        dlg.preview(builder.text(doc), _("Score Preview"))
        dlg.exec_()
        dlg.cleanup()


class Page(QWidget):
    """A Page in the tab widget.

    Basically this is just a QWidget that loads the desired page
    as soon as the widget() is called for the first time.

    """
    def __init__(self, dialog):
        super(Page, self).__init__(dialog)
        self._widget = None

    def title(self):
        """Should return a title."""

    def widget(self):
        if self._widget is None:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(layout)
            w = self._widget = self.createWidget(self)
            layout.addWidget(w)
        return self._widget

    def createWidget(self, parent):
        """Should return the widget for this tab."""


class Header(Page):
    def title(self):
        return _("&Titles and Headers")

    def createWidget(self, parent):
        from . import header
        return header.HeaderWidget(parent)


class Parts(Page):
    def title(self):
        return _("&Parts")

    def createWidget(self, parent):
        from . import score
        return score.ScorePartsWidget(parent)


class Settings(Page):
    def title(self):
        return _("&Score settings")

    def createWidget(self, parent):
        from . import settings
        return settings.SettingsWidget(parent)


