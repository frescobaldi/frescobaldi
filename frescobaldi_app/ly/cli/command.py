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
The commands that are available to the command line.
"""

from __future__ import unicode_literals

import sys

import ly.docinfo


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

    def run(self, opts, cursor):
        pass


class set_variable(_command):
    """set a variable to a value"""
    def __init__(self, arg):
        self.name, self.value = arg.split('=', 1)

    def run(self, opts, cursor):
        opts.set_variable(self.name, self.value)
    

class _info_command(_command):
    """base class for commands that print some output to stdout."""
    def run(self, opts, cursor):
        info = ly.docinfo.DocInfo(cursor.document)
        text = self.get_info(info)
        if text:
            if opts.with_filename:
                text = cursor.document.filename + ":" + text
            sys.stdout.write(text + '\n')
    
    def get_info(self, info):
        """Should return the desired information from the docinfo object."""
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


class indent(_command):
    """run the indenter"""
    pass


