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
The SVG preview panel widget.
"""


import os
import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                             QSpinBox, QToolButton, QVBoxLayout, QWidget)

import app
import qutil
import resultfiles

from . import view
from . import svgfiles


class SvgView(QWidget):
    def __init__(self, dockwidget):
        super(SvgView, self).__init__(dockwidget)

        self._document = None
        self._setting_zoom = False

        self.view = view.View(self)

        self.pageLabel = QLabel()
        self.pageCombo = QComboBox(sizeAdjustPolicy=QComboBox.AdjustToContents)

        layout = QVBoxLayout(spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        hbox = QHBoxLayout(spacing=0)
        hbox.addWidget(self.pageLabel)
        hbox.addWidget(self.pageCombo)

        self.zoomInButton = QToolButton(autoRaise=True)
        self.zoomOutButton = QToolButton(autoRaise=True)
        self.zoomOriginalButton = QToolButton(autoRaise=True)
        self.zoomNumber = QSpinBox(minimum=10, maximum=1000, suffix='%')
        ac = dockwidget.actionCollection
        self.zoomInButton.setDefaultAction(ac.svg_zoom_in)
        self.zoomOutButton.setDefaultAction(ac.svg_zoom_out)
        self.zoomOriginalButton.setDefaultAction(ac.svg_zoom_original)
        hbox.addWidget(self.zoomInButton)
        hbox.addWidget(self.zoomNumber)
        hbox.addWidget(self.zoomOutButton)
        hbox.addWidget(self.zoomOriginalButton)

        self.resetButton = QPushButton("reload", self)
        self.resetButton.clicked.connect(self.reLoadDoc)
        hbox.addWidget(self.resetButton)

        self.saveButton = QPushButton("save edits", self)
        self.saveButton.clicked.connect(self.callSave)
        hbox.addWidget(self.saveButton)

        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addWidget(self.view)

        app.jobFinished.connect(self.initSvg)
        app.documentClosed.connect(self.slotDocumentClosed)
        app.documentLoaded.connect(self.initSvg)
        self.pageCombo.currentIndexChanged.connect(self.changePage)
        self.zoomNumber.valueChanged.connect(self.slotZoomNumberChanged)
        self.view.zoomFactorChanged.connect(self.slotViewZoomChanged)
        dockwidget.mainwindow().currentDocumentChanged.connect(self.initSvg)
        self.zoomNumber.setValue(100)
        doc = dockwidget.mainwindow().currentDocument()
        if doc:
            self.initSvg(doc)
        app.translateUI(self)

    def translateUI(self):
        self.pageLabel.setText(_("Page:"))

    def mainwindow(self):
        return self.parent().mainwindow()

    def initSvg(self, doc):
        """Opens first page of score after compilation"""
        if doc == self.mainwindow().currentDocument():
            files = svgfiles.SvgFiles.instance(doc)
            model = files.model() # forces update
            if files:
                self._document = doc
                with qutil.signalsBlocked(self.pageCombo):
                    self.pageCombo.setModel(model)
                    self.pageCombo.setCurrentIndex(files.current)
                self.view.load(files.url(files.current))

    def reLoadDoc(self):
        """Reloads current document."""
        if self._document:
            self.initSvg(self._document)

    def callSave(self):
        """Call save function"""
        self.view.evalSave()

    def getCurrent(self):
        files = svgfiles.SvgFiles.instance(self._document)
        return files.filename(files.current)

    def slotZoomNumberChanged(self, value):
        self._setting_zoom = True
        self.view.setZoomFactor(value / 100.0)
        self._setting_zoom = False

    def slotViewZoomChanged(self):
        if not self._setting_zoom:
            self.zoomNumber.setValue(int(self.view.zoomFactor() * 100))

    def changePage(self, page_index):
        """change page of score"""
        doc = self._document
        if doc:
            files = svgfiles.SvgFiles.instance(doc)
            if files:
                files.current = page_index
                svg = files.url(page_index)
                self.view.load(svg)

    def slotDocumentClosed(self, doc):
        if doc == self._document:
            self._document = None
            if self.pageCombo.model():
                self.pageCombo.model().deleteLater()
            self.pageCombo.clear()
            self.pageCombo.update() # otherwise it doesn't redraw
            self.view.clear()

