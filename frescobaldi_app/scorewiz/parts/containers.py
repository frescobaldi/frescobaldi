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
Container part types.
"""


from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QRadioButton,
                             QVBoxLayout)

import ly.dom
import listmodel
import symbols
import widgets.lineedit
from scorewiz import scoreproperties

from . import _base
from . import register

class StaffGroup(_base.Container):
    @staticmethod
    def title(_=_base.translate):
        return _("Staff Group")

    def accepts(self):
        return (StaffGroup, _base.Part)

    def createWidgets(self, layout):
        self.systemStartLabel = QLabel()
        self.systemStart = QComboBox()
        self.systemStartLabel.setBuddy(self.systemStart)
        self.systemStart.setModel(listmodel.ListModel((
            # L10N: Brace like a piano staff
            (lambda: _("Brace"), 'system_start_brace'),
            # L10N: Bracket like a choir staff
            (lambda: _("Bracket"), 'system_start_bracket'),
            # L10N: Square bracket like a sub-group
            (lambda: _("Square"), 'system_start_square'),
            ), self.systemStart, display=listmodel.translate_index(0),
            icon=lambda item: symbols.icon(item[1])))
        self.systemStart.setIconSize(QSize(64, 64))
        self.connectBarLines = QCheckBox(checked=True)

        box = QHBoxLayout()
        box.addWidget(self.systemStartLabel)
        box.addWidget(self.systemStart)
        layout.addLayout(box)
        layout.addWidget(self.connectBarLines)

    def translateWidgets(self):
        self.systemStartLabel.setText(_("Type:"))
        self.connectBarLines.setText(_("Connect Barlines"))
        self.connectBarLines.setToolTip(_("If checked, barlines are connected between the staves."))
        self.systemStart.model().update()

    def build(self, data, builder):
        s = self.systemStart.currentIndex()
        b = self.connectBarLines.isChecked()
        if s == 0:
            node = ly.dom.GrandStaff()
            if not b:
                ly.dom.Line("\\remove Span_bar_engraver", node.getWith())
        else:
            node = ly.dom.StaffGroup() if b else ly.dom.ChoirStaff()
            if s == 2:
                node.getWith()['systemStartDelimiter'] = ly.dom.Scheme("'SystemStartSquare")
        data.nodes.append(node)
        data.music = ly.dom.Simr(node)


class Score(_base.Group, scoreproperties.ScoreProperties):
    @staticmethod
    def title(_=_base.translate):
        return _("Score")

    def createWidgets(self, layout):
        self.pieceLabel = QLabel()
        self.piece = QLineEdit()
        self.pieceLabel.setBuddy(self.piece)
        self.opusLabel = QLabel()
        self.opus = QLineEdit()
        self.opusLabel.setBuddy(self.opus)
        self.scoreProps = QGroupBox(checkable=True, checked=False)
        scoreproperties.ScoreProperties.createWidgets(self)

        grid = QGridLayout()
        grid.addWidget(self.pieceLabel, 0 ,0)
        grid.addWidget(self.piece, 0, 1)
        grid.addWidget(self.opusLabel, 1, 0)
        grid.addWidget(self.opus, 1, 1)
        layout.addLayout(grid)
        layout.addWidget(self.scoreProps)
        layout = QVBoxLayout()
        self.scoreProps.setLayout(layout)
        scoreproperties.ScoreProperties.layoutWidgets(self, layout)

        scorewiz = self.scoreProps.window()
        self.setPitchLanguage(scorewiz.pitchLanguage())
        scorewiz.pitchLanguageChanged.connect(self.setPitchLanguage)

    def translateWidgets(self):
        self.pieceLabel.setText(_("Piece:"))
        self.opusLabel.setText(_("Opus:"))
        self.scoreProps.setTitle(_("Properties"))
        scoreproperties.ScoreProperties.translateWidgets(self)

    def accepts(self):
        return (StaffGroup, _base.Part)

    def makeNode(self, node):
        score = ly.dom.Score(node)
        h = ly.dom.Header()
        piece = self.piece.text().strip()
        opus = self.opus.text().strip()
        if piece:
            h['piece'] = ly.dom.QuotedString(piece)
        if opus:
            h['opus'] = ly.dom.QuotedString(opus)
        if len(h):
            score.append(h)
        return score

    def globalSection(self, builder):
        if self.scoreProps.isChecked():
            return scoreproperties.ScoreProperties.globalSection(self, builder)



class BookPart(_base.Group):
    @staticmethod
    def title(_=_base.translate):
        return _("Book Part")

    def accepts(self):
        return (Score, StaffGroup, _base.Part)

    def makeNode(self, node):
        bookpart = ly.dom.BookPart(node)
        return bookpart


class Book(_base.Group):
    @staticmethod
    def title(_=_base.translate):
        return _("Book")

    def accepts(self):
        return (BookPart, Score, StaffGroup, _base.Part)

    def createWidgets(self, layout):
        self.bookOutputInfo = QLabel(wordWrap=True)
        self.bookOutputLabel = QLabel()
        self.bookOutput = widgets.lineedit.LineEdit()
        self.bookOutputFileName = QRadioButton()
        self.bookOutputSuffix = QRadioButton(checked=True)

        layout.addWidget(self.bookOutputInfo)
        grid = QGridLayout(spacing=0)
        grid.addWidget(self.bookOutputLabel, 0, 0)
        grid.addWidget(self.bookOutput, 0, 1, 1, 2)
        grid.addWidget(self.bookOutputFileName, 1, 1)
        grid.addWidget(self.bookOutputSuffix, 1, 2)
        layout.addLayout(grid)

    def translateWidgets(self):
        self.bookOutputInfo.setText(_(
            "<p>Here you can specify a filename or suffix (without extension) "
            "to set the names of generated output files for this book.</p>\n"
            "<p>If you choose \"Suffix\" the entered name will be appended "
            "to the document's file name; if you choose \"Filename\", just "
            "the entered name will be used.</p>"))
        self.bookOutputLabel.setText(_("Output Filename:"))
        self.bookOutputFileName.setText(_("Filename"))
        self.bookOutputSuffix.setText(_("Suffix"))

    def makeNode(self, node):
        book = ly.dom.Book(node)
        name = self.bookOutput.text().strip()
        if name:
            cmd = 'bookOutputName' if self.bookOutputFileName.isChecked() else 'bookOutputSuffix'
            ly.dom.Line(r'\{0} "{1}"'.format(cmd, name.replace('"', r'\"')), book)
        return book


register(
    lambda: _("Containers"),
    [
        StaffGroup,
        Score,
        BookPart,
        Book,
    ])
