# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2015 - 2015 by Wilbert Berendsen
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
Variables, checking and defaults.
"""

from __future__ import unicode_literals


def _check_bool(name, value):
    """Check for boolean value."""
    if value.lower() in ('yes', 'on', 'true'):
        return True
    elif value.lower() in ('no', 'off', 'false'):
        return False
    elif value.isdigit():
        return bool(int(value))
    raise ValueError(
        "{name}: ambiguous boolean value: {value}".format(
            name=name, value=value))


def _check_int(name, value):
    """Check for integer value."""
    if value.isdigit():
        return int(value)
    raise ValueError("{name}: not an integer value: {value}".format(
            name=name, value=value))


def mode(arg):
    import ly.lex
    if arg is not None and arg not in ly.lex.modes:
        raise ValueError("unknown mode: {mode}".format(mode=arg))
    return mode


def in_place(arg):
    return _check_bool("in-place", arg)


def encoding(arg):
    import codecs
    try:
        codecs.lookup(arg)
    except LookupError:
        raise ValueError("encoding: unknown encoding: {encoding}".format(
            encoding=encoding))
    return arg


def output_encoding(arg):
    if arg:
        import codecs
        try:
            codecs.lookup(arg)
        except LookupError:
            raise ValueError("output-encoding: unknown encoding: {encoding}".format(
                encoding=encoding))
        return arg
    return None


def output(arg):
    return arg or None


def replace_pattern(arg):
    return _check_bool("replace-pattern", arg)


def backup_suffix(arg):
    if "/" in arg:
        raise ValueError("/ not allowed in backup-suffix")


def with_filename(arg):
    if arg:
        return _check_bool("with-filename", arg)
    return None


def default_language(arg):
    import ly.pitch
    if arg:
        if arg not in ly.pitch.pitchInfo:
            raise ValueError("unknown pitch language: {language}".format(
                language=arg))
        return arg
    return "nederlands"


def rel_startpitch(arg):
    return _check_bool("rel-startpitch", arg)


def rel_absolute(arg):
    return _check_bool("rel-absolute", arg)


def indent_width(arg):
    return _check_int("indent-width", arg)


def indent_tabs(arg):
    return _check_bool("indent-tabs", arg)


def tab_width(arg):
    return _check_int("tab-width", arg)


def inline_style(arg):
    return _check_bool("inline-style", arg)


def full_html(arg):
    return _check_bool("full_html", arg)


def stylesheet(arg):
    return arg or None


def number_lines(arg):
    return _check_bool("number-lines", arg)


def wrapper_tag(arg):
    if not arg in ['div', 'pre', 'code', 'id']:
        raise ValueError("unknown wrapper tag: {tag}".format(
            tag=arg))
    return arg


def wrapper_attribute(arg):
    if not arg in ['id', 'class']:
        raise ValueError("wrapper attribute must be 'id' or 'class', found {attr}".format(
            attr=arg))
    return arg

    
def document_id(arg):
    return arg or None


def linenumbers_id(arg):
    return arg or None
