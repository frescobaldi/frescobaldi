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
A LilyPondJob runs LilyPond,
with specific subclasses
- PreviewJob        Run LilyPond in "Preview" mode
- PublishJob        Run LilyPond in "Publish" mode (without point-and-click)
- LayoutControlJob  Run LilyPond in "Layout Control" mode
- VolatileTextJob   Run LilyPond with a string as "document" input
                    and a temporary output file
- CachedPreviewJob  Run LilyPond with a string but cached output
"""

import codecs
import glob
import os
import shutil

from PyQt5.QtCore import (
    QSettings,
    QUrl
)

import ly.document
import ly.docinfo

import document
import documentinfo
import layoutcontrol
import lilypondinfo
import util

from . import Job


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
    """Compose an unordered list of -d options in their actual
    command line syntax."""
    return ['-d{}{}'.format(
        '' if d_options[key] else 'no-',
        key
    ) for key in d_options.keys()]


class LilyPondJob(Job):
    """Manages a LilyPond process.

    In addition to the generic functionality of the job.Job class
    this class performs basic LilyPond-related configuration.

    The job always works on a *LilyPond* document, which can be passed
    as a document.Document instance or as a QUrl.

    LilyPond Preferences are used as default values but can be overwritten
    before calling start().

    Code using the LilyPondJob class or its descendants doesn't explicitly
    deal with the 'command' list. Instead properties are set and options
    added from which the command line is implicitly composed in
    _configure_command().

    """

    def __init__(self, doc, **kwargs):
        """Create a LilyPond job by first retrieving some context
        from the document and feeding this into job.Job's __init__()."""

        # Determine the general process-related information
        if isinstance(doc, QUrl):
            doc = document.Document(doc)
        self.document = doc
        self.document_info = docinfo = documentinfo.info(doc)
        self.lilypond_info = kwargs.get('info', docinfo.lilypondinfo())
        input, self._includepath = docinfo.jobinfo(True)
        directory = os.path.dirname(input)
        environment = kwargs.get('environment', {})
        environment['LD_LIBRARY_PATH'] = self.lilypond_info.libdir()
        title = kwargs.get(
            'title',
            '{0} {1} [{2}]'.format(
                os.path.basename(self.lilypond_info.command),
                self.lilypond_info.versionString(), doc.documentName()
            ))


        # initialize the Job basics
        super(LilyPondJob, self).__init__(
            parent=kwargs.get('parent', None),
            encoding='utf-8',
            command=[
                self.lilypond_info.abscommand()
                or self.lilypond_info.command
            ],
            args=kwargs.get('args', None),
            input=input,
            decode_errors='replace',
            directory=directory,
            environment=environment,
            title=title,
            queue=kwargs.get('queue', 'engrave')
        )

        # Initialize further, LilyPond-specific options from the given arguments
        self._d_options = kwargs.get('d_options', {})
        self._backend_args = kwargs.get('backend', [])
        self._includepath.extend(kwargs.get('includepaths', []))

        # Set default values from Preferences
        s = QSettings()
        s.beginGroup("lilypond_settings")
        if not self.has_d_option('delete-intermediate-files'):
            self.set_d_option(
                'delete-intermediate-files',
                s.value("delete_intermediate_files", True, bool)
            )
        self.default_output_target = s.value(
            "default_output_target", "pdf", str)
        if not self.has_d_option('embed-source-code'):
            self.embed_source_code = s.value("embed_source_code", False, bool)
        if (
            s.value("no_translation", False, bool)
            or environment.get('LANG', False)
        ):
            self.set_environment('LANG', 'C')
            self.set_environment('LC_ALL', 'C')

    def add_include_path(self, path):
        """Manually add an include path to the current job."""
        if path:
            self._includepath.append(path)

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
                    if (
                        self.embed_source_code
                        and self.lilypond_version >= (2, 19, 39)
                    ):
                        result.append('-dembed-source-code')
                result.append('--pdf')
        return result

    def _cmd_add_backend_args(self):
        """
        Add the arguments defining the backend
        to the command.
        """
        self._command.extend(self.backend_args())

    def _cmd_add_d_options(self):
        """
        Compose a list of -d options
        and add it to the command.
        """
        cmd = self._command
        opts = self._d_options
        for key in opts.keys():
            value = opts[key]
            cmd.append('-d{state}{key}{value}'.format(
                state='' if value else 'no-',
                key=key,
                value='=' + value if type(value) != bool else ''
            ))

    def _cmd_add_includepath(self):
        """
        Add the include path(s) to the command.
        """
        self._command.extend(self.paths(self._includepath))

    def _configure_command(self):
        """Compose the command line for a LilyPond job using all options.
        Individual steps may be overridden in subclasses."""
        self._cmd_add_d_options()
        self._cmd_add_arguments()
        self._cmd_add_includepath()
        self._cmd_add_backend_args()
        self._cmd_add_input()

    def has_d_option(self, k):
        """
        Return True if a given -d option is present.
        """
        return k in self._d_options

    def paths(self, includepath):
        """
        Return the include paths as a string list
        Ensure paths have trailing slashes for Windows compatibility.
        """
        return ['-I{}'.format(path.rstrip('/') + '/') for path in includepath]

    def set_d_option(self, key, value=True):
        """
        Set a -d command line option.
        If None is given the entry is removed from the dictionary.
        """
        if value is None:
            self._d_options.remove(key)
        else:
            self._d_options[key] = value


