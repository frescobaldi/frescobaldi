# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
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
Import and export of snippets.
"""

from __future__ import unicode_literals

import sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import widgets.dialog

from . import model
from . import snippets
from . import builtin


def save(names, filename):
    """Saves the named snippets to a file."""
    root = ET.Element('snippets')
    root.text = root.tail = '\n'
    d = ET.ElementTree(root)
    
    for name in names:
        snippet = ET.Element('snippet')
        snippet.set('id', name)
        snippet.text = snippet.tail = '\n'
        
        title = ET.Element('title')
        title.text = snippets.title(name, False)
        title.tail = '\n'
        
        shortcuts = ET.Element('shortcuts')
        ss = model.shortcuts(name)
        if ss:
            shortcuts.text = '\n'
            for s in ss:
                shortcut = ET.Element('shortcut')
                shortcut.text = s.toString()
                shortcut.tail = '\n'
                shortcuts.append(shortcut)
        shortcuts.tail = '\n'
        
        body = ET.Element('body')
        body.text = snippets.text(name)
        body.tail = '\n'
        
        snippet.append(title)
        snippet.append(shortcuts)
        snippet.append(body)
        root.append(snippet)
    d.write(filename, "UTF-8")


def load(filename, widget):
    """Loads snippets from a file, displaying them in a list.
    
    The user can then choose:
    - overwrite builtin snippets or not
    - overwrite own snippets with same title or not
    - select and view snippets contents.
    
    """
    try:
        d = ET.parse(filename)
        elements = list(d.findall('snippet'))
        if not elements:
            raise ValueError(_("No snippets found."))
    except Exception as e:
        QMessageBox.critical(widget, app.caption(_("Error")),
        _("Can't load {url}\n\n{error}").format(
            url=filename, error=e))
        return


    dlg = widgets.dialog.Dialog(widget)
    dlg.setWindowTitle(app.caption(_("dialog title", "Import Snippets")))
    dlg.setMessage(_("Choose which snippets you want to import:"))
    tree = QTreeWidget(headerHidden=True, rootIsDecorated=False)
    dlg.setMainWidget(tree)
    
    allnames = frozenset(snippets.names())
    builtins = frozenset(builtin.builtin_snippets)
    titles = dict((snippets.title(n), n) for n in allnames if n not in builtins)
    
    new = QTreeWidgetItem(tree, [_("New Snippets")])
    updated = QTreeWidgetItem(tree, [_("Updated Snippets")])
    unchanged = QTreeWidgetItem(tree, [_("Unchanged Snippets")])
    
    new.setFlags(Qt.ItemIsEnabled)
    updated.setFlags(Qt.ItemIsEnabled)
    unchanged.setFlags(Qt.ItemIsEnabled)
    
    new.setExpanded(True)
    updated.setExpanded(True)
    
    for snip in elements:
        item = QTreeWidgetItem()
        
        body = snip.find('body').text
        t = snippets.parse(body)
        title = snip.find('title').text or snippets.maketitle(t.text)
        item.setText(0, title)
        
        name = snip.get('id')
        name = name if name in builtins else None
        
        # determine if new, updated or unchanged
        if not name:
            name = titles.get(title)
        item.name = name
        
        if not name or name not in allnames:
            new.addChild(item)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
        elif name:
            if body != snippets.text(name):
                updated.addChild(item)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked)
            else:
                unchanged.addChild(item)
                item.setFlags(Qt.ItemIsEnabled)
    # count:
    for i in new, updated, unchanged:
        i.setText(0, i.text(0) + " ({0})".format(i.childCount()))
    for i in new, updated:
        if i.childCount():
            i.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            i.setCheckState(0, Qt.Checked)
    
    def changed(item):
        if item in (new, updated):
            for i in range(item.childCount()):
                c = item.child(i)
                c.setCheckState(0, item.checkState(0))
            
    tree.itemChanged.connect(changed)
    
    importShortcuts = QTreeWidgetItem([_("Import Keyboard Shortcuts")])
    if new.childCount() or updated.childCount():
        tree.addTopLevelItem(importShortcuts)
        importShortcuts.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        importShortcuts.setCheckState(0, Qt.Unchecked)
    
        
    dlg.exec_()
    
    