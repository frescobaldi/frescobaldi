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

  ly-server [options]

An HTTP server for manipulating LilyPond input code

Server Options
==============

  -v, --version          show version number and exit
  -h, --help             show this help text and exit
  -p, --port PORT        port server listens to (default 5432)
  -t, --timeout TIME     If set, server shuts down automatically
                         after -t seconds of inactivity
                         NOT IMPLEMENTED YET!
  
Command Options
===============

  -e, --encoding ENC     (input) encoding (default UTF-8)
  --output-encoding ENC  output encoding (default to input encoding)
  -l, --language NAME    default pitch name language (default to "nederlands")
  -d <variable=value>    set a variable (see below)


Command options define defaults for the execution of commands triggered by HTTP
requests. These options can be overridden by the individual HTTP request.


HTTP Requests
=============

GET Requests
------------

Some GET requests will be implemented later to retrieve values
or change some server settings based on the URL path.


POST Requests
-------------

The server accepts POST requests without (currently) making use of the URL path.
As the request body it expects a single JSON string with the following elements:

  ``commands`` (mandatory)
         An array with one or more commands to be executed subsequently. 
         Each entry contains:
    
         ``command`` (mandatory): 
               A name for the command. It has to be one out of the list of
               available commands below.
        
         ``args`` (optional):
                If a command requires arguments (e.g. the ``transpose`` command)
                they are given as a single string value.

         ``variables`` (optional): 
                A dictionary of variable assignments. Keys have to be from the 
                list below, and proper value types are checked. If one or more
                variables are given they will be set *before* the command is
                executed. A variable may be modified again before the execution
                of the next command but it is not reset automatically. Giving a
                variable with a value of '' unsets the variable.

  ``options`` (optional)
         A dictionary of option assignments. Keys have to be from the above list 
         of Command Options, taking the long name without the leading hyphens, 
         e.g. ``{ "encoding": "UTF-16" }``.
         If an option is given here it overrides the default option given on the
         command line, but only for the current command.
         
  ``data`` (mandatory)
         A single string containing the LilyPond input document.

The server will try to construct a series of commands from the request, and if
anything is wrong with it send a "Bad Request" message with HTTP response code 400.

Response Object
---------------

If the commands execute successfully the response body will contain a serialized
JSON object with the following elements:

  ``info``
         An array of entries with the result of "info" commands (see below).
         Each entry has a ``command`` and an ``info`` field.
         
  ``doc``
         An object with two fields:
         
         ``content``
                A string with the content of the document with all "edit" commands applied
                consecutively. (If no edit commands have been specified this contains the
                original input.
         
         ``commands``
                An array with the names of the commands that have been applied.
  
  ``exports``
         An array with entries for each applied "export" command.
         Each entry has the following fields:
  
         ``doc``
                A string with the content of the converted/exported document
  
         ``command``
                The name of the applied command 

Commands
--------

There are three types of commands whose results are handled independently:

    - "info" commands retrieve metadata from the input document
    - "edit" commands modify the document, subsequent edit commands cascade the
      modifications
    - "export" commands that convert the input to another format.
      Subsequent commands are not affected by the result of export commands.

  
Informative commands that return information and do not change the file:

  ``mode``
         print the mode (guessing if not given) of the document
  
  ``version``
         print the LilyPond version, if set in the document

  ``language``
         print the pitch name language, if set in the document
  
Commands that modify the input:

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


Commands that convert the input to another format:

  ``musicxml``
         convert to MusicXML (in development, far from complete)

  ``highlight``
         export the document as syntax colored HTML



Variables
---------

The following variables can be set to influence the behaviour of commands.
If there is a default value, it is written between brackets:

  ``mode`` 
         mode of the input to read (default automatic) can be one
         of: lilypond, scheme, latex, html, docbook, texinfo.
  
  ``encoding`` [UTF-8]
         encoding to read (also set by -e argument)

  ``default-language`` [nederlands]
         the pitch names language to use by default, when not specified
         otherwise in the document

  ``output-encoding``
         encoding to write (defaults to ``encoding``, also
         set by the ``--output-encoding`` argument)

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



Examples
========

Here is the basic invocation, listening on port 5432::

  ly-server

Specifying port and a timeout::

  ly-server -p 4000 -t 5000
  
Sample Requests
---------------

The simplest request, just applying one edit command. In this case the result
will be in ``result['doc']['content']``::

    {
        'commands': [
            {
                'command': 'indent'
            }
        ],
        'data' : "\\relative c' { c ( d e f ) }"
    }

Another simple request, this time applying an "info" command. The result will
be in ``result['info']``, containing ``lilypond`` in the ``info`` field and
``mode`` in the ``command`` field::

    {
        'commands': [
            {
                'command': 'mode'
            }
        ],
        'data' : "\\relative c' { c ( d e f ) }"
    }
    
And a more complex example. This will first transpose the document and then
convert the transposed version independently to highlighted HTML and MusicXML.
Additionally it will retrieve the mode. This time the result will be in all
three places: the transposed document in ``doc.content``, the mode in 
``info.info``, and HTML and MusicXML in ``exports[0].doc`` and ``exports[1].doc``.::

    {
        'commands': [
            {
                'command': 'transpose',
                'args': 'c d'
            },
            {
                'command': 'highlight',
                'variables': { 'full-html': 'false' }
            },
            { 'command': 'musicxml' },
            { 'command': 'mode' },
        ],
        'options': {
            'language': "deutsch"
        },
        'data': "\\relative c' { c4 ( d e ) }"
    }

"""
