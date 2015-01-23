README for python-ly
====================

This package provides a commandline program `ly` that can be used to do various
manipulations with LilyPond files. LilyPond (www.lilypond.org) is a music
typsetter using a plain text input file format.

This package also provides a Python library `ly` containing various Python
modules to parse, manipulate or create LilyPond files.

The python-ly package is Free Software, licensed under the GPL. This package 
is written by the Frescobaldi developers and part of the Frescobaldi project.
The main author is Wilbert Berendsen.


### Functionality of the `ly` commandline tool:

With `ly` you can reformat, or re-indent LilyPond files, transpose music,
translate pitch names, convert LilyPond to syntax-colored HTML, etc.

There is also experimental support for converting LilyPond to MusicXML.

Use

    ly -h

to get a full list of the features of the `ly` command.

Here is an example to re-indent and transpose a LilyPond file:

    ly "indent; transpose c d" -o output.ly file.ly

### Functionality of the `ly` Python module:

The `ly` module supports both Python2 and Python3. This is a short description
of some modules:
  
  * `ly.slexer`: generic tools to build parsers using regular expressions
  * `ly.node`: a generic list-like node object to build tree structures with
  * `ly.document`: a tokenized text document (LilyPond file)
  * `ly.lex`: a parser for LilyPond, Scheme, and other formats, using `slexer`
  * `ly.music`: a tree structure of the contents of a document
  * `ly.pitch`: functions for translating, transposing etc
  * `ly.indent`: indent LilyPond text
  * `ly.reformat`: format LilyPond text
  * `ly.dom`: (deprecated) tree structure to build LilyPond text from
  * `ly.words`: words for highlighting and autocompletion
  * `ly.data`: layout objects, properties, interfaces, font glyphs etc extracted
    from LilyPond


