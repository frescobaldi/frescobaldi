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
The GraphicsScene for the SVG view.
"""

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtWebKit import QGraphicsWebView

import textedit

def getJsScript(filename):
	"""fetch the js file"""
	fileObject = open('frescobaldi_app/svgview/'+filename,'r')
	jsValue = fileObject.read()
	fileObject.close
	return jsValue

class SvgScene(QtGui.QGraphicsScene):
    def __init__(self):
        super(QtGui.QGraphicsScene, self).__init__()
        self._doc = None
        self._mainwindow = None
        self.view = QtGui.QGraphicsView(self)
        self.webview = QGraphicsWebView()
        self.webview.setFlags(QtGui.QGraphicsItem.ItemClipsToShape)
        self.webview.setCacheMode(QtGui.QGraphicsItem.NoCache)
        self.addItem(self.webview)

        self.webview.loadFinished.connect(self.svgLoaded)
        
    def setDoc(self, doc, mainwindow):
		self._doc = doc
		self._mainwindow = mainwindow

    def svgLoaded(self):
        frame = self.webview.page().mainFrame()
        fsize = frame.contentsSize()
        self.webview.resize(QtCore.QSizeF(fsize))
        self.view.resize(fsize.width() + 10, fsize.height() + 10)

        self.links = JSLink()
        self.links.setDocument(self._doc, self._mainwindow)
        frame.addToJavaScriptWindowObject("pyLinks", self.links)
        frame.evaluateJavaScript(getJsScript('pointandclick.js'))
        
    def toolTipText(self, txt):
		self.webview.setToolTip(txt)

class JSLink(QtCore.QObject):
    """functions to be called from JavaScript
    
    using addToJavaScriptWindowObject
    
    """
    
    def setDocument(self, doc, mainwindow):
	    """set document and mainwindow"""
	    self.doc = doc
	    self.mainwindow = mainwindow    
    
    @QtCore.pyqtSlot(str)
    def setCursor(self, url):
	    """set cursor in source by clicked textedit link""" 
	    t = textedit.link(url)
	    filename = self.doc.url().toLocalFile()
	    if t and t.filename == filename:
		    if not self.doc is self.mainwindow.currentDocument():
			    self.mainwindow.setCurrentDocument(self.doc)			
		    b = self.doc.findBlockByNumber(t.line - 1)
		    p = b.position() + t.column
		    cursor = self.mainwindow.textCursor()
		    cursor.clearSelection()
		    cursor.setPosition(p)
		    self.mainwindow.setTextCursor(cursor)		    
	
    @QtCore.pyqtSlot(str)	    
    def hover(self, url):
	    """actions when user set mouse over link"""
	    #TODO: implement highlighting in code when user hovers a link
	    pass
	    
    @QtCore.pyqtSlot(str)	    
    def pyLog(self, txt):
	    """Temporary function. Print to Python console."""
	    print txt
		
    
    
