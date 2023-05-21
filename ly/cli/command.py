# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2014 - 2015 by Wilbert Berendsen
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
The commands that are available to the command line.
"""

from __future__ import unicode_literals

import re
import sys

import ly.docinfo
import ly.indent
import ly.pitch
import ly.reformat


class _command(object):
    """Base class for commands.

    If the __init__() fails with TypeError or ValueError, the command is
    considered invalid and an error message will be written to the console
    in the parse_command() function in main.py.

    By default, __init__() expects no arguments. If your command does accept
    arguments, they are provided in a single argument that you should parse
    yourself.

    """
    def __init__(self):
        pass

    def run(self, opts, cursor, output):
        pass

    @staticmethod
    def get_absolute(opts, cursor):
        """Utility function to determine whether the first pitch in a relative should
        be regarded as absolute (LilyPond 2.18+ behaviour).
        
        """
        if opts.rel_absolute is None:
            return ly.docinfo.DocInfo(cursor.document).version() >= (2, 18)
        else:
            return opts.rel_absolute


class set_variable(_command):
    """set a variable to a value"""
    def __init__(self, arg):
        self.name, self.value = arg.split('=', 1)

    def run(self, opts, cursor, output):
        opts.set_variable(self.name, self.value)


class _info_command(_command):
    """base class for commands that print some output to stdout."""
    def run(self, opts, cursor, output):
        info = ly.docinfo.DocInfo(cursor.document)
        text = self.get_info(info)
        if text:
            if opts.with_filename:
                text = cursor.document.filename + ":" + text
            sys.stdout.write(text + '\n')

    def get_info(self, info):
        """Should return the desired information from the docinfo object.

        If it returns None or an empty string, nothing is printed.

        """
        raise NotImplementedError()


class mode(_info_command):
    """print mode to stdout"""
    def get_info(self, info):
        return info.mode()


class version(_info_command):
    """print version to stdout"""
    def get_info(self, info):
        return info.version_string()


class language(_info_command):
    """print language to stdout"""
    def get_info(self, info):
        return info.language()


class _edit_command(_command):
    """a command that edits the source file"""
    pass


class indent(_edit_command):
    """run the indenter"""
    def indenter(self, opts):
        """Get a ly.indent.Indenter initialized with our options."""
        i = ly.indent.Indenter()
        i.indent_tabs = opts.indent_tabs
        i.indent_width = opts.indent_width
        return i

    def run(self, opts, cursor, output):
        self.indenter(opts).indent(cursor)


class reformat(indent):
    """reformat the document"""
    def run(self, opts, cursor, output):
        ly.reformat.reformat(cursor, self.indenter(opts))


class translate(_edit_command):
    """translate pitch names"""
    def __init__(self, language):
        if language not in ly.pitch.pitchInfo:
            raise ValueError()
        self.language = language

    def run(self, opts, cursor, output):
        import ly.pitch.translate
        try:
            changed = ly.pitch.translate.translate(cursor, self.language, opts.default_language)
        except ly.pitch.PitchNameNotAvailable:
            sys.stderr.write(
                "warning: transate: pitch names not available in \"{0}\"\n"
                "  skipping file: {1}\n".format(self.language, cursor.document.filename))
            return
        if not changed:
            version = ly.docinfo.DocInfo(cursor.document).version()
            ly.pitch.translate.insert_language(cursor.document, self.language, version)


class transpose(_edit_command):
    """transpose music"""
    def __init__(self, arg):
        result = []
        for pitch, octave in re.findall(r"([a-z]+)([,']*)", arg):
            r = ly.pitch.pitchReader("nederlands")(pitch)
            if r:
                result.append(ly.pitch.Pitch(*r, octave=ly.pitch.octaveToNum(octave)))
        self.from_pitch, self.to_pitch = result

    def run(self, opts, cursor, output):
        absolute = self.get_absolute(opts, cursor)
        import ly.pitch.transpose
        transposer = ly.pitch.transpose.Transposer(self.from_pitch, self.to_pitch)
        try:
            ly.pitch.transpose.transpose(cursor, transposer, opts.default_language, absolute)
        except ly.pitch.PitchNameNotAvailable:
            language = ly.docinfo.DocInfo(cursor.document).language() or opts.default_language
            sys.stderr.write(
                "warning: transpose: pitch names not available in \"{0}\"\n"
                "  skipping file: {1}\n".format(language, cursor.document.filename))


class rel2abs(_edit_command):
    """convert relative music to absolute"""
    def run(self, opts, cursor, output):
        absolute = self.get_absolute(opts, cursor)
        import ly.pitch.rel2abs
        ly.pitch.rel2abs.rel2abs(cursor, opts.default_language, absolute)


class abs2rel(_edit_command):
    """convert absolute music to relative"""
    def run(self, opts, cursor, output):
        absolute = self.get_absolute(opts, cursor)
        import ly.pitch.abs2rel
        ly.pitch.abs2rel.abs2rel(cursor, opts.default_language, opts.rel_startpitch, absolute)


class simplify_accidentals(_edit_command):
    """replace notes with accidentals as much as possible with their natural neighbors"""
    def run(self, opts, cursor, output):
        absolute = self.get_absolute(opts, cursor)
        import ly.pitch.transpose
        transposer = ly.pitch.transpose.Simplifier()
        try:
            ly.pitch.transpose.transpose(cursor, transposer, opts.default_language, absolute)
        except ly.pitch.PitchNameNotAvailable:
            language = ly.docinfo.DocInfo(cursor.document).language() or opts.default_language
            sys.stderr.write(
                "warning: simplify_accidentals: pitch names not available in \"{0}\"\n"
                "  skipping file: {1}\n".format(language, cursor.document.filename))


class _export_command(_command):
    """Command that exports to a file."""
    def __init__(self, output=None):
        self.output = output


class musicxml(_export_command):
    def run(self, opts, cursor, output):
        absolute = self.get_absolute(opts, cursor)
        import ly.musicxml
        writer = ly.musicxml.writer()
        writer.parse_document(cursor.document, absolute)
        xml = writer.musicxml()
        if self.output:
            filename = self.output
        else:
            filename = output.get_filename(opts, cursor.document.filename)
        encoding = opts.output_encoding or "utf-8"
        with output.file(opts, filename, "binary") as f:
            xml.write(f, encoding)


class write(_command):
    """write the source file."""
    def __init__(self, output=None):
        self.output = output

    def run(self, opts, cursor, output):
        # determine the real output filename to use
        encoding = opts.output_encoding or opts.encoding
        if self.output:
            filename = self.output
        elif opts.in_place:
            if not cursor.document.modified and encoding == opts.encoding:
                return
            filename = cursor.document.filename
        else:
            filename = output.get_filename(opts, cursor.document.filename)
        with output.file(opts, filename, encoding) as f:
            f.write(cursor.document.plaintext())


class highlight(_export_command):
    """write syntax colored HTML."""
    def run(self, opts, cursor, output):
        import ly.colorize
        w = ly.colorize.HtmlWriter()

        w.full_html = opts.full_html
        w.inline_style = opts.inline_style
        w.stylesheet_ref = opts.stylesheet
        w.number_lines = opts.number_lines
        w.title = cursor.document.filename
        w.encoding = opts.output_encoding or "utf-8"
        w.wrapper_tag = opts.wrapper_tag
        w.wrapper_attribute = opts.wrapper_attribute
        w.document_id = opts.document_id
        w.linenumbers_id = opts.linenumbers_id

        doc = w.html(cursor)
        if self.output:
            filename = self.output
        else:
            filename = output.get_filename(opts, cursor.document.filename)
        with output.file(opts, filename, w.encoding) as f:
            f.write(doc)


hl = highlight

