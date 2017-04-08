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
Import and export of snippets.
"""


import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMessageBox, QTreeWidget, QTreeWidgetItem

import app
import appinfo
import qutil
import userguide
import widgets.dialog

from . import model
from . import snippets
from . import builtin


def save(names, filename):
    """Saves the named snippets to a file."""
    root = ET.Element('snippets')
    root.text = '\n\n'
    root.tail = '\n'
    d = ET.ElementTree(root)

    comment = ET.Comment(_comment.format(appinfo=appinfo))
    comment.tail = '\n\n'
    root.append(comment)

    for name in names:
        snippet = ET.Element('snippet')
        snippet.set('id', name)
        snippet.text = '\n'
        snippet.tail = '\n\n'

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
        _("Can't read from source:\n\n{url}\n\n{error}").format(
            url=filename, error=e))
        return


    dlg = widgets.dialog.Dialog(widget)
    dlg.setWindowModality(Qt.WindowModal)
    dlg.setWindowTitle(app.caption(_("dialog title", "Import Snippets")))
    tree = QTreeWidget(headerHidden=True, rootIsDecorated=False)
    dlg.setMainWidget(tree)
    userguide.addButton(dlg.buttonBox(), "snippet_import_export")

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

    items = []
    for snip in elements:
        item = QTreeWidgetItem()

        item.body = snip.find('body').text
        item.title = snip.find('title').text
        item.shortcuts = list(e.text for e in snip.findall('shortcuts/shortcut'))

        title = item.title or snippets.maketitle(snippets.parse(item.body).text)
        item.setText(0, title)

        name = snip.get('id')
        name = name if name in builtins else None


        # determine if new, updated or unchanged
        if not name:
            name = titles.get(title)
        item.name = name

        if not name or name not in allnames:
            new.addChild(item)
            items.append(item)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
        elif name:
            if (item.body != snippets.text(name)
                or title != snippets.title(name)
                or (item.shortcuts and item.shortcuts !=
                    [s.toString() for s in model.shortcuts(name) or ()])):
                updated.addChild(item)
                items.append(item)
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
    if items:
        tree.addTopLevelItem(importShortcuts)
        importShortcuts.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        importShortcuts.setCheckState(0, Qt.Checked)
        dlg.setMessage(_("Choose which snippets you want to import:"))
    else:
        dlg.setMessage(_("There are no new or updated snippets in the file."))
        unchanged.setExpanded(True)

    tree.setWhatsThis(_(
        "<p>Here the snippets from {filename} are displayed.</p>\n"
        "<p>If there are new or updated snippets, you can select or deselect "
        "them one by one, or all at once, using the checkbox of the group. "
        "Then click OK to import all the selected snippets.</p>\n"
        "<p>Existing, unchanged snippets can't be imported.</p>\n"
        ).format(filename=os.path.basename(filename)))

    qutil.saveDialogSize(dlg, "snippettool/import/size", QSize(400, 300))
    if not dlg.exec_() or not items:
        return
    ac = model.collection()
    m = model.model()
    with qutil.busyCursor():
        for i in items:
            if i.checkState(0) == Qt.Checked:
                index = m.saveSnippet(i.name, i.body, i.title)
                if i.shortcuts and importShortcuts.checkState(0):
                    shortcuts = list(map(QKeySequence.fromString, i.shortcuts))
                    ac.setShortcuts(m.name(index), shortcuts)
        widget.updateColumnSizes()


_comment = """
  Created by {appinfo.appname} {appinfo.version}.

  Every snippet is represented by:
    title:      title text
    shortcuts:  list of shortcut elements, every shortcut is a key sequence
    body:       the snippet text

  The snippet id attribute can be the name of a builtin snippet or a random
  name like 'n123456'. In the latter case, the title is used to determine
  whether a snippet is new or updated.
"""


