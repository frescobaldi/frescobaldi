# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
A LilyPondJob runs LilyPond and captures the output
to get it later or to have a log follow it.
"""

import codecs
import os

from PyQt5.QtCore import QSettings

import documentinfo
from . import Job
import lilypondinfo


def lilypondInfo(document):
    """Returns a LilyPondInfo instance that should be used by default to engrave the document."""
    version = documentinfo.docinfo(document).version()
    if version and QSettings().value("lilypond_settings/autoversion", False, bool):
        return lilypondinfo.suitable(version)
    return lilypondinfo.preferred()


class LilyPondJob(Job):
    """Manages a LilyPond process.

    This class performs basic configuration that is required
    for any *LilyPond* job as compared to a generic job.

    Options are set to default values based on Preferences,
    if a document is passed, the respective values are set too.

    """

    def __init__(self, document, args=None):
        super(LilyPondJob, self).__init__()
        self.document = document
        self.backend_args = []
        self.additional_args = args if args else []
        self.filename, self.includepath = (
            documentinfo.info(document).jobinfo(True) if document
            else ('', [])
        )
        self.lilypondinfo = lilypondInfo(document)
        self.environment['LD_LIBRARY_PATH'] = self.lilypondinfo.libdir()
        self.command = [self.lilypondinfo.abscommand() or self.lilypondinfo.command]
        self.decode_errors = 'replace'  # codecs error handling
        self.d_options = {}

        # Set default values from Preferences
        s = QSettings()
        s.beginGroup("lilypond_settings")
        self.d_options['delete-intermediate-files'] = s.value(
            "delete_intermediate_files", True, bool)
        self.default_output_target = s.value(
            "default_output_target", "pdf", str)

        self.embed_source_code = s.value("embed_source_code", False, bool)

        if s.value("no_translation", False, bool):
            self.environment['LANG'] = 'C'
            self.environment['LC_ALL'] = 'C'
        self.set_title("{0} {1} [{2}]".format(
            os.path.basename(self.lilypondinfo.command),
            self.lilypondinfo.versionString(), document.documentName()))
        self.directory = os.path.dirname(self.filename)

    def configure_command(self):
        """Compose the command line for a LilyPond job using all options."""
        cmd = self.command

        for key in self.d_options:
            cmd.append('-d{}{}'.format(
                '' if self.d_options[key] else 'no-', key))
        cmd.extend(self.additional_args)
        cmd.extend(self.paths(self.includepath))

        # Specify target/backend
        if not self.backend_args:
            # no specific backend selected
            if self.default_output_target == "svg":
                # engrave to SVG
                self.backend_args.append('-dbackend=svg')
            else:
                # engrave to PDF
                if not self.additional_args:
                    # publish mode
                    if self.embed_source_code and self.lilypond_version >= (2, 19, 39):
                        self.backend_args.append('-dembed-source-code')
                self.backend_args.append('--pdf')
        cmd.extend(self.backend_args)

        # Input file
        cmd.append(self.filename)

    def create_decoder(self, channel):
        """Return a decoder for the given channel (STDOUT/STDERR).

        This method produces the default 'utf-8' decoders for LilyPond jobs
        and is called from the constructor. Decoders can be set manually
        by setting the `decoder_stdout` and `decoder_stderr` manually after
        construction.

        This decoder is then used to decode the 8bit bytestrings into Python
        unicode strings.

        """
        return codecs.getdecoder('utf-8')

    def paths(self, includepath):
        """Ensure paths have trailing slashes for Windows compatibility."""
        result = []
        for path in includepath:
            result.append('-I' + path.rstrip('/') + '/')
        return result


class PreviewJob(LilyPondJob):
    """Represents a LilyPond Job in Preview mode."""

    def __init__(self, document, args=None):
        super(PreviewJob, self).__init__(document, args)
        self.d_options['point-and-click'] = True


class PublishJob(LilyPondJob):
    """Represents a LilyPond Job in Publish mode."""

    def __init__(self, document, args=None):
        super(PublishJob, self).__init__(document, args)
        self.d_options['point-and-click'] = False


class LayoutControlJob(LilyPondJob):
    """Represents a LilyPond Job in Layout Control mode."""

    def __init__(self, document, args=None):
        super(LayoutControlJob, self).__init__(document, args)
        # So far no further code is necessary
