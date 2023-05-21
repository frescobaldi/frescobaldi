# This file is part of python-ly, https://pypi.python.org/pypi/python-ly
#
# Copyright (c) 2008 - 2015 by Wilbert Berendsen
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
A package of modules dealing with LilyPond and the LilyPond format.

The ly module supports both Python2 and Python3. This is a short description
of some modules:

  * ly.slexer: generic tools to build parsers using regular expressions
  * ly.node: a generic list-like node object to build tree structures with
  * ly.document: a tokenized text document (LilyPond file)
  * ly.docinfo: harvests and caches various information from a LilyPond document
  * ly.lex: a parser for LilyPond, Scheme, and other formats, using slexer
  * ly.music: a tree structure of the contents of a document
  * ly.pitch: functions for translating, transposing etc
  * ly.rhythm: functions dealing with rhythm
  * ly.indent: indent LilyPond text
  * ly.reformat: format LilyPond text
  * ly.dom: (deprecated) tree structure to build LilyPond text from
  * ly.words: words for highlighting and autocompletion
  * ly.data: layout objects, properties, interfaces, font glyphs etc extracted
    from LilyPond
  * ly.cli: the implementation of the command-line 'ly' script

A LilyPond document (source file) is held by a ly.document.Document. The
Document class automatically parses and tokenizes the text, also when its
contents are changed.

A music tree can be built from a document using the ly.music module.
In the near future, music trees can be built from scratch and also generate
LilyPond output from scratch. At that moment, ly.dom is deprecated.

The functions in ly.pitch, such as transpose and translate currently access
the tokens in the document, but in the future they will work on the music tree.


"""
