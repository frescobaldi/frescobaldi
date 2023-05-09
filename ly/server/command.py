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

import ly

known_commands = [
    'mode',
    'version',
    'language',
    'indent',
    'reformat',
    'translate',
    'transpose',
    'rel2abs',
    'abs2rel',
    'musicxml',
    'highlight'
]

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

    def run(self, opts, data):
        pass


class set_variable(_command):
    """set a configuration variable to a value"""
    def __init__(self, arg):
        self.name, self.value = arg.split('=', 1)

    def run(self, opts, data):
        opts.set_variable(self.name, self.value)


#################################
### Base classes for commands ###
#################################

# The command classes have a run() method that serves as a common structure
# for each command type.  From within run() a function is called to perform
# the actual, command-specific funcionality.
# The run() method also takes care of updating the data object with the correct
# nesting structure and metadata.
class _info_command(_command):
    """
    Base class for commands that retrieve some info about the document.
    The result is appended to the data['info'] array as a dict with 'command'
    and 'info' fields.
    """
    def run(self, opts, data):
        import ly.docinfo
        info = ly.docinfo.DocInfo(data['doc']['content'].document)
        text = self.get_info(info)
        data['info'].append({
            'command': self.__class__.__name__,
            'info': text or ""
        })

    def get_info(self, info):
        """
        Should return the desired information from the docinfo object.
        """
        raise NotImplementedError()


class _edit_command(_command):
    """
    Base class for commands that modify the input.
    The modifications overwrite the content of data['doc']['content'], so a
    subsequent edit commands builds on the modified content. The command name is
    added to the data['doc']['commands'] dict so it is possible to retrace which
    commands have been applied to the final result.
    """
    def run(self, opts, data):
        self.edit(opts, data['doc']['content'])
        data['doc']['commands'].append(self.__class__.__name__)
    
    def edit(self, opts, cursor):
        """Should edit the cursor in-place."""
        raise NotImplementedError()


class _export_command(_command):
    """
    Base class for commands that convert the input to another format.
    For each command an entry will be appended to data['exports'] field of the
    'data' dict, leaving data['doc'] untouched. Each entry in data['exports']
    has a ['doc'] and a ['command'] field, allowing the client to identify the
    
    """
    def run(self, opts, data):
        export = self.export(opts, data['doc']['content'], data['exports'])
        data['exports'].append({
            'command': self.__class__.__name__,
            'doc': export
        })
    
    def export(self, opts, cursor, exports):
        """Should return the converted document as string."""
        raise NotImplementedError()


#####################
### Info commands ###
#####################

class mode(_info_command):
    """retrieve mode from document"""
    def get_info(self, info):
        return info.mode()


class version(_info_command):
    """retrieve version from document"""
    def get_info(self, info):
        return info.version_string()


class language(_info_command):
    """retrieve language from document"""
    def get_info(self, info):
        return info.language()


#####################
### Edit commands ###
#####################

class indent(_edit_command):
    """run the indenter"""
    def indenter(self, opts):
        """Get a ly.indent.Indenter initialized with our options."""
        import ly.indent
        i = ly.indent.Indenter()
        i.indent_tabs = opts.indent_tabs
        i.indent_width = opts.indent_width
        return i
    
    def edit(self, opts, cursor):
        self.indenter(opts).indent(cursor)


class reformat(indent):
    """reformat the document"""
    def edit(self, opts, cursor):
        import ly.reformat
        ly.reformat.reformat(cursor, self.indenter(opts))


class translate(_edit_command):
    """translate pitch names"""
    def __init__(self, language):
        if language not in ly.pitch.pitchInfo:
            raise ValueError()
        self.language = language
    
    def edit(self, opts, cursor):
        import ly.pitch.translate
        try:
            changed = ly.pitch.translate.translate(cursor, self.language, opts.default_language)
        except ly.pitch.PitchNameNotAvailable as pna:
            raise ValueError(format(pna))
        if not changed:
            version = ly.docinfo.DocInfo(cursor.document).version()
            ly.pitch.translate.insert_language(cursor.document, self.language, version)
    

class transpose(_edit_command):
    """transpose music"""
    def __init__(self, arg):
        import re
        result = []
        for pitch, octave in re.findall(r"([a-z]+)([,']*)", arg):
            r = ly.pitch.pitchReader("nederlands")(pitch)
            if r:
                result.append(ly.pitch.Pitch(*r, octave=ly.pitch.octaveToNum(octave)))
        self.from_pitch, self.to_pitch = result

    def edit(self, opts, cursor):
        import ly.pitch.transpose
        transposer = ly.pitch.transpose.Transposer(self.from_pitch, self.to_pitch)
        try:
            ly.pitch.transpose.transpose(cursor, transposer, opts.default_language)
        except ly.pitch.PitchNameNotAvailable as pna:
            language = ly.docinfo.DocInfo(cursor.document).language() or opts.default_language
            raise ValueError(format(pna))


class rel2abs(_edit_command):
    """convert relative music to absolute"""
    def edit(self, opts, cursor):
        import ly.pitch.rel2abs
        ly.pitch.rel2abs.rel2abs(cursor, opts.default_language)


class abs2rel(_edit_command):
    """convert absolute music to relative"""
    def edit(self, opts, cursor):
        import ly.pitch.abs2rel
        ly.pitch.abs2rel.abs2rel(cursor, opts.default_language)


#######################
### Export commands ###
#######################

class musicxml(_export_command):
    """convert source to MusicXML"""
    def export(self, opts, cursor, exports):
        import ly.musicxml
        writer = ly.musicxml.writer()
        writer.parse_document(cursor.document)
        #TODO!!!
        # In Python3 this incorrectly escapes the \n characters,
        # but leaving out the str() conversion returns a Bytes object,
        # which will in turn trigger an "object is not JSON serializable" error
        return str(writer.musicxml().tostring())


class highlight(_export_command):
    """convert source to syntax colored HTML."""
    def export(self, opts, cursor, exports):
        import ly.colorize
        w = ly.colorize.HtmlWriter()
    
        # set configuration options
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

        return w.html(cursor)
