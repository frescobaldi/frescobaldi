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

import sys

import ly.pkginfo

from . import command


def usage():
    """Print usage info."""
    sys.stdout.write("""\
Usage: ly [options] commands file, ...

A tool for manipulating LilyPond source files

Options:
  -v, --version         show version number and exit
  -h, --help            show this help text and exit
  -i, --in-place        overwrite input files
  -o, --output NAME     output file name
  -e, --encoding ENC    (input) encoding (default UTF-8)
  --output-encoding ENC output encoding (default to input encoding)
  -d variable=value     set a variable
  --                    consider the remaining arguments to be file names

The command is one string with semicolon-separated commands.
Available commands are:
  variable=value        set a variable, can be used between other commands
  indent                re-indent the file
  reformat              reformat the file
  translate language    translate the pitch names to the language
  transpose from to     transpose the file like LilyPond would do, pitches
                        are given in the 'nederlands' language

The following variables can be set to influence the behaviour of commands:
  mode                  [empty] mode of the file to read (default automatic)
                        can be one of: lilypond, scheme, latex, html, docbook,
                        texinfo.
  backup-suffix         string [~], to use when editing files in-place, if set,
                        backs up the original file before overwriting it
  indent-tabs           true/false [false], whether to use tabs for indent
  indent-width          number [2], how many spaces for each indent level
  tab-width             number [8], used when converting tabs to spaces

Example:
  ly "reformat; transpose c d" file.ly

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
        self.backup_suffix = '~'
        
        self.command = []
        self.files = []
        
        self.indent_width = 2
        self.indent_tabs = False
        self.tab_width = 8
    
    def set_variable(self, s):
        try:
            name, value = s.split('=', 1)
        except ValueError:
            die("missing '=' in variable set")
        name = name.replace('-', '_')
        if value.lower() in ('yes', 'on', 'true'):
            value = True
        elif value.lower() in ('no', 'off', 'false'):
            value = False
        elif value.isdigit():
            value = int(value)
        setattr(self, name, value)

def parse_command_line():
    """Return an Options instance with all the information from the commandline.
    
    Also performs error handling and may exit on certain circumstances.
    
    """
    if len(sys.argv) < 2:
        usage_short()
        sys.exit(2)

    args = iter(sys.argv[1:])
    opts = Options()
    
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
            varset = next_arg("missing variable=value")
            opts.set_variable(varset)
        elif arg in ('-e', '--encoding'):
            opts.encoding = next_arg("missing encoding name")
        elif arg == '--output-encoding':
            opts.output_encoding = next_arg("missing output encoding name")
        elif arg == '--':
            opts.files.extend(args)
        elif arg.startswith('-'):
            die('unknown option: ' + arg)
        elif not opts.command:
            opts.command = parse_command(arg)
        else:
            opts.files.append(arg)
    if not opts.command and opts.output_encoding is None:
        die('no commands given, nothing to do')
    if not opts.files:
        opts.files.append('-')
    return opts

def parse_command(arg):
    """Parse the command string, returning a list of command.command instances.
    
    Exits when a command is invalid.
    
    """
    result = []
    
    for c in arg.split(';'):
        args = c.split(None, 1)
        if args:
            if '=' in args[0]:
                args = ['set_variable', c]
            cmd = args.pop(0)
            try:
                result.append(getattr(command, cmd)(*args))
            except AttributeError:
                die("unknown command: " + cmd)
            except (TypeError, ValueError):
                die("invalid arguments: " + c)
    return result

opts = parse_command_line()
print vars(opts)

