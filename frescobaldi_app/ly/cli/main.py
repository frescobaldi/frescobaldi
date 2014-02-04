# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2014 - 2014 by Wilbert Berendsen
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


def usage():
    """Print usage info."""
    sys.stdout.write("""\
Usage: ly [options] commands file, ...

A tool for manipulating LilyPond source files

OPTIONS

  -v, --version         show version number and exit
  -h, --help            show this help text and exit
  -i, --in-place        overwrite input files
  -o, --output NAME     output file name
  -e, --encoding ENC    (input) encoding (default UTF-8)
  --output-encoding ENC output encoding (default to input encoding)
  -d variable=value     set a variable
  --                    consider the remaining arguments to be file names

ARGUMENTS

The command is one argument with semicolon-separated commands. In most cases
you'll quote the command so that it is seen as one argument.

You can specify more than one LilyPond file. If you want to process many 
files and write the results of the operations on each file to a separate 
output file, you can use two special characters in the output filename: a 
'*' will be replaced with the full path name of the current input file 
(without extension), and a '?' will be replaced with the input filename 
(without path and extension). If you don't want to have '*' or '?' replaced 
in the output filename, you can set -d replace-pattern=false.

If you don't specify input or output filenames, standard input is read and
standard output is written to.


COMMANDS
  
Informative commands that write information to standard output and do not
change the file:

  mode                  print the mode (guessing if not given) of the document
  version               print the LilyPond version, if set in the document
  language              print the pitch name language, if set in the document
  
Commands that change the file:

  indent                re-indent the file
  reformat              reformat the file
  translate language    translate the pitch names to the language
  transpose from to     transpose the file like LilyPond would do, pitches
                        are given in the 'nederlands' language
  abs2rel               convert absolute music to relative
  rel2abs               convert relative music to absolute
  write [filename]      write the file to the given filename or the output
                        variable. If the last command was an editing command,
                        write is automatically called.

Commands that export the file to another format:

  musicxml [filename]   exports to MusicXML (in development, far from complete)
  highlight [filename]  exports the document as syntax colored HTML
  hl [filename]         alias for highlight

Between commands, you can set or unset a variable using:

  variable=value        set a variable to value. Special values are true, false,
                        which are interpreted as boolean values, or digits,
                        which will be interpreted as integer values.
  variable=             unset a variable


VARIABLES

The following variables can be set to influence the behaviour of commands.
If there is a default value, it is written between brackets:

  mode                  mode of the file to read (default automatic) can be one
                        of: lilypond, scheme, latex, html, docbook, texinfo.
  output [-]            the output filename (also set by -o argument)
  encoding [UTF-8]      encoding to read (also set by -e argument)
  output-encoding       encoding to write (defaults to encoding, also
                        set by --output-encoding argument)
  in-place [false]      whether to overwrite input files (same as -i)
  backup-suffix [~]     suffix to use when editing files in-place, if set,
                        backs up the original file before overwriting it
  replace-pattern [true] whether to replace '*' and '?' in the output filename.
  indent-tabs [false]   whether to use tabs for indent
  indent-width [2]      how many spaces for each indent level (if not using
                        tabs)
  stylesheet            filename to reference as an external stylesheet for
                        syntax-highlighted HTML. This filename is literally used
                        in the <link rel="stylesheet"> tag.
  inline-style [false]  whether to use inline style attributes for syntax-
                        highlighted HTML. By default a css shylesheet is embed-
                        ded.
  number-lines [false]  whether to add line numbers when creating syntax-
                        highlighted HTML.

These variables influence the output of information commands:

  with-filename         prints the filename next to information like version,
                        etc. This is true by default if there is more than one
                        file specified.

Example:

  ly "reformat; transpose c d" -o output.ly file.ly

Example using the '*' in the output file name:

  ly "transpose c d" *.ly -o '*-transposed.ly'
  ly highlight *.ly -o 'html/?.html'


""")

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
        
        self.indent_width = 2
        self.indent_tabs = False
        self.tab_width = 8
        
        self.inline_style = False
        self.stylesheet = None
        self.number_lines = False
    
    def set_variable(self, name, value):
        name = name.replace('-', '_')
        if value.lower() in ('yes', 'on', 'true'):
            value = True
        elif value.lower() in ('no', 'off', 'false'):
            value = False
        elif value.isdigit():
            value = int(value)
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
    
    # are the arguments unicode? python2 leaves them encoded...
    if type(sys.argv[0]) != type(''):
        args = (a.decode(sys.stdin.encoding) for a in sys.argv[1:])
    else:
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
                args = ['set_variable', c]
            cmd = args.pop(0)
            try:
                result.append(getattr(command, cmd.replace('-', '_'))(*args))
            except AttributeError:
                die("unknown command: " + cmd)
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

sys.exit(main())
