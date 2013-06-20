# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
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
Export settings dialog.
"""

from __future__ import unicode_literals

import collections
import os

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import (QVBoxLayout, QHBoxLayout, QGridLayout, 
    QDialog, QFileDialog, QPrinter, QPrintDialog, QAbstractPrintDialog, 
    QGroupBox, QDialogButtonBox,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QRadioButton, QPushButton, QLabel)

import app
import help
import icons
import qutil

import widgets
import info
import export

class ExportDialog(QDialog):
    """A dialog to define source code export settings.
       Tries to be strict about interdepending properties.
       Optionally saves to Preferences.
    """
    def __init__(self, mainwindow):
        """Creates the about dialog. exec_() returns True or False."""
        super(ExportDialog, self).__init__(mainwindow)
        
        self.mainwindow = mainwindow
        self.document = mainwindow.currentDocument()
        self.docname, dummy = os.path.splitext(os.path.basename(self.document.url().path()))
        self.dirname = os.path.dirname(self.document.url().toLocalFile())
        if not self.dirname:
            from os.path import expanduser
            self.dirname = expanduser("~")

        # make a local copy of the options
        self.options = export.ExportOptions()
        self.options.assign(export.options)
        self.lastDest = self.options.value("dest")
        self.lastStyle = self.options.value("style")
        self.lastFiletype = self.options.value("filetype")
        self.lastDocname = self.docname
        
        self.createWidgets()
        self.assignOptions()
        
        self.createContainers()
        self.configureContainers()
        
        if self.options.value("source") == "css":
            self.setOption("source", "css")
        self.updateUI()
        self.composeLayout()
        self.connectSlots()
        
    def createWidgets(self):
        
        # "source"
        self.srcSelection = QRadioButton()
        self.srcDocument = QRadioButton()
        self.srcCSS = QRadioButton()
        
        # "document"
        self.docFull = QRadioButton()
        self.docBody = QRadioButton()
        
        # "destination"
        self.destClipboard = QRadioButton()
        self.destFile = QRadioButton()
        self.destPrinter = QRadioButton()
        
        # "style"
        self.styleInline = QRadioButton()
        self.styleCSS = QRadioButton()
        self.styleExternal = QRadioButton()
        
        # "format"
        self.formatHtml = QRadioButton()
        self.formatRich = QRadioButton()
        
        # "filetype"
        self.filetypeHtml = QRadioButton()
        self.filetypePdf = QRadioButton()
        self.filetypeOdt = QRadioButton()
        self.filetypeCSS = QRadioButton()
        
        # Line numbers
        self.lineNumbers = QCheckBox()
        self.printTitle = QCheckBox()
        
        # Filename
        self.dirnameLabel = QLabel()
        self.filenameLabel = QLabel()
        self.filenameEdit = QLineEdit()
        self.filenameSelect = QPushButton()
        self.filenameSelect.setFixedWidth(25)
        
        # Print layout
        
        self.orientPortrait = QRadioButton()
        self.orientLandscape = QRadioButton()
        self.colorColor = QRadioButton()
        self.colorGray = QRadioButton()
        self.marginTop = QSpinBox()
        self.marginBottom = QSpinBox()
        self.marginLeft = QSpinBox()
        self.marginRight = QSpinBox()
        self.marginTopLabel = QLabel()
        self.marginBottomLabel = QLabel()
        self.marginLeftLabel = QLabel()
        self.marginRightLabel = QLabel()
        self.paperSize = QComboBox()
        self.printerSelect = QPushButton()
        self.paperSizeLabel = QLabel()
        
        # Individual elements
        self.autoSave = QCheckBox()
        
        # Button(s)
        self.save = QPushButton()
        
    def assignOptions(self):
        """Bind options to widgets"""
        # Dictionary of option names,
        # each holding another dictionary 
        # mapping option values to autoexclusive 
        # checkable widgets (RadioButtons).
        # self.enumOptions[OPTIONNAME][self.options.value(OPTIONNAME)]
        # will point to the RadioButton in the dialog.
        self.enumOptions = {}
        self.enumOptions["source"]  = { 
            "selection": self.srcSelection, 
            "document": self.srcDocument, 
            "css": self.srcCSS }
        self.enumOptions["document"] = { 
            "full": self.docFull, 
            "body": self.docBody }
        self.enumOptions["dest"] = { 
            "clipboard": self.destClipboard, 
            "file": self.destFile, 
            "printer": self.destPrinter }
        self.enumOptions["style"] = { 
            "inline": self.styleInline, 
            "css": self.styleCSS, 
            "external": self.styleExternal }
        self.enumOptions["format"] = { 
            "html": self.formatHtml, 
            "formatted": self.formatRich }
        self.enumOptions["filetype"] = { 
            "html": self.filetypeHtml, 
            "pdf": self.filetypePdf, 
            "odt": self.filetypeOdt, 
            "css": self.filetypeCSS }
        self.enumOptions["orientation"] = {
            "portrait": self.orientPortrait, 
            "landscape": self.orientLandscape }
        self.enumOptions["color"] = {
            "color": self.colorColor, 
            "gray": self.colorGray }
        
        # Simpler dictionary for boolean options
        self.boolOptions = {}
        self.boolOptions["linenumbers"] = self.lineNumbers
        self.boolOptions["print_title"] = self.printTitle
        self.boolOptions["autosave_settings"] = self.autoSave
        
        # dictionary for setValue options
        self.valueOptions = {}
        self.valueOptions["margintop"] = self.marginTop
        self.valueOptions["marginbottom"] = self.marginBottom
        self.valueOptions["marginleft"] = self.marginLeft
        self.valueOptions["marginright"] = self.marginRight

    def createContainers(self):
        
        self.srcGroup = QGroupBox()
        self.docGroup =QGroupBox()
        self.destGroup = QGroupBox()
        self.styleGroup = QGroupBox()
        self.formatGroup = QGroupBox()
        self.filetypeGroup = QGroupBox()
        self.layoutGroup = QGroupBox()
        self.orientGroup = QGroupBox()
        self.colorGroup = QGroupBox()
        self.marginGroup = QGroupBox()
        self.printerGroup = QGroupBox()
        
        self.buttonBox = QHBoxLayout()
        
    def configureContainers(self):
        
        # Export source Group box
        self.srcLayout = QVBoxLayout()
        self.srcLayout.addWidget(self.srcSelection)
        self.srcLayout.addWidget(self.srcDocument)
        self.srcLayout.addWidget(self.srcCSS)
        self.srcGroup.setLayout(self.srcLayout)

        # Document Group Box
        self.docLayout = QVBoxLayout()
        self.docLayout.addWidget(self.docBody)
        self.docLayout.addWidget(self.docFull)
        self.docLayout.addStretch(1)
        self.docGroup.setLayout(self.docLayout)
        
        # Destination Group Box
        self.destLayout = QVBoxLayout()
        self.destLayout.addWidget(self.destClipboard)
        self.destLayout.addWidget(self.destFile)
        self.destLayout.addWidget(self.destPrinter)
        self.destGroup.setLayout(self.destLayout)
        
        # Style Group Box
        self.styleLayout = QVBoxLayout()
        self.styleLayout.addWidget(self.styleInline)
        self.styleLayout.addWidget(self.styleCSS)
        self.styleLayout.addWidget(self.styleExternal)
        self.styleLayout.addStretch(1)
        self.styleGroup.setLayout(self.styleLayout)
        
        # Format Group Box
        self.formatLayout = QVBoxLayout()
        self.formatLayout.addWidget(self.formatHtml)
        self.formatLayout.addWidget(self.formatRich)
        self.formatLayout.addStretch(2)
        self.formatGroup.setLayout(self.formatLayout)
        
        # Filetype Group Box
        self.filetypeLayout = QVBoxLayout()
        self.filetypeLayout.addWidget(self.filetypeHtml)
        self.filetypeLayout.addWidget(self.filetypePdf)
        self.filetypeLayout.addWidget(self.filetypeOdt)
        self.filetypeLayout.addWidget(self.filetypeCSS)
        self.filetypeGroup.setLayout(self.filetypeLayout)
        
        # Line Numbers
        self.lineNumLayout = QVBoxLayout()
        self.lineNumLayout.addWidget(self.printTitle)
        self.lineNumLayout.addWidget(self.lineNumbers)
        
        # File name
        self.destfileLayout = QVBoxLayout()
        self.dirnameLayout = QHBoxLayout()
        self.dirnameLayout.addWidget(self.filenameLabel)
        self.dirnameLayout.addStretch(1)
        self.dirnameLayout.addWidget(self.dirnameLabel)
        self.filenameLayout = QHBoxLayout()
        self.filenameLayout.addWidget(self.filenameEdit)
        self.filenameLayout.addWidget(self.filenameSelect)
        self.destfileLayout.addLayout(self.dirnameLayout)
        self.destfileLayout.addLayout(self.filenameLayout)
        
        # Print layout
        self.layoutLayout = QGridLayout()
        
        self.layoutLayout.addWidget(self.orientGroup, 0, 0)
        self.orientLayout = QVBoxLayout()
        self.orientLayout.addWidget(self.orientPortrait)
        self.orientLayout.addWidget(self.orientLandscape)
        self.orientGroup.setLayout(self.orientLayout)
        
        self.layoutLayout.addWidget(self.colorGroup, 1, 0)
        self.colorLayout = QVBoxLayout()
        self.colorLayout.addWidget(self.colorColor)
        self.colorLayout.addWidget(self.colorGray)
        self.colorGroup.setLayout(self.colorLayout)
        self.marginLayout = QGridLayout()
        self.marginLayout.addWidget(self.marginTopLabel, 0, 0)
        self.marginLayout.addWidget(self.marginBottomLabel, 1, 0)
        self.marginLayout.addWidget(self.marginLeftLabel, 2, 0)
        self.marginLayout.addWidget(self.marginRightLabel, 3, 0)
        self.marginLayout.addWidget(self.marginTop, 0, 1)
        self.marginLayout.addWidget(self.marginBottom, 1, 1)
        self.marginLayout.addWidget(self.marginLeft, 2, 1)
        self.marginLayout.addWidget(self.marginRight, 3, 1)
        for spin in [self.marginTop, self.marginBottom, self.marginLeft, self.marginRight]:
            spin.setMinimum(0)
        self.marginGroup.setLayout(self.marginLayout)
        self.layoutLayout.addWidget(self.marginGroup, 0, 1, 2, 1)
        self.printerLayout = QVBoxLayout()
        self.printerLayout.addWidget(self.paperSizeLabel)
        self.printerLayout.addWidget(self.paperSize)
        self.printerLayout.addWidget(self.printerSelect)
        self.printerLayout.addStretch(1)
        self.printerGroup.setLayout(self.printerLayout)
        self.layoutLayout.addWidget(self.printerGroup, 0, 2, 2, 1)
        self.layoutGroup.setLayout(self.layoutLayout)
        
        # Buttons bar
        self.buttonBox.addWidget(self.save)
        self.buttonBox.addStretch(1)
        b = self.buttons = QDialogButtonBox(self)
        b.setStandardButtons(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel)
        self.buttonBox.addWidget(b)
        
    def composeLayout(self):
        
        # Line numbers and filename
        lineNumFileBar = QHBoxLayout()
        lineNumFileBar.addLayout(self.lineNumLayout)
        lineNumFileBar.addLayout(self.destfileLayout)

        # grid
        grid = QGridLayout()
        grid.addWidget(self.srcGroup, 0, 0)
        grid.addWidget(self.docGroup, 0, 1)
        grid.addWidget(self.destGroup, 0, 2)
        grid.addLayout(lineNumFileBar, 1, 0, 1, 3)
        grid.addWidget(self.styleGroup, 2, 0)
        grid.addWidget(self.formatGroup, 2, 1)
        grid.addWidget(self.filetypeGroup, 2, 2)

        # layout
        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addWidget(self.layoutGroup)
        layout.addWidget(self.autoSave)
        layout.addLayout(self.buttonBox)
        
        self.setLayout(layout)
        app.translateUI(self)
        
    def connectSlots(self):
        
        # enumeration options
        self.srcSelection.toggled.connect(self.enumOptionToggled)
        self.srcCSS.toggled.connect(self.enumOptionToggled)
        self.srcDocument.toggled.connect(self.enumOptionToggled)
        self.docBody.toggled.connect(self.enumOptionToggled)
        self.docFull.toggled.connect(self.enumOptionToggled)
        self.destClipboard.toggled.connect(self.enumOptionToggled)
        self.destFile.toggled.connect(self.enumOptionToggled)
        self.destPrinter.toggled.connect(self.enumOptionToggled)
        self.styleInline.toggled.connect(self.enumOptionToggled)
        self.styleCSS.toggled.connect(self.enumOptionToggled)
        self.styleExternal.toggled.connect(self.enumOptionToggled)
        self.formatHtml.toggled.connect(self.enumOptionToggled)
        self.formatRich.toggled.connect(self.enumOptionToggled)
        self.filetypeHtml.toggled.connect(self.enumOptionToggled)
        self.filetypePdf.toggled.connect(self.enumOptionToggled)
        self.filetypeOdt.toggled.connect(self.enumOptionToggled)
        self.orientPortrait.toggled.connect(self.enumOptionToggled)
        self.orientLandscape.toggled.connect(self.enumOptionToggled)
        self.colorColor.toggled.connect(self.enumOptionToggled)
        self.colorGray.toggled.connect(self.enumOptionToggled)
        
        # boolean options
        self.lineNumbers.toggled.connect(self.boolOptionToggled)
        self.autoSave.toggled.connect(self.boolOptionToggled)
        
        # integer options
        self.marginTop.valueChanged.connect(self.valueOptionChanged)
        self.marginBottom.valueChanged.connect(self.valueOptionChanged)
        self.marginLeft.valueChanged.connect(self.valueOptionChanged)
        self.marginRight.valueChanged.connect(self.valueOptionChanged)
        
        # buttons
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.save.clicked.connect(self.saveSettings)
        self.filenameSelect.clicked.connect(self.filenameDlg)
        
        self.paperSize.activated.connect(self.paperSizeSelect)
        self.printerSelect.clicked.connect(self.printerSelectPressed)
    
    # ####################
    # UI translation
    # ####################
    
    def translateUI(self):
        self.setWindowTitle(_("Export Source"))
        self.srcGroup.setTitle(_("What to Export"))
        self.docGroup.setTitle(_("What to Generate"))
        self.destGroup.setTitle(_("Where to Export to"))
        self.styleGroup.setTitle(_("Styling Technique"))
        self.formatGroup.setTitle(_("Output Format"))
        self.filetypeGroup.setTitle(_("File Format"))
        self.layoutGroup.setTitle(_("Print/PDF Layout Settings"))
        
        # "source"
        self.srcSelection.setText(_("Current Selection"))
        self.srcSelection.setToolTip(_(
            "Exports the currently selected code."))
        self.srcDocument.setText(_("Whole Document"))
        self.srcDocument.setToolTip(_(
            "Exports the complete document,\n"
            "regardless of the current selection."))
        self.srcCSS.setText(_("CSS Stylesheets Only"))
        self.srcCSS.setToolTip(_(
            "Export a CSS style sheet for use\n"
            "as an external resource. This is\n"
            "independent of the current document."))
        
        # "document"
        self.docFull.setText(_("Complete Document"))
        self.docFull.setToolTip(_(
            "Export a complete Document\n"
            "that can be used standalone."))
        self.docBody.setText(_("Only Content (Body)"))
        self.docBody.setToolTip(_(
            "Export only the document body.\n"
            "This can't be used standalone\n"
            "but only within an existing document."))
        
        # "destination"
        self.destClipboard.setText(_("Clipboard"))
        self.destClipboard.setToolTip(_(
            "Export to Clipboard.\n"
            "You can paste into another application later."))
        self.destFile.setText(_("File"))
        self.destFile.setToolTip(_(
            "Export to a file."))
        self.destPrinter.setText(_("Printer"))
        self.destPrinter.setToolTip(_(
            "Print formatted source code on paper."))
        
        # "style"
        self.styleInline.setText(_("Inline"))
        self.styleInline.setToolTip(_(
            "Format each item directly.\n"
            "Useful for pasting into any HTML\n"
            "document without any dependencies."))
        self.styleCSS.setText(_("Use Style Sheets"))
        self.styleCSS.setToolTip(_(
            "Format each item with CSS classes.\n"
            "If \"What to generate\" is set to\n"
            "\"Complete Document\" this document\n"
            "will contain the style sheets in its header.\n"
            "otherwise this option is useful to paste\n"
            "into a HTML page that already references\n"
            "an external CSS file,"))
        self.styleExternal.setText(_("Use External CSS"))
        self.styleExternal.setToolTip(_(
            "Format each item with CSS classes.\n"
            "In the header an external CSS file\n"
            "is referenced. You are responsible\n"
            "that such a file is actually present."))
        
        # "format"
        self.formatHtml.setText(_("Plain HTML source"))
        self.formatHtml.setToolTip(_(
            "Export HTML source code that\n"
            "can be pasted to any text editor"))
        self.formatRich.setText(_("Formatted Rich Text"))
        self.formatRich.setToolTip(_(
            "Export Rich Text.\n"
            "Can only be pasted to a \n"
            "rich text editor, e.g. OpenOffice."))
        
        # "fileformat"
        self.filetypeHtml.setText(_(".html"))
        self.filetypePdf.setText(_(".pdf"))
        self.filetypeOdt.setText(_(".odt"))
        self.filetypeCSS.setText(_(".css"))
        
        # Line numbers
        self.printTitle.setText(_("Print Title"))
        self.printTitle.setToolTip(_(
            "Print the document\'s filename.\n"
            "When exporting to a complete HTML document\n"
            "this will be the title tag. When exporting\n"
            "to PDF or printing it will be a first line."))
        self.lineNumbers.setText(_("Line Numbers"))
        self.lineNumbers.setToolTip(_(
            "Print line numbers in front of every line."))
        
        # Filename
        self.filenameLabel.setText(_("File Name:"))
        self.filenameSelect.setText(_("..."))
        self.filenameSelect.setToolTip(_(
            "Select destination file name."))
        self.dirnameLabel.setToolTip(_(
            "Currently selected file\'s directory"))
        
        # Print layout
        self.orientGroup.setTitle(_("Paper Orientation:"))
        self.orientPortrait.setText(_("Portrait"))
        self.orientLandscape.setText(_("Landscape"))
        self.colorGroup.setTitle(_("Color Mode:"))
        self.colorGray.setText(_("Grayscale"))
        self.colorColor.setText(_("Color"))
        self.marginGroup.setTitle(_("Margins (mm):"))
        self.marginTopLabel.setText(_("Top:"))
        self.marginBottomLabel.setText(_("Bottom:"))
        self.marginLeftLabel.setText(_("Left:"))
        self.marginRightLabel.setText(_("Right:"))
        self.printerGroup.setTitle(_("More Options:"))
        self.paperSizeLabel.setText(_("Paper Size"))
        self.printerSelect.setText(_("Printer Options..."))
        
        # Individual elements
        self.autoSave.setText(_("Remember settings"))
        self.autoSave.setToolTip(_(
            "If checked, Frescobaldi will keep settings\n"
            "for source code export throughout sessions,\n"
            "without explicitely saving them."))
        
        # Button(s)
        self.save.setText(_("Save Settings"))
        self.save.setToolTip(_(
            "Permanently save settings.\n"
            "(Only useful when autoSave is deactivated)"))
        
    # ################
    # Handlers
    # ################
    
    def accept(self):
        self.writeOptions()
        export.options.autosave()
        super(ExportDialog, self).accept()
    
    def boolOptionToggled(self, checked):
        if self.updating:
            return
        for option in self.boolOptions:
            if self.boolOptions[option] == self.sender():
                self.options.set(option, checked, self)
        self.updateUI()

    def enumOptionToggled(self, checked):
        if (not checked) or self.updating:
            return
        for option in self.enumOptions:
            for value in self.enumOptions[option]:
                if self.enumOptions[option][value] == self.sender():
                    self.setOption(option, value)
        self.updateUI()

    def filenameDlg(self):
        name = os.path.join(self.dirname, self.docname)
        if self.options.value("filetype") == "pdf":
            if not name.endswith('-src'):
                name += '-src'
        filename = QFileDialog.getSaveFileName(self, app.caption(_("Export Source Code")),
            name, "{type} Files (*.{type})".format(type=self.options.value("filetype")))
        if filename:
            self.dirname = os.path.dirname(filename)
            fullname, dummy = os.path.splitext(filename)
            self.docname = os.path.basename(fullname)
            self.updateUI()
            
    def paperSizeSelect(self, item):
        pass
        
    def printerSelectPressed(self):
        printer = QPrinter()
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle(app.caption(_("dialog title", "Print Source")))
        options = (QAbstractPrintDialog.PrintShowPageSize
            | QAbstractPrintDialog.PrintPageRange
            | QAbstractPrintDialog.PrintShowPageSize)
        dlg.setOptions(options)
        if not dlg.exec_():
            return
        print dlg.testOption(QAbstractPrintDialog.PageSize)
#        print_selection = dlg.testOption(QAbstractPrintDialog.PrintSelection)
        
        
        
    def saveSettings(self):
        self.writeOptions()
        export.options.save()
        self.updateUI() 

    def setOption(self, option, value):
        """As a reaction to toggling a widget
           set the corresponding option and
           update other widgets accordingly."""
        self.options.set(option, value)
        if option == "source":
            for group in (self.docGroup, 
                          self.styleGroup, 
                          self.formatGroup, 
                          self.filetypeGroup, 
                          self.lineNumbers):
                group.setEnabled(value != "css")
            if value == "css":
                self.lastFiletype = self.options.value("filetype")
                self.options.set("filetype", "css")
                self.lastDocname = self.docname
                self.docname = "lilypond"
            else:
                if self.options.value("format") == "html":
                    self.options.set("filetype", "html")
                else:
                    self.options.set("filetype", "pdf")
                self.docname = self.lastDocname
        if option == "document":
            if value == "body":
                self.lastStyle = self.options.value("style")
                if self.options.value("style") == "external":
                    self.options.set("style", "inline")
            else:
                if self.lastStyle:
                    self.options.set("style", self.lastStyle)
        if option == "dest":
            if value == "file":
                if self.options.value("format") == "formatted":
                    self.lastFiletype = self.options.value("filetype")
                    if self.lastFiletype == "html":
                        self.options.set("filetype", "pdf")
            else:
                if self.options.value("format") == "formatted":
                    self.options.set("filetype", self.lastFiletype)
        if option == "format":
            if value == "formatted":
                self.lastStyle = self.options.value("style")
                self.options.set("style", "inline")
                if self.options.value("dest") == "file":
                    self.lastFiletype = self.options.value("filetype")
                    if self.lastFiletype == "html":
                        self.options.set("filetype", "pdf")
                    else:
                        self.options.set("filetype", self.lastFiletype)
            else:
                self.options.set("style", self.lastStyle)
        if option == "filetype":
            if value == "pdf":
                if not self.docname.endswith("-src"):
                    self.docname += "-src"
            else:
                if self.docname.endswith("-src"):
                    self.docname = self.docname[:-4]
        
    def updateLogic(self):
        self.save.setEnabled(self.options.changed())

    def updateUI(self):
        """Read the settings from the local copy
           and update the widgets."""
        self.updating = True
        # read all options and update widgets
        for option in self.enumOptions:
            self.enumOptions[option][self.options.value(option)].setChecked(True)
        for option in self.boolOptions:
            self.boolOptions[option].setChecked(self.options.value(option))
        for option in self.valueOptions:
            self.valueOptions[option].setValue(int(self.options.value(option)))

        # disable/enable widgets according to application logic
        self.srcSelection.setEnabled(self.mainwindow.hasSelection())
        
        self.docGroup.setEnabled(self.options.value("format") == "html")
        
        self.printTitle.setEnabled(self.options.value("document") == "full")
        
        self.filenameEdit.setEnabled(self.options.value("dest") == "file")
        if len(self.dirname) > 50:
            displaydirname = self.dirname[:10] + "..." + self.dirname[len(self.dirname) - 37:]
        else:
            displaydirname = self.dirname
        self.dirnameLabel.setText(displaydirname)
        self.filenameEdit.setText(self.docname + "." + self.options.value("filetype"))
        self.filenameSelect.setEnabled(self.options.value("dest") == "file")
            
        self.styleExternal.setEnabled(self.options.value("document") == "full" and
                                      self.options.value("format") == "html")
        self.styleGroup.setEnabled(self.options.value("format") == "html" and
                                   self.options.value("source") != "css")    
        
        self.filetypeGroup.setEnabled(self.options.value("dest") == "file" and
                                      self.options.value("source") != "css")
        
        self.layoutGroup.setEnabled((self.options.value("dest") == "file" and
                                    self.options.value("filetype") == "pdf") or
                                    self.options.value("dest") == "printer")
        
        self.save.setEnabled(self.options.changed())
        self.updating = False

    def valueOptionChanged(self, value):
        if self.updating:
            return
        for option in self.valueOptions:
            if self.valueOptions[option] == self.sender():
                print "new value:", option, value
                self.options.set(option, value, self)
        self.updateUI()

    def writeOptions(self):
        """Read the values from the Dialog
           and write them to the options object
           (not the QSettings object)"""
        self.options.set("filename", os.path.join(self.dirname, self.filenameEdit.text()))
        export.options.assign(self.options)