class PreviewJob(LilyPondJob):
    """Represents a LilyPond Job in Preview mode."""

    def __init__(self, document, **kwargs):
        super(PreviewJob, self).__init__(document, **kwargs)
        self.set_d_option('point-and-click', True)


class PublishJob(LilyPondJob):
    """Represents a LilyPond Job in Publish mode."""

    def __init__(self, document, **kwargs):
        super(PublishJob, self).__init__(document, **kwargs)
        self.set_d_option('point-and-click', False)


class LayoutControlJob(LilyPondJob):
    """Represents a LilyPond Job in Layout Control mode."""

    def __init__(self, document, **kwargs):
        super(LayoutControlJob, self).__init__(document, **kwargs)
        self.check_options()

    def check_options(self):
        s = QSettings()
        s.beginGroup('lilypond_settings')
        for mode in layoutcontrol.modelist():
            if s.value(mode, False, bool):
                self.set_d_option(layoutcontrol.option(mode))

        if s.value('custom-file', False, bool):
            include_file = s.value('custom-filename', '', str)
            if include_file:
                self.set_d_option('debug-custom-file', include_file)

        # if at least one debug mode is used, add the directory with the
        # preview-mode files to the search path
        if self._d_options:
            self.set_d_option('include-settings', 'debug-layout-options.ly')
            self.add_include_path(layoutcontrol.__path__[0])

        self.set_d_option(
            'point-and-click', s.value('point-and-click', True, bool)
        )

        if s.value('verbose', False, bool):
            self.add_argument('--verbose')


class VolatileTextJob(PublishJob):
    """
    Represents a 'volatile' LilyPond Job where the document
    is given as a string. Internally a document is created
    in a temporary file, and options set to not use point-and-click.
    Keyword arguments known to LilyPondJob will be passed on, and
    `base_dir` can be used to add a 'virtual' document Directory
    in order to use relative includes.
    """

    _target_dir = util.tempdir()

    def __init__(self, text, **kwargs):
        doc = self.create_document(text, kwargs)
        super(VolatileTextJob, self).__init__(doc, **kwargs)
        self.add_include_path(kwargs.get('base_dir', ''))
        self.set_directory(self.target_dir)

    def _create_document(self, text):
        """
        Write the given text to a temporary file
        and create a document.Document instance.
        """
        filename = os.path.join(self.target_dir, self.base_name + '.ly')
        with open(filename, 'wb') as f:
            f.write(text.encode('utf-8'))
        url = QUrl(filename)
        url.setScheme('file')
        return document.Document(url)

    def create_document(self, text, kwargs):
        """Create a document from the text.
        kwargs is ignored in this class but not in the
        CachedPreviewJob subclass."""
        self.target_dir = self._target_dir
        self.base_name = 'document'
        return self._create_document(text)

    def resultfiles(self):
        """Returns a list of resulting file(s)"""
        # TODO: Support non-PDF compilation modes
        return glob.glob(os.path.join(self.directory(), '*.pdf'))


class CachedPreviewJob(VolatileTextJob):
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

    def __init__(self, text, **kwargs):
        super(CachedPreviewJob, self).__init__(text, **kwargs)
        self.done.connect(self.remove_intermediate)

    def create_document(self, text, kwargs):
        """Create a document and determine the need for recompilation
        Generate a filename by a full hash of the input file (without
        includes) and test if the corresponding PDF file already exists.
        """
        import hashlib
        md = hashlib.md5()
        md.update(text.encode('utf-8'))
        self.base_name = md.hexdigest()
        self.target_dir = kwargs.get('target_dir', self._target_dir)
        self.needs_compilation = not os.path.exists(
            os.path.join(self.target_dir, self.base_name + '.pdf')
        )
        if self.needs_compilation:
            return self._create_document(text)
        else:
            return document.Document()

    def remove_intermediate(self):
        """Remove all files from the compilation except
        the (main) .pdf and the .ly files."""
        dir = self.target_dir
        files = os.listdir(dir)
        base_name = self.base_name
        keep = [base_name + '.ly', base_name + '.pdf']
        for f in files:
            if f.startswith(base_name) and f not in keep:
                os.remove(os.path.join(dir, f))

    def resultfiles(self):
        """
        Returns a single result file, wrapped in a list.
        This for example prevents system-wise files from
        lilypond-book-preamble to clutter the preview.
        """
        # TODO: Support non-PDF compilation modes
        resultfile = os.path.join(self.directory(), self.base_name + '.pdf')
        if os.path.exists(resultfile):
            return [resultfile]
        else:
            return []

    def start(self):
        """Override the Job start, using cached PDF if possible."""
        if self.needs_compilation:
            super(CachedPreviewJob, self).start()
        else:
            self.done("cached")
