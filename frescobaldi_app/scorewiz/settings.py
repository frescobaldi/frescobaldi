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
The score settings widget.
"""


from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QVBoxLayout, QWidget,
                             QButtonGroup, QRadioButton)

import app
import po.setup
import language_names
import listmodel
import lilypondinfo

from . import scoreproperties

class SettingsWidget(QWidget):
    def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        grid = QGridLayout()
        self.setLayout(grid)

        self.scoreProperties = ScoreProperties(self)
        self.generalPreferences = GeneralPreferences(self)
        self.lilyPondPreferences = LilyPondPreferences(self)
        self.instrumentNames = InstrumentNames(self)

        grid.addWidget(self.scoreProperties, 0, 0)
        grid.addWidget(self.generalPreferences, 0, 1)
        grid.addWidget(self.lilyPondPreferences, 1, 0)
        grid.addWidget(self.instrumentNames, 1, 1)

    def clear(self):
        self.scoreProperties.tempo.clear()
        self.scoreProperties.keyNote.setCurrentIndex(0)
        self.scoreProperties.keyMode.setCurrentIndex(0)
        self.scoreProperties.pickup.setCurrentIndex(0)


class ScoreProperties(QGroupBox, scoreproperties.ScoreProperties):
    def __init__(self, parent):
        super(ScoreProperties, self).__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.createWidgets()
        self.layoutWidgets(layout)

        app.translateUI(self)

        scorewiz = self.window()
        scorewiz.pitchLanguageChanged.connect(self.setPitchLanguage)
        self.setPitchLanguage(scorewiz.pitchLanguage())

        self.loadSettings()
        self.window().finished.connect(self.saveSettings)

    def translateUI(self):
        self.translateWidgets()
        self.setTitle(_("Score properties"))

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/scoreproperties')
        self.metronomeRound.setChecked(s.value('round_metronome', True, bool))

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/scoreproperties')
        s.setValue('round_metronome', self.metronomeRound.isChecked())


class GeneralPreferences(QGroupBox):
    def __init__(self, parent):
        super(GeneralPreferences, self).__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.typq = QCheckBox()
        self.tagl = QCheckBox()
        self.barnum = QCheckBox()
        self.neutdir = QCheckBox()
        self.midi = QCheckBox()
        self.metro = QCheckBox()

        # paper size
        self.paperSizeLabel = QLabel()
        self.paper = QComboBox()
        self.paper.addItems(paperSizes)
        self.paper.activated.connect(self.slotPaperChanged)
        paperSizeBox = QHBoxLayout(spacing=2)
        paperSizeBox.addWidget(self.paperSizeLabel)
        paperSizeBox.addWidget(self.paper)

        # paper orientation
        self.paperRegularBtn = QRadioButton(self)
        self.paperLandscapeBtn = QRadioButton(self)
        self.paperRotatedBtn = QRadioButton(self)
        self.paperOrientationBox = QGroupBox()
        pg = self.paperOrientationGroup = QButtonGroup()
        pg.setExclusive(True)
        pg.addButton(self.paperRegularBtn, 0)
        pg.addButton(self.paperLandscapeBtn, 1)
        pg.addButton(self.paperRotatedBtn, 2)
        orientationBox = QHBoxLayout()
        orientationBox.addWidget(self.paperRegularBtn)
        orientationBox.addWidget(self.paperLandscapeBtn)
        orientationBox.addWidget(self.paperRotatedBtn)
        self.paperOrientationBox.setLayout(orientationBox)

        layout.addWidget(self.typq)
        layout.addWidget(self.tagl)
        layout.addWidget(self.barnum)
        layout.addWidget(self.neutdir)
        layout.addWidget(self.midi)
        layout.addWidget(self.metro)
        layout.addLayout(paperSizeBox)
        layout.addWidget(self.paperOrientationBox)

        app.translateUI(self)

        self.loadSettings()
        self.window().finished.connect(self.saveSettings)

    def translateUI(self):
        self.setTitle(_("General preferences"))
        self.typq.setText(_("Use typographical quotes"))
        self.typq.setToolTip(_(
            "Replace normal quotes in titles with nice typographical quotes."))
        self.tagl.setText(_("Remove default tagline"))
        self.tagl.setToolTip(_(
            "Suppress the default tagline output by LilyPond."))
        self.barnum.setText(_("Remove bar numbers"))
        self.barnum.setToolTip(_(
            "Suppress the display of measure numbers at the beginning of "
            "every system."))
        self.neutdir.setText(_("Smart neutral stem direction"))
        self.neutdir.setToolTip(_(
            "Use a logical direction (up or down) for stems on the middle "
            "line of a staff."))
        self.midi.setText(_("Create MIDI output"))
        self.midi.setToolTip(_(
            "Create a MIDI file in addition to the PDF file."))
        self.metro.setText(_("Show metronome mark"))
        self.metro.setToolTip(_(
            "If checked, show the metronome mark at the beginning of the "
            "score. The MIDI output also uses the metronome setting."))
        # paper size and orientation:
        self.paperSizeLabel.setText(_("Paper size:"))
        self.paper.setItemText(0, _("Default"))
        self.paperOrientationBox.setTitle(_("Orientation:"))
        self.paperRegularBtn.setText(_("Regular"))
        self.paperRegularBtn.setToolTip(_("Regular portrait orientation."))
        self.paperLandscapeBtn.setText(_("Landscape"))
        self.paperLandscapeBtn.setToolTip(_(
            "Set paper orientation to landscape while keeping upright printing orientation."))
        self.paperRotatedBtn.setText(_("Rotated"))
        self.paperRotatedBtn.setToolTip(_(
            "Rotate print on regular paper."))

    def slotPaperChanged(self, index):
        self.paperOrientationBox.setEnabled(bool(index))

    def getPaperSize(self):
        """Returns the configured papersize or the empty string for default."""
        return paperSizes[self.paper.currentIndex()]

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/preferences')
        self.typq.setChecked(s.value('typographical_quotes', True, bool))
        self.tagl.setChecked(s.value('remove_tagline', False, bool))
        self.barnum.setChecked(s.value('remove_barnumbers', False, bool))
        self.neutdir.setChecked(s.value('smart_neutral_direction', False, bool))
        self.midi.setChecked(s.value('midi', True, bool))
        self.metro.setChecked(s.value('metronome_mark', False, bool))
        psize = s.value('paper_size', '', str)
        enable = bool(psize and psize in paperSizes)
        self.paper.setCurrentIndex(paperSizes.index(psize) if enable else 0)
        orientation = s.value('paper_rotation', 0, int)
        self.paperOrientationGroup.button(orientation).setChecked(True)
        self.paperOrientationBox.setEnabled(enable)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/preferences')
        s.setValue('typographical_quotes', self.typq.isChecked())
        s.setValue('remove_tagline', self.tagl.isChecked())
        s.setValue('remove_barnumbers', self.barnum.isChecked())
        s.setValue('smart_neutral_direction', self.neutdir.isChecked())
        s.setValue('midi', self.midi.isChecked())
        s.setValue('metronome_mark', self.metro.isChecked())
        s.setValue('paper_size', paperSizes[self.paper.currentIndex()])
        s.setValue('paper_rotation', self.paperOrientationGroup.checkedId())


class InstrumentNames(QGroupBox):
    def __init__(self, parent):
        super(InstrumentNames, self).__init__(parent, checkable=True, checked=True)

        grid = QGridLayout()
        self.setLayout(grid)

        self.firstSystemLabel = QLabel()
        self.firstSystem = QComboBox()
        self.firstSystemLabel.setBuddy(self.firstSystem)
        self.otherSystemsLabel = QLabel()
        self.otherSystems = QComboBox()
        self.otherSystemsLabel.setBuddy(self.otherSystems)
        self.languageLabel = QLabel()
        self.language = QComboBox()
        self.languageLabel.setBuddy(self.language)

        self.firstSystem.setModel(listmodel.ListModel(
            (lambda: _("Long"), lambda: _("Short")), self.firstSystem,
            display = listmodel.translate))
        self.otherSystems.setModel(listmodel.ListModel(
            (lambda: _("Long"), lambda: _("Short"), lambda: _("None")), self.otherSystems,
            display = listmodel.translate))

        self._langs = l = ['','C']
        l.extend(sorted(po.available()))
        def display(lang):
            if lang == 'C':
                return _("English (untranslated)")
            elif not lang:
                return _("Default")
            return language_names.languageName(lang, po.setup.current())
        self.language.setModel(listmodel.ListModel(l, self.language, display=display))

        grid.addWidget(self.firstSystemLabel, 0, 0)
        grid.addWidget(self.firstSystem, 0, 1)
        grid.addWidget(self.otherSystemsLabel, 1, 0)
        grid.addWidget(self.otherSystems, 1, 1)
        grid.addWidget(self.languageLabel, 2, 0)
        grid.addWidget(self.language, 2, 1)
        app.translateUI(self)
        self.loadSettings()
        self.window().finished.connect(self.saveSettings)

    def translateUI(self):
        self.setTitle(_("Instrument names"))
        self.firstSystemLabel.setText(_("First system:"))
        self.otherSystemsLabel.setText(_("Other systems:"))
        self.languageLabel.setText(_("Language:"))
        self.firstSystem.setToolTip(_(
            "Use long or short instrument names before the first system."))
        self.otherSystems.setToolTip(_(
            "Use short, long or no instrument names before the next systems."))
        self.language.setToolTip(_(
            "Which language to use for the instrument names."))
        self.firstSystem.model().update()
        self.otherSystems.model().update()
        self.language.model().update()

    def getLanguage(self):
        """Returns the language the user has set.

        '' means:  default (use same translation as system)
        'C' means: English (untranslated)
        or a language code that is available in Frescobaldi's translation.

        """
        return self._langs[self.language.currentIndex()]

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/instrumentnames')
        self.setChecked(s.value('enabled', True, bool))
        allow = ['long', 'short']
        first = s.value('first', '', str)
        self.firstSystem.setCurrentIndex(allow.index(first) if first in allow else 0)
        allow = ['long', 'short', 'none']
        other = s.value('other', '', str)
        self.otherSystems.setCurrentIndex(allow.index(other) if other in allow else 2)
        language = s.value('language', '', str)
        self.language.setCurrentIndex(self._langs.index(language) if language in self._langs else 0)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/instrumentnames')
        s.setValue('enable', self.isChecked())
        s.setValue('first', ('long', 'short')[self.firstSystem.currentIndex()])
        s.setValue('other', ('long', 'short', 'none')[self.otherSystems.currentIndex()])
        s.setValue('language', self._langs[self.language.currentIndex()])


class LilyPondPreferences(QGroupBox):
    def __init__(self, parent):
        super(LilyPondPreferences, self).__init__(parent)

        grid = QGridLayout()
        self.setLayout(grid)

        self.pitchLanguageLabel = QLabel()
        self.pitchLanguage = QComboBox()
        self.versionLabel = QLabel()
        self.version = QComboBox(editable=True)

        self.pitchLanguage.addItem('')
        self.pitchLanguage.addItems([lang.title() for lang in sorted(scoreproperties.keyNames)])
        self.version.addItem(lilypondinfo.preferred().versionString())
        for v in ("2.18.0", "2.16.0", "2.14.0", "2.12.0"):
            if v != lilypondinfo.preferred().versionString():
                self.version.addItem(v)

        grid.addWidget(self.pitchLanguageLabel, 0, 0)
        grid.addWidget(self.pitchLanguage, 0, 1)
        grid.addWidget(self.versionLabel, 1, 0)
        grid.addWidget(self.version, 1, 1)

        self.pitchLanguage.activated.connect(self.slotPitchLanguageChanged)
        app.translateUI(self)
        self.loadSettings()
        self.window().finished.connect(self.saveSettings)

    def translateUI(self):
        self.setTitle(_("LilyPond"))
        self.pitchLanguageLabel.setText(_("Pitch name language:"))
        self.pitchLanguage.setToolTip(_(
            "The LilyPond language you want to use for the pitch names."))
        self.pitchLanguage.setItemText(0, _("Default"))
        self.versionLabel.setText(_("Version:"))
        self.version.setToolTip(_(
            "The LilyPond version you will be using for this document."))

    def slotPitchLanguageChanged(self, index):
        if index == 0:
            language = ''
        else:
            language = self.pitchLanguage.currentText().lower()
        self.window().setPitchLanguage(language)

    def loadSettings(self):
        language = self.window().pitchLanguage()
        languages = list(sorted(scoreproperties.keyNames))
        index = languages.index(language) + 1 if language in languages else 0
        self.pitchLanguage.setCurrentIndex(index)

    def saveSettings(self):
        QSettings().setValue('scorewiz/lilypond/pitch_language', self.window().pitchLanguage())


paperSizes = ['', 'a3', 'a4', 'a5', 'a6', 'a7', 'legal', 'letter', '11x17']
