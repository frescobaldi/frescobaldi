# -*- coding: utf-8 -*-
#
# This file is part of the qpageview package.
#
# Copyright (c) 2019 - 2019 by Wilbert Berendsen
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
ViewActions provides QActions to control a View.
"""


import weakref

from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction, QActionGroup, QApplication, QComboBox, QLabel, QSpinBox,
    QWidgetAction)

from . import util
from .constants import *


class ViewActions(QObject):
    """ViewActions provides QActions to control a View.

    Use setView() to connect the actions with a View. If no View is connected,
    and an action is used; the viewRequested signal is emitted. You can connect
    this signal and call setView() in the called slot; the action is then
    performed on the View.

    The attribute `smartLayoutOrientationEnabled` (defaulting to True) enables
    some intuitive behaviour: if set to True, for layout modes that do not make
    sense in horizontal mode the orientation is automatically set to Vertical;
    and when the user chooses Horizontal orientation in such modes, the layout
    mode is set to "single".

    """

    smartLayoutOrientationEnabled = True

    viewRequested = pyqtSignal()

    def __init__(self, *args, **kwargs):
        """Create the actions.

        Does not yet connect anything, use setView() for that.

        """
        super().__init__(*args, **kwargs)
        self._view = lambda: None
        self.createActions()
        self.connectActions()
        self.setActionTexts()
        self.setActionIcons()
        self.setActionShortcuts()

    def setView(self, view):
        """Connects all the actions to the View.

        Use None to set no view. If a view was previously set, all connections
        are removed from that View.

        """
        old = self._view()
        if old == view:
            return
        if old:
            old.viewModeChanged.disconnect(self.updateViewModeActions)
            old.zoomFactorChanged.disconnect(self.updateZoomActions)
            old.pageLayoutModeChanged.disconnect(self.updatePageLayoutModeActions)
            old.orientationChanged.disconnect(self.updateActions)
            old.continuousModeChanged.disconnect(self.updateActions)
            old.currentPageNumberChanged.disconnect(self.updatePagerActions)
            old.pageCountChanged.disconnect(self.updatePagerActions)

        if view:
            view.viewModeChanged.connect(self.updateViewModeActions)
            view.zoomFactorChanged.connect(self.updateZoomActions)
            view.pageLayoutModeChanged.connect(self.updatePageLayoutModeActions)
            view.orientationChanged.connect(self.updateActions)
            view.continuousModeChanged.connect(self.updateActions)
            view.currentPageNumberChanged.connect(self.updatePagerActions)
            view.pageCountChanged.connect(self.updatePagerActions)
            self._view = weakref.ref(view)
            self.updateActions()
            self.updateViewModeActions(view.viewMode())
            self.updateZoomActions(view.zoomFactor())
            self.updatePagerActions()
        else:
            self._view = lambda: None

    def view(self):
        """Return the View.

        If no View is set, viewRequested is emitted. You can connect to this
        signal to create a View, and call setView() to use it to perform
        the requested action.

        """
        view = self._view()
        if not view:
            self.viewRequested.emit()
        return self._view()

    @staticmethod
    def names():
        """Return a tuple of all the names of the actions we support."""
        return (
            'print',
            'fit_width',
            'fit_height',
            'fit_both',
            'zoom_natural',
            'zoom_original'
            'zoom_in',
            'zoom_out',
            'zoomer',
            'rotate_left',
            'rotate_right',
            'layout_single',
            'layout_double_right',
            'layout_double_left',
            'layout_raster',
            'vertical',
            'horizontal',
            'continuous',
            'reload',
            'previous_page',
            'next_page',
            'pager',
            'magnifier',
        )

    def createActions(self):
        """Creates the actions; called by __init__()."""
        self.print = QAction(self)

        self._viewMode = QActionGroup(self)
        self.fit_width = QAction(self._viewMode, checkable=True)
        self.fit_height = QAction(self._viewMode, checkable=True)
        self.fit_both = QAction(self._viewMode, checkable=True)

        self.zoom_natural = QAction(self)
        self.zoom_original = QAction(self)
        self.zoom_in = QAction(self)
        self.zoom_out = QAction(self)
        self.zoomer = ZoomerAction(self)

        self.rotate_left = QAction(self)
        self.rotate_right = QAction(self)

        self._pageLayoutMode = QActionGroup(self)
        self.layout_single = QAction(self._pageLayoutMode, checkable=True)
        self.layout_double_right = QAction(self._pageLayoutMode, checkable=True)
        self.layout_double_left = QAction(self._pageLayoutMode, checkable=True)
        self.layout_raster = QAction(self._pageLayoutMode, checkable=True)

        self._orientation = QActionGroup(self)
        self.vertical = QAction(self._orientation, checkable=True)
        self.horizontal = QAction(self._orientation, checkable=True)

        self.continuous = QAction(self, checkable=True)
        self.reload = QAction(self)

        self.previous_page = QAction(self)
        self.next_page = QAction(self)
        self.pager = PagerAction(self)

        self.magnifier = QAction(self, checkable=True)

    def updateFromProperties(self, properties):
        """Set the actions to the state stored in the given ViewProperties."""
        if properties.pageLayoutMode is not None:
            self.updatePageLayoutModeActions(properties.pageLayoutMode)
        if properties.orientation is not None:
            self.vertical.setChecked(properties.orientation == Vertical)
            self.horizontal.setChecked(properties.orientation == Horizontal)
        if properties.continuousMode is not None:
            self.continuous.setChecked(properties.continuousMode)
        if properties.zoomFactor is not None:
            self.updateZoomActions(properties.zoomFactor)
        if properties.viewMode is not None:
            self.updateViewModeActions(properties.viewMode)

    def connectActions(self):
        """Connect our actions with our methods. Called by __init__()."""
        self.print.triggered.connect(self.slotPrint)
        self._viewMode.triggered.connect(self.slotViewMode)
        self.zoom_natural.triggered.connect(self.slotZoomNatural)
        self.zoom_original.triggered.connect(self.slotZoomOriginal)
        self.zoom_in.triggered.connect(self.slotZoomIn)
        self.zoom_out.triggered.connect(self.slotZoomOut)
        self.zoomer.zoomFactorChanged.connect(self.slotZoomFactor)
        self.zoomer.viewModeChanged.connect(self.slotZoomViewMode)
        self.rotate_left.triggered.connect(self.slotRotateLeft)
        self.rotate_right.triggered.connect(self.slotRotateRight)
        self._pageLayoutMode.triggered.connect(self.slotPageLayoutMode)
        self._orientation.triggered.connect(self.slotOrientation)
        self.continuous.triggered.connect(self.slotContinuousMode)
        self.reload.triggered.connect(self.slotReload)
        self.previous_page.triggered.connect(self.slotPreviousPage)
        self.next_page.triggered.connect(self.slotNextPage)
        self.pager.currentPageNumberChanged.connect(self.slotSetPageNumber)
        self.magnifier.triggered.connect(self.slotMagnifier)

    def updateActions(self):
        """Update the state of the actions not handled in the other update methods."""
        view = self.view()
        if not view:
            return
        self.print.setEnabled(view.pageCount() > 0)
        self.vertical.setChecked(view.orientation() == Vertical)
        self.horizontal.setChecked(view.orientation() == Horizontal)
        self.continuous.setChecked(view.continuousMode())
        self.magnifier.setEnabled(bool(view.magnifier()))
        self.magnifier.setChecked(bool(view.magnifier() and view.magnifier().isVisible()))

    def updatePageLayoutModeActions(self, mode):
        """Update the state of the layout mode actions."""
        self.layout_single.setChecked(mode == "single")
        self.layout_double_left.setChecked(mode == "double_left")
        self.layout_double_right.setChecked(mode == "double_right")
        self.layout_raster.setChecked(mode == "raster")

    def updateViewModeActions(self, mode):
        """Update the state of view mode related actions."""
        self.fit_width.setChecked(mode == FitWidth)
        self.fit_height.setChecked(mode == FitHeight)
        self.fit_both.setChecked(mode == FitBoth)
        self.zoomer.setViewMode(mode)

    def updateZoomActions(self, factor):
        """Update the state of zoom related actions."""
        self.zoomer.setZoomFactor(factor)

    def updatePagerActions(self):
        """Update the state of paging-related actions."""
        view = self.view()
        if not view:
            return
        self.pager.setPageCount(view.pageCount())
        self.pager.updateCurrentPageNumber(view.currentPageNumber())
        self.pager.setEnabled(view.pageCount() > 0)
        self.previous_page.setEnabled(view.currentPageNumber() > 1)
        self.next_page.setEnabled(view.currentPageNumber() < view.pageCount())

    def setActionTexts(self, _=None):
        """Set a default text to all the actions, you may override or translate them.

        You may also set tooltip or whatsthis text in this method.

        """
        if _ is None: _ = lambda t: t
        self.print.setText(_("&Print..."))
        self.fit_width.setText(_("Fit &Width"))
        self.fit_height.setText(_("Fit &Height"))
        self.fit_both.setText(_("Fit &Page"))
        self.zoom_natural.setText(_("&Natural Size"))
        self.zoom_original.setText(_("Original &Size"))
        self.zoom_in.setText(_("Zoom &In"))
        self.zoom_out.setText(_("Zoom &Out"))
        self.zoomer.setViewModes((
            # L10N: "Width" as in "Fit Width" (display in zoom menu)
            (FitWidth, _("Width")),
            # L10N: "Height" as in "Fit Height" (display in zoom menu)
            (FitHeight, _("Height")),
            # L10N: "Page" as in "Fit Page" (display in zoom menu)
            (FitBoth, _("Page")),
        ))
        self.rotate_left.setText(_("Rotate &Left"))
        self.rotate_right.setText(_("Rotate &Right"))
        self.layout_single.setText(_("Single Pages"))
        self.layout_double_right.setText(_("Two Pages (first page right)"))
        self.layout_double_left.setText(_("Two Pages (first page left)"))
        self.layout_raster.setText(_("Raster"))
        self.vertical.setText(_("Vertical"))
        self.horizontal.setText(_("Horizontal"))
        self.continuous.setText(_("&Continuous"))
        self.reload.setText(_("Re&load View"))
        self.previous_page.setText(_("Previous Page"))
        self.previous_page.setIconText(_("Previous"))
        self.next_page.setText(_("Next Page"))
        self.next_page.setIconText(_("Next"))
        self.magnifier.setText(_("Magnifier"))

    def setActionIcons(self):
        """Implement this method to set icons to the actions."""
        pass

    def setActionShortcuts(self):
        """Implement this method to set keyboard shortcuts to the actions."""
        self.print.setShortcuts(QKeySequence.Print)
        self.zoom_in.setShortcuts(QKeySequence.ZoomIn)
        self.zoom_out.setShortcuts(QKeySequence.ZoomOut)
        self.reload.setShortcut(QKeySequence(Qt.Key_F5))

    def slotPrint(self):
        view = self.view()
        if view:
            view.print()

    def slotViewMode(self, action):
        view = self.view()
        if view:
            viewMode = FitWidth if action == self.fit_width else \
                       FitHeight if action == self.fit_height else \
                       FitBoth
            view.setViewMode(viewMode)

    def slotZoomNatural(self):
        view = self.view()
        if view:
            view.zoomNaturalSize()

    def slotZoomOriginal(self):
        view = self.view()
        if view:
            view.setZoomFactor(1.0)

    def slotZoomIn(self):
        view = self.view()
        if view:
            view.zoomIn()

    def slotZoomOut(self):
        view = self.view()
        if view:
            view.zoomOut()

    def slotZoomViewMode(self, mode):
        view = self.view()
        if view:
            view.setViewMode(mode)

    def slotZoomFactor(self, factor):
        view = self.view()
        if view:
            view.setZoomFactor(factor)

    def slotRotateLeft(self):
        view = self.view()
        if view:
            view.rotateLeft()

    def slotRotateRight(self):
        view = self.view()
        if view:
            view.rotateRight()

    def slotPageLayoutMode(self, action):
        view = self.view()
        if view:
            mode = "single" if action == self.layout_single else \
                   "double_left" if action == self.layout_double_left else \
                   "double_right" if action == self.layout_double_right else \
                   "raster"
            view.setPageLayoutMode(mode)

            if self.smartLayoutOrientationEnabled:
                if mode in ("double_left", "double_right"):
                    view.setOrientation(Vertical)

    def slotOrientation(self, action):
        view = self.view()
        if view:
            orientation = Vertical if action == self.vertical else Horizontal
            view.setOrientation(orientation)

            if self.smartLayoutOrientationEnabled:
                if orientation == Horizontal and \
                        view.pageLayoutMode() in ("double_left", "double_right"):
                    view.setPageLayoutMode("single")

    def slotContinuousMode(self):
        view = self.view()
        if view:
            view.setContinuousMode(self.continuous.isChecked())

    def slotReload(self):
        view = self.view()
        if view:
            view.reload()

    def slotPreviousPage(self):
        view = self.view()
        if view:
            view.gotoPreviousPage()

    def slotNextPage(self):
        view = self.view()
        if view:
            view.gotoNextPage()

    def slotSetPageNumber(self, num):
        view = self.view()
        if view:
            view.setCurrentPageNumber(num)

    def slotMagnifier(self):
        view = self._view() # do not trigger creation
        if view and view.magnifier():
            view.magnifier().setVisible(self.magnifier.isChecked())


class PagerAction(QWidgetAction):
    """PagerAction shows a spinbox widget with the current page number.

    When the current page number is changed (by the user or by calling
    setCurrentPageNumber()) the signal currentPageNumberChanged() is emitted
    with the new current page number.

    You can use the instance or class attributes buttonSymbols, focusPolicy and
    the displayFormat() method to influence behaviour and appearance of the
    spinbox widget(s) that is/are created when this action is added to a
    toolbar.

    The displayFormat string should contain the text "{num}". You can also
    include the string "{total}", so the page count is displayed as well.

    """

    currentPageNumberChanged = pyqtSignal(int)

    buttonSymbols = QSpinBox.NoButtons
    focusPolicy = Qt.ClickFocus

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._currentPage = 0
        self._pageCount = 0
        self._displayFormat = "{num} of {total}"

    def createWidget(self, parent):
        w = QSpinBox(parent, buttonSymbols=self.buttonSymbols)
        w.setFocusPolicy(self.focusPolicy)
        self._adjustSpinBox(w)
        if self._currentPage:
            w.setValue(self._currentPage)
        w.valueChanged[int].connect(self.setCurrentPageNumber)
        return w

    def setButtonSymbols(self, buttonSymbols):
        """Set the ``buttonSymbols`` property, and update already existing widgets."""
        self.buttonSymbols = buttonSymbols
        for w in self.createdWidgets():
            w.setButtonSymbols(buttonSymbols)

    def displayFormat(self):
        """Return the currently active display format string."""
        return self._displayFormat

    def setDisplayFormat(self, displayFormat):
        """Set the display format string to use.

        The default is "{num} of {total}".

        """
        assert "{num}" in displayFormat
        if displayFormat != self._displayFormat:
            self._displayFormat = displayFormat
            self._updateDisplay()

    def pageCount(self):
        """Return the currently set page count."""
        return self._pageCount

    def setPageCount(self, pageCount):
        """Set the page count."""
        if pageCount != self._pageCount:
            self._pageCount = pageCount
            if pageCount:
                self._currentPage = max(1, min(self._currentPage, pageCount))
            else:
                self._currentPage = 0
            self._updateDisplay()

    def currentPageNumber(self):
        """Return the current page number."""
        return self._currentPage

    def setCurrentPageNumber(self, num):
        """Set our current page number."""
        if num and num != self._currentPage:
            self.updateCurrentPageNumber(num)
            self.currentPageNumberChanged.emit(num)

    def updateCurrentPageNumber(self, num):
        """Set our current page number, but without emitting the signal."""
        if num and num != self._currentPage:
            self._currentPage = num
            for w in self.createdWidgets():
                w.setValue(num)
                w.lineEdit().deselect()

    def _adjustSpinBox(self, widget):
        """Update the display of the individual spinbox."""
        if self._pageCount:
            if "{num}" in self._displayFormat:
                prefix, suffix = self._displayFormat.split('{num}', 1)
            else:
                prefix, suffix = "", ""
            widget.setSpecialValueText("")
            widget.setRange(1, self._pageCount)
            widget.setSuffix(suffix.format(total=self._pageCount))
            widget.setPrefix(prefix.format(total=self._pageCount))
        else:
            widget.setSpecialValueText(" ")
            widget.setRange(0, 0)
            widget.setSuffix("")
            widget.setPrefix("")
            widget.clear()

    def _updateDisplay(self):
        """Update the display in the pager.

        This is called when the page count or the display format string
        is changed.

        """
        for w in self.createdWidgets():
            self._adjustSpinBox(w)


class ZoomerAction(QWidgetAction):
    """ZoomerAction provides a combobox with view modes and zoom factors."""

    zoomFactorChanged = pyqtSignal(float)
    viewModeChanged = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoomFactor = 1.0
        self._viewMode = FixedScale
        self._viewModes = (
            (FitWidth, "Width"),
            (FitHeight, "Height"),
            (FitBoth, "Page"),
        )
        self._zoomFactors = (
            0.5,
            0.75,
            1.0,
            1.25,
            1.5,
            2.0,
            3.0,
            8.0,
            24.0,
            64.0,
        )
        self._zoomFormat = "{0:.0%}"

    def viewModes(self):
        """Return the view modes that are displayed in the combobox.

        See setViewModes() for explanation.

        """
        return self._viewModes

    def setViewModes(self, modes):
        """Set the view modes to display on top of the zoom values in the box.

        An iterable of tuples (mode, name) is expected; every mode is a
        viewMode, the name is displayed. By default modes 1, 2 and 3 are
        displayed with the names "Width", "Height", "Page".

        """
        self._viewModes = tuple(modes)
        self._setupComboBoxes()

    def zoomFactors(self):
        """Return the zoom factors that are displayed in the combobox.

        A zoom factor of 100% is represented by a floating point value of 1.0.

        """
        return self._zoomFactors

    def setZoomFactors(self, factors):
        """Set the zoom factors to display in the combobox.

        A zoom factor of 100% is represented by a floating point value of 1.0.

        """
        self._zoomFactors = tuple(factors)
        self._setupComboBoxes()

    def zoomFormat(self):
        """Return the format string used to display zoom factors."""
        return self._zoomFormat

    def setZoomFormat(self, zoomFormat):
        """Set the format string used to display zoom factors."""
        self._zoomFormat = zoomFormat
        self._setupComboBoxes()

    def createWidget(self, parent):
        w = QComboBox(parent)
        w.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        w.setEditable(True)
        w.lineEdit().setReadOnly(True)
        w.setFocusPolicy(Qt.NoFocus)
        self._setupComboBox(w)
        self._adjustComboBox(w)
        w.activated[int].connect(self.setCurrentIndex)
        return w

    def viewMode(self):
        """Return the current view mode."""
        return self._viewMode

    def setViewMode(self, mode):
        """Set the current view mode."""
        if mode != self._viewMode:
            self._viewMode = mode
            self.viewModeChanged.emit(mode)
            self._adjustComboBoxes()

    def zoomFactor(self):
        """Return the current zoom factor."""
        return self._zoomFactor

    def setZoomFactor(self, factor):
        """Set the current zoom factor."""
        if factor != self._zoomFactor:
            self._zoomFactor = factor
            self.zoomFactorChanged.emit(factor)
            self._adjustComboBoxes()

    def setCurrentIndex(self, index):
        """Called when the user chooses an entry in a combobox."""
        viewModeCount = len(self._viewModes)
        if index < viewModeCount:
            self.setViewMode(self._viewModes[index][0])
        else:
            self.setZoomFactor(self._zoomFactors[index - viewModeCount])

    def _setupComboBoxes(self):
        """Update the contents and current setting of all comboboxes.

        Called after setting view modes and zoom values.

        """
        for w in self.createdWidgets():
            with util.signalsBlocked(w):
                self._setupComboBox(w)
                self._adjustComboBox(w)

    def _adjustComboBoxes(self):
        """Adjust the current setting (zoom/viewmode) of all comboboxes.

        Called when current zoom or view mode changes.

        """
        for w in self.createdWidgets():
            with util.signalsBlocked(w):
                self._adjustComboBox(w)

    def _setupComboBox(self, w):
        """Put the entries in the (new) QComboBox widget."""
        w.clear()
        for mode, name in self._viewModes:
            w.addItem(name)
        for v in self._zoomFactors:
            w.addItem(self._zoomFormat.format(v))

    def _adjustComboBox(self, w):
        """Select the current index based on our zoomFactor and view mode."""
        for i, (mode, name) in enumerate(self._viewModes):
            if mode == self._viewMode:
                w.setCurrentIndex(i)
                break
        else:
            if self._zoomFactor in self._zoomFactors:
                i = self._zoomFactors.index(self._zoomFactor) + len(self._viewModes)
                w.setCurrentIndex(i)
            else:
                w.setEditText(self._zoomFormat.format(self._zoomFactor))


