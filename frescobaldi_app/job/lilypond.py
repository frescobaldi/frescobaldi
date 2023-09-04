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
import glob
import os
import shutil
import sys

from PyQt5.QtCore import QSettings, QUrl

import ly.document
import ly.docinfo

import document
import documentinfo
from . import Job
import lilypondinfo
import util


def parse_d_option(token):
    """Parse a -d option into its bare name and a Boolean value. For example
    '-dno-point-and-click' will be parsed into 'point-and-click' and False
    """
    token = token[2:]
    value = True
    if token.startswith('no-'):
        token = token[3:]
        value = False
    return token, value


def serialize_d_options(d_options, ordered=False):
    """Compose an (un)ordered list of -d options in their actual
    command line syntax."""
    result = []
    keys = sorted(d_options.keys()) if ordered else d_options.keys()
    for key in keys:
        result.append('-d{}{}'.format(
            '' if d_options[key] else 'no-', key))
    return result


class LilyPondJob(Job):
    """Manages a LilyPond process.

    In addition to the generic functionality of the job.Job class
    this class performs basic LilyPond-related configuration.

    The job always works on a *LilyPond* document, which is passed to
    LilyPond as the last command line argument. This is different from
    the way the generic Job class works.

    LilyPond Preferences are used as default values but can be overwritten
    before calling start().

    Code using the LilyPondJob class or its descendants doesn't explicitly
    deal with the 'command' list. Instead properties are set and options
    added from which the command line is implicitly composed in
    configure_command().

    """

    def __init__(self, doc, args=None, title=""):
        """Create a LilyPond job by first retrieving some context
        from the document and feeding this into job.Job's __init__()."""
        if isinstance(doc, QUrl):
            doc = document.Document(doc)
        self.document = doc
        self.document_info = docinfo = documentinfo.info(doc)
        self.lilypond_info = docinfo.lilypondinfo()
        self._d_options = {}
        self._backend_args = []
        input, self.includepath = docinfo.jobinfo(True)
        directory = os.path.dirname(input)

        super().__init__(
                encoding='utf-8',
                args=args,
                input=input,
                decode_errors='replace',
                directory=directory,
                environment=(
                    {'LD_LIBRARY_PATH': libdir}
                    if (libdir := self.lilypond_info.libdir())
                    else {}),
                title=title,
                priority=2)

        # Set default values from Preferences
        s = QSettings()
        s.beginGroup("lilypond_settings")
        self.set_d_option('delete-intermediate-files',
            s.value("delete_intermediate_files", True, bool))
        self.default_output_target = s.value(
            "default_output_target", "pdf", str)
        self.embed_source_code = s.value("embed_source_code", False, bool)
        if s.value("no_translation", False, bool):
            self.environment['LC_MESSAGES'] = 'C'
        self.set_title("{} {} [{}]".format(
            os.path.basename(self.lilypond_info.command),
            self.lilypond_info.versionString(), doc.documentName()))

    def add_additional_arg(self, arg):
        """Append an additional command line argument if it is not
        present already."""
        if not arg in self._additional_args:
            self._additional_args.append(arg)

    def add_include_path(self, path):
        """Manually add an include path to the current job."""
        self.includepath.append(path)

    def additional_args(self):
        """Additional (custom) arguments, will be inserted between
        the -d options and the include paths. May for example stem
        from the manual part of the Engrave Custom dialog."""
        return self._additional_args

    def backend_args(self):
        """Determine the target/backend type and produce appropriate args."""
        result = self._backend_args
        if not result:
            # no specific backend selected
            if self.default_output_target == "svg":
                # engrave to SVG
                result.append('-dbackend=svg')
            else:
                # engrave to PDF
                if not self.arguments():
                    # publish mode
                    if self.embed_source_code and self.lilypond_info.version() >= (2, 19, 39):
                        result.append('-dembed-source-code')
                result.append('--pdf')
        return result

    def configure_command(self):
        """Compose the command line for a LilyPond job using all options.
        Individual steps may be overridden in subclasses."""
        self.command = cmd = (
            [self.lilypond_info.abscommand() or self.lilypond_info.command])
        cmd.extend(serialize_d_options(self._d_options))
        cmd.extend(self.arguments())
        cmd.extend(self.paths(self.includepath))
        cmd.extend(self.backend_args())
        self.set_input_file()

    def d_option(self, key):
        return self._d_options.get(key, None)

    def paths(self, includepath):
        """Ensure paths have trailing slashes for Windows compatibility."""
        result = []
        for path in includepath:
            result.append('-I' + path.rstrip('/') + '/')
        return result

    def set_backend_args(self, args):
        self._backend_args = args

    def set_d_option(self, key, value=True):
        self._d_options[key] = value


