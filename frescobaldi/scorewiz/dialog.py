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


from PyQt6.QtCore import pyqtSignal, QSettings, QUrl
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QGroupBox, QTabWidget, QVBoxLayout, QWidget)

import app
import indent
import qutil
import userguide
import ly.document
import ly.dom
import ly.music
import ly.util


class ScoreWizardDialog(QDialog):

    pitchLanguageChanged = pyqtSignal(str)

    def __init__(self, mainwindow):
        super().__init__(mainwindow)
        self.addAction(mainwindow.actionCollection.help_whatsthis)
        self._pitchLanguage = None
        self.mainwindow = mainwindow

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tabs = QTabWidget()
        b = self.dialogButtons = QDialogButtonBox()
        b.setStandardButtons(
            QDialogButtonBox.StandardButton.Reset
            | QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.accepted.connect(self.accept)
        b.rejected.connect(self.reject)
        userguide.addButton(b, "scorewiz")
        b.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset)
        self.previewButton = b.addButton('', QDialogButtonBox.ButtonRole.ActionRole)
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
        self.dialogButtons.button(QDialogButtonBox.StandardButton.Reset).setText(_("Clear"))
        self.dialogButtons.button(QDialogButtonBox.StandardButton.Reset).setToolTip(_(
            "Clears the current page of the Score Wizard."))
        self.previewButton.setText(_("Preview"))

    def slotCurrentChanged(self, i):
        """Lazy-loads the tab's page if shown for the first time."""
        self.tabs.widget(i).widget()

    def reset(self):
        self.tabs.currentWidget().widget().clear()

    def resetAll(self):
        for tab in self.header, self.parts, self.settings:
            tab.widget().clear()

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
        doc = builder.document()            # get the ly.dom document tree
        if not self.settings.widget().generalPreferences.relpitch.isChecked():
            # remove pitches from \relative commands
            for n in doc.find(ly.dom.Relative):
                for n1 in n.find(ly.dom.Pitch, 1):
                    n.remove(n1)
        text = builder.text(doc)            # convert to LilyPond source text
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
        dlg.exec()
        dlg.cleanup()

    def readScore(self):
        """Read the score of an existing document."""
        self.resetAll()
        cursor = self.mainwindow.textCursor()
        text = cursor.document().toPlainText()
        # Parse the music
        music = ly.music.document(ly.document.Document(text))
        for item in music:
            if isinstance(item, ly.music.items.Header):
                self.header.readFromMusicItem(item)
            elif isinstance(item, ly.music.items.Assignment):
                name = item.name()
                if name == 'global':
                    self.settings.readFromMusicItem(item)
                elif name.endswith('Part'):
                    self.parts.readFromMusicItem(item)


class Page(QWidget):
    """A Page in the tab widget.

    Basically this is just a QWidget that loads the desired page
    as soon as the widget() is called for the first time.

    """
    def __init__(self, dialog):
        super().__init__(dialog)
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

    def readFromMusicItem(self, headerBlock):
        """Read an existing header block as a ly.music.items.Header."""
        widget = self.widget()
        for item in headerBlock:
            name = item.name()
            value = item.value()
            if name in widget.edits:
                widget.edits[name].setText(value.plaintext())


class Parts(Page):
    def __init__(self, dialog):
        super().__init__(dialog)
        # Directory mapping assignment identifiers to the corresponding
        # Part class. For example: self._partTypes['jazzGuitar'] == JazzGuitar
        self._partTypes = {}

    def title(self):
        return _("&Parts")

    def createWidget(self, parent):
        from . import score
        return score.ScorePartsWidget(parent)

    def readFromMusicItem(self, assignment):
        """Read a part definition from an ly.music.items.Assignment."""
        from . import score
        widget = self.widget()
        if not self._partTypes:
            # This is only needed when reading from an existing score,
            # so generate it the first time it is used.
            from . import build, parts
            for category in parts.categories:
                for item in category.items:
                    self._partTypes[ly.util.mkid(item.__name__)] = item
        name = assignment.name()
        # Make sure this is, in fact, a part definition before proceeding.
        # We already check this in ScoreWizardDialog.readScore(), but it never
        # hurts to be safe...
        if name.endswith('Part'):
            try:
                # TODO: Handle containers
                parent = widget.scoreView
                part = self._partTypes[name[:-4]]
                box = QGroupBox(widget.partSettings)
                score.PartItem(parent, part, box)
            except KeyError:
                pass


class Settings(Page):
    def title(self):
        return _("&Score settings")

    def createWidget(self, parent):
        from . import settings
        return settings.SettingsWidget(parent)

    def readFromMusicItem(self, assignment):
        """Read settings from an ly.music.items.Assignment."""
        from . import scoreproperties
        widget = self.widget()
        sp = widget.scoreProperties
        for item in assignment.value():
            if isinstance(item, ly.music.items.KeySignature):
                pitch = item.pitch()
                # pitch.alter is a fractions.Fraction
                key = (pitch.note, pitch.alter.numerator)
                if key in scoreproperties.keys:
                    sp.keyNote.setCurrentIndex(scoreproperties.keys.index(key))
                for mode, translation in scoreproperties.modes:
                    if mode == item.mode():
                        sp.keyMode.setCurrentText(translation())
                        break
            elif isinstance(item, ly.music.items.Partial):
                length = item.partial_length()
                midiDuration = (length.denominator, length.numerator)
                if midiDuration in scoreproperties.midiDurations:
                    # index 0 is "None"
                    sp.pickup.setCurrentIndex(
                        scoreproperties.midiDurations.index(midiDuration) + 1
                    )
            elif isinstance(item, ly.music.items.Tempo):
                fraction = item.fraction()
                midiDuration = (fraction.denominator, fraction.numerator)
                if midiDuration in scoreproperties.midiDurations:
                    sp.metronomeNote.setCurrentIndex(
                        scoreproperties.midiDurations.index(midiDuration)
                    )
                tempo = item.tempo()
                if tempo:
                    sp.metronomeValue.setCurrentText(str(tempo[0]))
                if item.text():
                    sp.tempo.setText(item.text().plaintext())
            elif isinstance(item, ly.music.items.TimeSignature):
                # Note item.fraction().numerator is always 1
                fraction = "{}/{}".format(item.numerator(),
                                            item.fraction().denominator)
                sp.timeSignature.setCurrentText(fraction)


