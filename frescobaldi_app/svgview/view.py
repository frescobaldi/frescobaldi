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
The SVG view (a QWebView displaying a SVG file).

Interaction between the SVG object and Python is done via a JavaScript bridge
that runs inside the displayed SVG file.

"""

from __future__ import unicode_literals
from __future__ import absolute_import

import os
import sys

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

import app
import util
import textedit
import textformats
import pointandclick
import scratchdir


from . import __path__


def getJsScript(filename):
    """fetch the js file"""
    directory = __path__[0]
    with open(os.path.join(directory, filename), 'r') as fileObject:
        jsValue = fileObject.read()
	return jsValue


class View(QtWebKit.QWebView):
    zoomFactorChanged = QtCore.pyqtSignal(float)
    
    def __init__(self, parent):
        super(View, self).__init__(parent)
        self.jslink = JSLink(self)
        self.loadFinished.connect(self.svgLoaded)
    
    def mainwindow(self):
        return self.parent().mainwindow()
    
    def svgLoaded(self):
        if not self.url().isEmpty():
            frame = self.page().mainFrame()
            frame.addToJavaScriptWindowObject("pyLinks", self.jslink)
            frame.evaluateJavaScript(getJsScript('pointandclick.js'))
            frame.evaluateJavaScript(getJsScript('editsvg.js')) #remove this for stable releases
    
    def clear(self):
        """Empty the View."""
        self.load(QtCore.QUrl())
    
    def zoomIn(self):
        self.setZoomFactor(self.zoomFactor() * 1.1)
        
    def zoomOut(self):
        self.setZoomFactor(self.zoomFactor() / 1.1)
        
    def zoomOriginal(self):
        self.setZoomFactor(1.0)
    
    def setZoomFactor(self, value):
        changed = self.zoomFactor() != value
        super(View, self).setZoomFactor(value)
        if changed:
            self.zoomFactorChanged.emit(self.zoomFactor())


class JSLink(QtCore.QObject):
    """functions to be called from JavaScript
    
    using addToJavaScriptWindowObject
    
    """
    def __init__(self, view):
        super(JSLink, self).__init__()
        self.view = view
        self._highlightFormat = QtGui.QTextCharFormat()
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
        
    def mainwindow(self):
        return self.view.mainwindow()
    
    def readSettings(self):
        """Reads the settings from the user's preferences."""
        color = textformats.formatData('editor').baseColors['selectionbackground']
        color.setAlpha(128)
        self._highlightFormat.setBackground(color)
    
    def document(self, filename, load=False):
        """Get the document with the specified filename.
        
        If load is True, the document is loaded if it wasn't already.
        Also takes scratchdir into account for unnamed or non-local documents.
        
        """
        for d in app.documents:
            s = scratchdir.scratchdir(d)
            if (s.directory() and util.equal_paths(filename, s.path())
                or d.url().toLocalFile() == filename):
                return d
        if load:
            return app.openUrl(QtCore.QUrl.fromLocalFile(filename))
        
    @QtCore.pyqtSlot(str)
    def setCursor(self, url):
        """set cursor in source by clicked textedit link""" 
        t = textedit.link(url)
        if t:
            doc = self.document(t.filename, True)
            cursor = QtGui.QTextCursor(doc)
            b = doc.findBlockByNumber(t.line - 1)
            p = b.position() + t.column
            cursor.setPosition(p)
            mainwindow = self.mainwindow()
            mainwindow.setTextCursor(cursor)
            import widgets.blink
            widgets.blink.Blinker.blink_cursor(mainwindow.currentView())
            mainwindow.activateWindow()
            mainwindow.currentView().setFocus()
        else:
            import helpers
            helpers.openUrl(QtCore.QUrl(url))
	
    @QtCore.pyqtSlot(str)	    
    def hover(self, url):
        """actions when user set mouse over link"""
        t = textedit.link(url)
        if t:
            doc = self.document(t.filename)
            if doc and doc == self.mainwindow().currentDocument():
                cursor = QtGui.QTextCursor(doc)
                b = doc.findBlockByNumber(t.line - 1)
                p = b.position() + t.column
                cursor.setPosition(p)
                cursors = pointandclick.positions(cursor)
                if cursors:
                    import viewhighlighter
                    view = self.mainwindow().currentView()
                    viewhighlighter.highlighter(view).highlight(self._highlightFormat, cursors, 2, 5000)
    
    @QtCore.pyqtSlot(str)	    
    def leave(self, url):
        """actions when user moves mouse off link"""
        import viewhighlighter
        view = self.mainwindow().currentView()
        viewhighlighter.highlighter(view).clear(self._highlightFormat)
        
    @QtCore.pyqtSlot(str)	    
    def pyLog(self, txt):
        """Temporary function. Print to Python console."""
        print(txt)
		
    @QtCore.pyqtSlot(str)	    
    def saveSVG(self, svg_string):
		"""Pass string from JavaScript."""
		pass
		
    
