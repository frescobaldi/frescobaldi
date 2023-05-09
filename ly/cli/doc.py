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

# this module only contains a doc string, which is printed when using
# ly -h .

"""
Usage::

  ly [options] commands file, ...

A tool for manipulating LilyPond source files

Options
-------

  -v, --version          show version number and exit
  -h, --help             show this help text and exit
  -i, --in-place         overwrite input files
  -o, --output NAME      output file name
  -e, --encoding ENC     (input) encoding (default UTF-8)
  --output-encoding ENC  output encoding (default to input encoding)
  -l, --language NAME    default pitch name language (default to "nederlands")
  -d <variable=value>    set a variable

The special option ``--`` considers the remaining arguments to be file names.


Arguments
---------

The command is one argument with semicolon-separated commands. In most cases
you'll quote the command so that it is seen as one argument.

You can specify more than one LilyPond file. If you want to process many 
files and write the results of the operations on each file to a separate 
output file, you can use two special characters in the output filename: a 
'*' will be replaced with the full path name of the current input file 
(without extension), and a '?' will be replaced with the input filename 
(without path and extension). If you don't want to have '*' or '?' replaced 
in the output filename, you can set ``-d replace-pattern=false``.

If you don't specify input or output filenames, standard input is read and
standard output is written to.


Commands
--------
  
Informative commands that write information to standard output and do not
change the file:

  ``mode``
         print the mode (guessing if not given) of the document
  
  ``version``
         print the LilyPond version, if set in the document

  ``language``
         print the pitch name language, if set in the document
  
Commands that change the file:

  ``indent``
         re-indent the file
  
  ``reformat``
         reformat the file

  ``translate <language>``
         translate the pitch names to the language

  ``transpose <from> <to>``
         transpose the file like LilyPond would do, pitches
         are given in the 'nederlands' language

  ``abs2rel``
         convert absolute music to relative

  ``rel2abs``
         convert relative music to absolute

  ``simplify-accidentals``
         replace notes with accidentals as much as possible with their
         natural neighbors

  ``write [filename]``
         write the file to the given filename or the output
         variable. If the last command was an editing command,
         write is automatically called.

Commands that export the file to another format:

  ``musicxml [filename]``
         export to MusicXML (in development, far from complete)

  ``highlight [filename]``
         export the document as syntax colored HTML

  ``hl [filename]``
         alias for highlight

Between commands, you can set or unset a variable using:

  ``variable=value``
         set a variable to value. Special values are true, false,
         which are interpreted as boolean values, or digits,
         which will be interpreted as integer values.

  ``variable=``
         unset a variable


Variables
---------

The following variables can be set to influence the behaviour of commands.
If there is a default value, it is written between brackets:

  ``mode``
         mode of the file to read (default automatic) can be one
         of: lilypond, scheme, latex, html, docbook, texinfo.
  
  ``output`` [-]
         the output filename (also set by -o argument)

  ``encoding`` [UTF-8]
         encoding to read (also set by -e argument)

  ``default-language`` [nederlands]
         the pitch names language to use by default, when not specified
         otherwise in the document

  ``output-encoding``
         encoding to write (defaults to ``encoding``, also
         set by the ``--output-encoding`` argument)

  ``in-place`` [``false``]
         whether to overwrite input files (same as ``-i``)

  ``backup-suffix`` [~]
         suffix to use when editing files in-place, if set,
         backs up the original file before overwriting it

  ``replace-pattern`` [``true``]
         whether to replace '*' and '?' in the output filename.

  ``rel-startpitch`` [``true``]
         whether to write relative music with a startpitch
  
  ``rel-absolute``
         whether to assume that the first pitch in a relative expression without
         specified startpitch is absolute. If ``false``, it is assumed to be
         relative to ``c'``. If ``true``, it is assumed to be absolute (in fact
         relative to ``f``. If not set, this variable defaults to ``true`` only
         when the LilyPond version in the document >= 2.18.

  ``indent-tabs`` [``false``]
         whether to use tabs for indent

  ``indent-width`` [2]
         how many spaces for each indent level (if not using tabs)

  ``full-html`` [``True``]
        if set to True a full document with syntax-highlighted HTML
        will be exported, otherwise only the bare content wrapped in an
        element configured by the ``wrapper-`` variables.        

  ``stylesheet``
         filename to reference as an external stylesheet for
         syntax-highlighted HTML. This filename is literally used
         in the ``<link rel="stylesheet">`` tag.

  ``inline-style`` [``false``]
         whether to use inline style attributes for syntax-highlighted HTML.
         By default a css stylesheet is embedded.

  ``number-lines`` [``false``]
         whether to add line numbers when creating syntax-highlighted HTML.

  ``wrapper-tag`` [``pre``]
         which tag syntax highlighted HTML will be wrapped in. Possible values:
         ``div``, ``pre``, ``id`` and ``code``

  ``wrapper-attribute`` [``class``]
        attribute used for the wrapper tag. Possible values: ``id`` and ``class``.

  ``document-id`` [``lilypond``]
        name applied to the wrapper-attribute.
        If the three last options use their default settings
        the highlighted HTML elements are wrapped in an element
        ``<pre class="lilypond"></pre>``

  ``linenumbers-id`` [``linenumbers``]
        if linenumbers are exported this is the name used for the ``<td>`` elements

These variables influence the output of information commands:

  ``with-filename``
         prints the filename next to information like version,
         etc. This is ``true`` by default if there is more than one
         file specified.


Examples
--------

Here is an example to re-indent and transpose a LilyPond file::

  ly "indent; transpose c d" -o output.ly file.ly

Examples using the '*' in the output file name::

  ly "transpose c d" *.ly -o '*-transposed.ly'
  ly highlight *.ly -o 'html/?.html'


"""