class PreviewJob(LilyPondJob):
    """Represents a LilyPond Job in Preview mode."""

    def __init__(self, document, args=None, title=""):
        super().__init__(document, args, title)
        self.set_d_option('point-and-click', True)


class PublishJob(LilyPondJob):
    """Represents a LilyPond Job in Publish mode."""

    def __init__(self, document, args=None, title=""):
        super().__init__(document, args, title)
        self.set_d_option('point-and-click', False)


class LayoutControlJob(LilyPondJob):
    """Represents a LilyPond Job in Layout Control mode."""

    def __init__(self, document, args=None, title=""):
        super().__init__(document, args, title)
        # So far no further code is necessary


class VolatileTextJob(PublishJob):
    """Represents a 'volatile' LilyPond Job where the document
    is only passed in as a string. Internally a document is created
    in a temporary file, and options set to not use point-and-click.
    base_dir can be used to add a 'virtual' document Directory
    in order to use relative includes.
    """
    def __init__(
        self, text, title=None, base_dir=None):
        # TODO: ???
        #       I have the impression this "info" stuff
        #       is not used at all. And *if* it is used,
        #       shouldn't it be implemented in LilyPondJob???
        # Initialize default LilyPond version
        info = lilypondinfo.preferred()
        # Optionally infer a suitable LilyPond version from the content
        if QSettings().value("lilypond_settings/autoversion", True, bool):
            version = ly.docinfo.DocInfo(ly.document.Document(text, 'lilypond')).version()
            if version:
                info = lilypondinfo.suitable(version)
        # Create temporary (document.Document object and file)
        self.directory = util.tempdir()
        filename = os.path.join(self.directory, 'document.ly')
        with open(filename, 'wb') as f:
            f.write(text.encode('utf-8'))
        url = QUrl(filename)
        url.setScheme('file')
        super().__init__(url, title=title)

        if title:
            self.set_title(title)
        if base_dir:
            self.add_include_path(base_dir)

    def resultfiles(self):
        """Returns a list of resulting file(s)"""
        #TODO: Support non-PDF compilation modes
        return glob.glob(os.path.join(self.directory, '*.pdf'))

    def cleanup(self):
        shutil.rmtree(self.directory, ignore_errors=True)


class CachedPreviewJob(PublishJob):
    """Represents a cached example LilyPond Job where the document
    is only passed in as a string. Internally a document is created
    in a cached file, and options set to not use point-and-click.
    The filename is generated as the md5 hash of the passed text, and
    the compilation is only started if a corresponding file has not
    been compiled yet.
    If a target_dir is given it is used (for example to allow persistent
    caching), otherwise an autogenerated temporary directory is used
    (and deleted upon program termination).
    base_dir can be used to add a 'virtual' document Directory
    in order to use relative includes from the 'current document'.
    """

    _target_dir = util.tempdir()

    def __init__(
        self, text, target_dir=None, title=None, base_dir=None
    ):
        import hashlib
        md = hashlib.md5()
        md.update(text.encode('utf-8'))
        self.hash_name = md.hexdigest()
        self.base_name = self.hash_name + '.ly'
        self.target_dir = target_dir or self._target_dir
        filename = os.path.join(self.target_dir, self.base_name)
        if os.path.exists(os.path.join(
            self.target_dir,
            self.hash_name + '.pdf')
        ):
            self._needs_compilation = False
        else:
            with open(filename, 'wb') as f:
                f.write(text.encode('utf-8'))
            self._needs_compilation = True
        url = QUrl(filename)
        url.setScheme('file')
        super().__init__(url, title=title)
        self.done.connect(self.remove_intermediate)

        if title:
            self.set_title(title)
        if base_dir:
            self.add_include_path(base_dir)

    def cleanup(self):
        """Do *not* remove the generated files."""
        pass

    def needs_compilation(self):
        return self._needs_compilation

    def remove_intermediate(self):
        """Remove all files from the compilation except
        the (main) .pdf and the .ly files."""
        dir = self.target_dir
        files = os.listdir(dir)
        hash_name = self.hash_name
        keep = [hash_name + '.ly', hash_name + '.pdf']
        for f in files:
            if f.startswith(hash_name) and f not in keep:
                os.remove(os.path.join(dir, f))

    def resultfiles(self):
        """
        Returns a single result file, wrapped in a list.
        This for example prevents system-wise files from
        lilypond-book-preamble to clutter the preview.
        """
        #TODO: Support non-PDF compilation modes
        output_name, _ = os.path.splitext(self.base_name)
        resultfile = os.path.join(self.directory(), output_name + '.pdf')
        if os.path.exists(resultfile):
            return [resultfile]
        else:
            return []

    def start(self):
        """Override the Job start, using cached PDF if possible."""
        if self.needs_compilation():
            super().start()
        else:
            self.done("cached")
