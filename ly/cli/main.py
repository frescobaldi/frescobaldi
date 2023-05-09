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
The entry point for the 'ly' command.
"""

from __future__ import unicode_literals

import contextlib
import copy
import io
import os
import shutil
import sys

import ly.pkginfo
from . import setvar


def usage():
    """Print usage info."""
    from . import doc
    sys.stdout.write(doc.__doc__)

def usage_short():
    """Print short usage info."""
    sys.stdout.write("""\
Usage: ly [options] commands file, ...

A tool for manipulating LilyPond source files

See ly -h for a full list of commands and options.
""")

def version():
    """Print version info."""
    sys.stdout.write("ly {0}\n".format(ly.pkginfo.version))

def die(message):
    """Exit with message to STDERR."""
    sys.stderr.write("error: " + message + '\n')
    sys.stderr.write(
        "See ly -h for a full list of commands and options.\n")
    sys.exit(1)

class Options(object):
    """Store all the startup options and their defaults."""
    def __init__(self):
        self.mode = None
        self.in_place = False
        self.encoding = 'UTF-8'
        self.output_encoding = None
        self.output = None
        self.replace_pattern = True
        self.backup_suffix = '~'
        self.with_filename = None
        self.default_language = "nederlands"
        self.rel_startpitch = True
        self.rel_absolute = None

        self.indent_width = 2
        self.indent_tabs = False
        self.tab_width = 8

        self.full_html = True
        self.inline_style = False
        self.stylesheet = None
        self.number_lines = False
        self.wrapper_tag = 'pre'
        self.wrapper_attribute = 'class'
        self.document_id = 'lilypond'
        self.linenumbers_id = 'linenumbers'

    def set_variable(self, name, value):
        name = name.replace('-', '_')
        try:
            func = getattr(setvar, name)
        except AttributeError:
            die("unknown variable: {name}".format(name=name))
        try:
            value = func(value)
        except ValueError as e:
            die(format(e))
        setattr(self, name, value)

class Output(object):
    """Object living for a whole file/command operation, handling the output.

    When opening a file it has already opened earlier, the file is appended to
    (like awk).

    """
    def __init__(self):
        self._seen_filenames = set()

    def get_filename(self, opts, filename):
        """Queries the output attribute from the Options and returns it.

        If replace_pattern is True (by default) and the attribute contains a
        '*', it is replaced with the full path of the specified filename,
        but without extension. It the attribute contains a '?', it is
        replaced with the filename without path and extension.

        If '-' is returned, it denotes standard output.

        """
        if not opts.output:
            return '-'
        elif opts.replace_pattern:
            path, ext = os.path.splitext(filename)
            directory, name = os.path.split(path)
            return opts.output.replace('?', name).replace('*', path)
        else:
            return opts.output

    @contextlib.contextmanager
    def file(self, opts, filename, encoding):
        """Return a context manager for writing to.

        If you set encoding to "binary" or False, the file is opened in binary
        mode and you should encode the data you write yourself.

        """
        if not filename or filename == '-':
            filename, mode = sys.stdout.fileno(), 'w'
        else:
            if filename not in self._seen_filenames:
                self._seen_filenames.add(filename)
                if opts.backup_suffix and os.path.exists(filename):
                    shutil.copy(filename, filename + opts.backup_suffix)
                mode = 'w'
            else:
                mode = 'a'
        if encoding in (False, "binary"):
            f = io.open(filename, mode + 'b')
        else:
            f = io.open(filename, mode, encoding=encoding)
        try:
            yield f
        finally:
            f.close()

def parse_command_line():
    """Return a three-tuple(options, commands, files).

    options is an Options instance with all the command-line options
    commands is a list of command.command instances
    files is the list of filename arguments

    Also performs error handling and may exit on certain circumstances.

    """
    if len(sys.argv) < 2:
        usage_short()
        sys.exit(2)

    args = iter(sys.argv[1:])

    opts = Options()
    commands = []
    files = []

    def next_arg(message):
        """Get the next argument, if missing, die with message."""
        try:
            return next(args)
        except StopIteration:
            die(message)

    for arg in args:
        if arg in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif arg in ('-v', '--version'):
            version()
            sys.exit(0)
        elif arg in ('-i', '--in-place'):
            opts.in_place = True
        elif arg in ('-o', '--output'):
            opts.output = next_arg("missing output filename")
        elif arg == '-d':
            s = next_arg("missing variable=value")
            try:
                name, value = s.split('=', 1)
            except ValueError:
                die("missing '=' in variable set")
            opts.set_variable(name, value)
        elif arg in ('-e', '--encoding'):
            opts.encoding = next_arg("missing encoding name")
        elif arg == '--output-encoding':
            opts.output_encoding = next_arg("missing output encoding name")
        elif arg in ('-l', '--language'):
            s = next_arg("missing language name")
            opts.set_variable("default-language", s)
        elif arg == '--':
            files.extend(args)
        elif arg.startswith('-'):
            die('unknown option: ' + arg)
        elif not commands:
            commands = parse_command(arg)
        else:
            files.append(arg)
    from . import command
    if not commands or isinstance(commands[-1], command._edit_command):
        commands.append(command.write())
    if not files:
        files.append('-')
    if opts.with_filename is None:
        opts.with_filename = len(files) > 1
    return opts, commands, files

def parse_command(arg):
    """Parse the command string, returning a list of command.command instances.

    Exits when a command is invalid.

    """
    from . import command

    result = []

    for c in arg.split(';'):
        args = c.split(None, 1)
        if args:
            if '=' in args[0]:
                args = ['set_variable', c.strip()]
            cmd = args.pop(0)
            if not cmd or not cmd[0].isalpha():
                die("unknown command: " + cmd)
            try:
                cmd_class = getattr(command, cmd.replace('-', '_'))
            except AttributeError:
                die("unknown command: " + cmd)
            try:
                result.append(cmd_class(*args))
            except (TypeError, ValueError):
                die("invalid arguments: " + c)
    return result

def load(filename, encoding, mode):
    """Load a file, returning a ly.document.Document"""
    import ly.document
    if filename == '-':
        doc = ly.document.Document.load(sys.stdin.fileno(), encoding, mode)
        doc.filename = '-'
    else:
        doc = ly.document.Document.load(filename, encoding, mode)
    return doc

def main():
    opts, commands, files = parse_command_line()
    import ly.document
    output = Output()
    exit_code = 0
    for filename in files:
        options = copy.deepcopy(opts)
        try:
            doc = load(filename, options.encoding, options.mode)
        except IOError as err:
            sys.stderr.write('warning: skipping file "{0}":\n  {1}\n'.format(filename, err))
            exit_code = 1
            continue
        cursor = ly.document.Cursor(doc)
        for c in commands:
            c.run(options, cursor, output)
    return exit_code
