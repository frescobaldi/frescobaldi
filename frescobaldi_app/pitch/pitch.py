# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Various tools to edit pitch of selected music.

All use the tools in ly.pitch.

"""

from __future__ import unicode_literals

import re

from PyQt4.QtGui import QMessageBox

import app
import icons
import qutil
import lydocument
import documentinfo
import lilypondinfo
import inputdialog
import ly.pitch.translate
import ly.pitch.transpose
import ly.pitch.rel2abs
import ly.pitch.abs2rel


def changeLanguage(cursor, language):
    """Changes the language of the pitch names."""
    c = lydocument.cursor(cursor, select_all=True)
    try:
        with qutil.busyCursor():
            changed = ly.pitch.translate.translate(c, language)
    except ly.pitch.PitchNameNotAvailable:
        QMessageBox.critical(None, app.caption(_("Pitch Name Language")), _(
            "Can't perform the requested translation.\n\n"
            "The music contains quarter-tone alterations, but "
            "those are not available in the pitch language \"{name}\"."
            ).format(name=language))
        return
    if changed:
        return
    if not cursor.hasSelection():
        # there was no selection and no language command, so insert one
        version = (documentinfo.docinfo(cursor.document()).version()
                   or lilypondinfo.preferred().version())
        ly.pitch.translate.insert_language(c.document, language, version)
        return
    # there was a selection but no command, user must insert manually.
    QMessageBox.information(None, app.caption(_("Pitch Name Language")),
        '<p>{0}</p>'
        '<p><code>\\include "{1}.ly"</code> {2}</p>'
        '<p><code>\\language "{1}"</code> {3}</p>'.format(
            _("The pitch language of the selected text has been "
                "updated, but you need to manually add the following "
                "command to your document:"),
            language,
            _("(for LilyPond below 2.14), or"),
            _("(for LilyPond 2.14 and higher.)")))


def rel2abs(cursor):
    """Converts pitches from relative to absolute."""
    with qutil.busyCursor():
        c = lydocument.cursor(cursor, select_all=True)
        ly.pitch.rel2abs.rel2abs(c)


def abs2rel(cursor):
    """Converts pitches from absolute to relative."""
    with qutil.busyCursor():
        c = lydocument.cursor(cursor, select_all=True)
        ly.pitch.abs2rel.abs2rel(c)


def getTransposer(document, mainwindow):
    """Show a dialog and return the desired transposer.
    
    Returns None if the dialog was cancelled.
    
    """
    language = documentinfo.docinfo(document).language() or 'nederlands'
    
    def readpitches(text):
        """Reads pitches from text."""
        result = []
        for pitch, octave in re.findall(r"([a-z]+)([,']*)", text):
            r = ly.pitch.pitchReader(language)(pitch)
            if r:
                result.append(ly.pitch.Pitch(*r, octave=ly.pitch.octaveToNum(octave)))
        return result
    
    def validate(text):
        """Returns whether the text contains exactly two pitches."""
        return len(readpitches(text)) == 2
    
    text = inputdialog.getText(mainwindow, _("Transpose"), _(
        "Please enter two absolute pitches, separated by a space, "
        "using the pitch name language \"{language}\"."
        ).format(language=language), icon = icons.get('tools-transpose'),
        help = "transpose", validate = validate)
    
    if text:
        return ly.pitch.transpose.Transposer(*readpitches(text))


def getModalTransposer(document, mainwindow):
    """Show a dialog and return the desired modal transposer.
    
    Returns None if the dialog was cancelled.
    
    """
    language = documentinfo.docinfo(document).language() or 'nederlands'
    
    def readpitches(text):
        """Reads pitches from text."""
        result = []
        for pitch, octave in re.findall(r"([a-z]+)([,']*)", text):
            r = ly.pitch.pitchReader(language)(pitch)
            if r:
                result.append(ly.pitch.Pitch(*r, octave=ly.pitch.octaveToNum(octave)))
        return result
    
    def validate(text):
        """Returns whether the text is an integer followed by the name of a key."""
        words = text.split()
        if len(words) != 2:
            return False
        try:
            steps = int(words[0])
            keyIndex = ly.pitch.transpose.ModalTransposer.getKeyIndex(words[1])
            return True
        except ValueError:
            return False
    
    text = inputdialog.getText(mainwindow, _("Transpose"), _(
        "Please enter the number of steps to alter by, followed by a key signature. (i.e. \"5 F\")"
        ), icon = icons.get('tools-transpose'),
        help = "modal_transpose", validate = validate)
    if text:
        words = text.split()
        return ly.pitch.transpose.ModalTransposer(int(words[0]), ly.pitch.transpose.ModalTransposer.getKeyIndex(words[1]))

    
def transpose(cursor, transposer, mainwindow=None):
    """Transpose pitches using the specified transposer."""
    c = lydocument.cursor(cursor, select_all=True)
    try:
        with qutil.busyCursor():
            ly.pitch.transpose.transpose(c, transposer)
    except ly.pitch.PitchNameNotAvailable as e:
        QMessageBox.critical(mainwindow, app.caption(_("Transpose")), _(
            "Can't perform the requested transposition.\n\n"
            "The transposed music would contain quarter-tone alterations "
            "that are not available in the pitch language \"{language}\"."
            ).format(language = e.language))


