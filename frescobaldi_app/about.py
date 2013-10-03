# -*- coding: utf-8 -*-
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
About dialog.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import QSettings, QSize, Qt, QUrl
from PyQt4.QtGui import (
    QDialog, QDialogButtonBox, QLabel, QLayout, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget)

import app
import info
import icons
import helpers
import bugreport
import language_names
import po.setup

def credits():
    """Iterating over this should return paragraphs for the credits page."""
    yield _(
        "{appname} is written in {python} and uses the {qt} toolkit.").format(
        appname=info.appname,
        # L10N: the Python programming language
        python='<a href="http://www.python.org/">{0}</a>'.format(_("Python")),
        # L10N: the Qt4 application framework
        qt='<a href="http://qt.nokia.com/">{0}</a>'.format(_("Qt4")))
    yield _(
        "The Music View is powered by the {poppler} library by "
        "{authors} and others.").format(
        poppler='<a href="http://poppler.freedesktop.org/">{0}</a>'.format(
            # L10N: the Poppler PDF library
            _("Poppler")),
        authors='Kristian Høgsberg, Albert Astals Cid')
    yield _(
        "Most of the bundled icons are created by {tango}.").format(
        tango='<a href="http://tango.freedesktop.org/">{0}</a>'.format(_(
            "The Tango Desktop Project")))
    
    yield _("The following people contributed to {appname}:").format(
        appname=info.appname)
    
    # list other credits here
    def author(name, *contributions):
        return "{author}: {contributions}".format(
            author = name,
            contributions = ", ".join(contributions))
            
    yield author("Richard Cognot", 
        _("Kinetic Scrolling for the Music View"),
        )
    
    yield author("Nicolas Malarmey",
        _("Improved highlighting and auto-completion of Scheme code"),
		)
	
    yield author("Urs Liska",
        _("Preview modes"),
        _("Various contributions"),
		)
	
    yield author("Christopher Bryan",
        _("Modal Transpose"),
        )
	
    yield author("Peter Bjuhr",
        _("Quick Insert buttons for grace notes"),
        _("MusicXML import"),
        )
	
    # translations
    yield _(
        "{appname} is translated into the following languages:").format(
        appname=info.appname)
    lang = QSettings().value("language", "", type("")) or po.setup.current() or None
    langs = [(language_names.languageName(code, lang), names)
             for code, names in info.translators.items()]
    for lang, names in sorted(langs):
        yield lang + ": " + (', '.join(names))


class AboutDialog(QDialog):
    """A simple 'About Frescobaldi' dialog.
    
    Most of the information is taken from the info module.
    
    """
    def __init__(self, mainwindow):
        """Creates the about dialog. You can simply exec_() it."""
        super(AboutDialog, self).__init__(mainwindow)
        
        self.setWindowTitle(_("About {appname}").format(appname = info.appname))
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        tabw = QTabWidget()
        layout.addWidget(tabw)
        
        tabw.addTab(About(self), _("About"))
        tabw.addTab(Credits(self), _("Credits"))
        tabw.addTab(Version(self), _("Version"))
        
        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.setCenterButtons(True)
        button.accepted.connect(self.accept)
        layout.addWidget(button)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        

class About(QWidget):
    """About widget."""
    def __init__(self, parent=None):
        super(About, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        size = QSize(100, 100)
        pic = QLabel()
        pic.setPixmap(icons.get("frescobaldi").pixmap(size))
        pic.setFixedSize(size)
        layout.addWidget(pic, 0, Qt.AlignHCenter)

        text = QLabel()
        text.setText(html())
        text.linkActivated.connect(self.openLink)
        layout.addWidget(text)
    
    def openLink(self, url):
        helpers.openUrl(QUrl(url))


class Credits(QTextBrowser):
    """Credits widget."""
    def __init__(self, parent=None):
        super(Credits, self).__init__(parent)
        self.setOpenLinks(False)
        self.anchorClicked.connect(helpers.openUrl)
        self.setHtml('\n'.join(map('<p>{0}</p>'.format, credits())))


class Version(QTextBrowser):
    """Version information."""
    def __init__(self, parent=None):
        super(Version, self).__init__(parent)
        self.setHtml(
            "<p>{app_name}: {app_version}</p>\n"
            "<p>Python: {python_version}<br />"
            "Qt: {qt_version}<br />\n"
            "PyQt4: {pyqt_version}<br />\n"
            "sip: {sip_version}</p>\n"
            "<p>{operating_system}:<br />\n"
            "{osname}</p>".format(
                app_name = info.appname,
                app_version = info.version,
                operating_system = _("Operating System"),
                **bugreport.versionInfo()))


def html():
    """Returns a HTML string for the about dialog."""
    appname = info.appname
    version = _("Version {version}").format(version = info.version)
    description = _("A LilyPond Music Editor")
    copyright = _("Copyright (c) {year} by {author}").format(
        year = "2008-2012",
        author = """<a href="mailto:{0}" title="{1}">{2}</a>""".format(
            info.maintainer_email,
            _("Send an e-mail message to the maintainers."),
            info.maintainer))
    # L10N: Translate this sentence and fill in your own name to have it appear in the About Dialog.
    translator = _("Translated by Your Name.")
    if translator == "Translated by Your Name.":
        translator = ""
    else:
        translator = "<p>{0}</p>".format(translator)
    license = _("Licensed under the {gpl}.").format(
        gpl = """<a href="http://www.gnu.org/licenses/gpl.html">GNU GPL</a>""")
    homepage = info.url
    
    return html_template.format(**locals())


html_template = """<html>
<body><div align="center">
<h1>{appname}</h1>
<h3>{version}</h3>
<p>{description}</p>
<p>{copyright}</p>
{translator}
<p>{license}</p>
<p><a href="{homepage}">{homepage}</a></p>
</div></body>
</html>
"""

