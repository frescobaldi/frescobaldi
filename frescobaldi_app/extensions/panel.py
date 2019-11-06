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
Base ExtensionPanel for extensions
"""

import panel

from . import ExtensionMixin

class ExtensionPanel(panel.Panel):
    """Base class for an Extension Tool Panel.
    It is a lightweight layer around the regular panel.Panel,
    its only purpose being to act as a bridge to ExtensionWidget and
    descendants.
    """
    def __init__(self, extension, widget_class, dock_area):
        self._extension = extension
        if not issubclass(widget_class, ExtensionMixin):
            raise TypeError(_(
                "Extension panel widget class '{classname}' "
                "is not a subclass of ExtensionMixin.\n"
                "Please derive either from ExtensionWidget "
                "or add extensions.ExtensionMixin as a second base class."
            ).format(classname=widget_class.__name__))
        self._widget_class = widget_class
        super(ExtensionPanel, self).__init__(extension.mainwindow())
        self.hide()
        self.mainwindow().addDockWidget(dock_area, self)

    def createWidget(self):
        """Create the panel's widget.
        *If* an ExtensionPanel is actually instantiated it also has
        information about it's widget class, which we use here.
        If the widget's class is not dre"""
        try:
            w = self._widget_class(self)
            if not hasattr(w, 'extension'):
                w.extension = lambda: self.extension()
            return w
        except Exception as e:
            # If the instantiation of the widget fails we create a nice
            # error message and return an "empty" FailedExtensionWidget instead.
            import sys
            import traceback
            from PyQt5.QtWidgets import QMessageBox
            import appinfo
            from extensions.widget import FailedExtensionWidget

            extension = self.extension()
            info = extension.infos()

            msg_box = QMessageBox()
            msg_box.setWindowTitle(appinfo.appname)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText(_("Extension Tool Panel failed to load"))
            info_text = _(
                "The Tool Panel provided by the extension\n\n  {name}\n\n"
                "failed to load due to an exception. "
                "Please contact the extension's maintainer(s)."
            ).format(name=extension.display_name() or extension.name())
            maintainers = info.get('maintainers', [])
            for m in maintainers:
                info_text += "\n  - {}".format(m)
            msg_box.setInformativeText(info_text)
            exc_info = sys.exc_info()
            msg_box.setDetailedText(
                ' '.join(traceback.format_exception(*exc_info)))
            msg_box.exec()

            return FailedExtensionWidget(self)

    def translateUI(self):
        self.setWindowTitle(self.extension().display_name())

    def extension(self):
        return self._extension

    def settings(self):
        return self.extension().settings()
