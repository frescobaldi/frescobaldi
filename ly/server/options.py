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
Options configuring the commands' behaviour
"""

from __future__ import unicode_literals

from ly.cli import setvar

class ServerOptions(object):
    """
    Options configuring the server itself, not the individual commands
    """
    
    def __init__(self):
        self.port = 5432
        self.timeout = 0
    

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
            raise AttributeError("unknown variable: {name}".format(name=name))
        try:
            value = func(value)
        except ValueError as e:
            raise ValueError(format(e))
        setattr(self, name, value)    
