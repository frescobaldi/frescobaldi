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


class command(object):
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


class set_variable(command):
    """sets a variable to a value"""
    def __init__(self, arg):
        self.name, self.value = arg.split('=', 1)

    def run(self, opts, cursor):
        opts.set_variable(self.name, self.value)
    

class indent(command):
    """runs the indenter"""
    pass


