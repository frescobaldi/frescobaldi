# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
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

from __future__ import unicode_literals

"""
Delivers information about a document.
"""

import itertools
import os
import re

from PyQt4.QtCore import QUrl

import ly.tokenize
import app
import tokeniter
import util
import variables


def mode(document, guess=True):
    """Returns the type of document ('lilypond, 'html', etc.).
    
    The mode can be set using the "mode" document variable.
    If guess is True (default), the mode is auto-recognized based on the contents
    if not set explicitly using the "mode" variable. In this case, this function
    always returns an existing mode.
    
    If guess is False, auto-recognizing is not done and the function returns None
    if the mode wasn't set explicitly.
    
    """
    mode = variables.get(document, "mode")
    if mode in ly.tokenize.modes:
        return mode
    if guess:
        return ly.tokenize.guessMode(document.toPlainText())
    

def tokens(document):
    """Iterates over all the tokens in a document, parsing if the document has not yet materialized."""
    if document.materialized():
        return tokeniter.allTokens(document)
    else:
        return ly.tokenize.state(mode(document)).tokens(document.toPlainText())


def version(document):
    """Returns the LilyPond version if set in the document, as a tuple of ints.
    
    First the functions searches inside LilyPond syntax.
    Then it looks at the 'version' document variable.
    Then, if the document is not a LilyPond document, it simply searches for a
    \\version command string, possibly embedded in a comment.
    
    """
    source = tokens(document)
    for token in source:
        if isinstance(token, ly.tokenize.lilypond.Keyword) and token == "\\version":
            for token in source:
                if not isinstance(token, (ly.tokenize.Space, ly.tokenize.Comment)):
                    break
            if token == '"':
                pred = lambda t: t != '"'
            else:
                pred = lambda t: not isinstance(t, ly.tokenize.Space, ly.tokenize.Comment)
            version = ''.join(itertools.takewhile(pred, source))
            return tuple(map(int, re.findall(r"\d+", version)))
    # look at document variables
    version = variables.get(document, "version")
    if version:
        return tuple(map(int, re.findall(r"\d+", version)))
    # parse whole document for non-lilypond documents
    if mode(document) != "lilypond":
        m = re.search(r'\\version\s*"(\d+\.\d+(\.\d+)*)"', document.toPlainText())
        if m:
            return tuple(map(int, m.group(1).split('.')))


def jobinfo(document, create=False):
    """Returns a three tuple(filename, mode, includepath) based on the given document.
    
    If the document is a local file, its contents is checked for the 'master' variable
    to run the engraver on a different file instead. The mode is then also chosen
    based on the contents of that other file.
    
    If no redirecting variables are found and the document is modified, its text
    is saved to a temporary area and that filename is returned. If the 'create'
    argument is False (the default), no temporary file is created, and in that
    case, the existing filename (may be empty) is returned.
    
    If a scratch area is used but the document has a local filename and includes
    other files, the original directory is given in the includepath list.
    
    """
    # Determine the filename to run the engraving job on
    filename = document.url().toLocalFile()
    redir = variables.get(document, "master")
    mode_ = mode(document)
    
    includepath = []
    
    if filename and redir:
        # We have a local filename and the document wants another one as master,
        # find the mode of the other file. If it is loaded in a different document,
        # getting the mode is easy. Otherwise just read part of the file.
        url = document.url().resolved(QUrl(redir))
        filename = url.toLocalFile()
        d = app.findDocument(url)
        if d:
            mode_ = mode(d)
        elif os.path.exists(filename):
            with open(filename) as f:
                text = util.decode(f.read())
            mode_ = variables.variables(text).get("mode")
            if mode_ not in ly.tokenize.modes:
                mode_ = ly.tokenize.guessMode(text)

    elif not filename or document.isModified():
        # We need to use a scratchdir to save our contents to
        import scratchdir
        scratch = scratchdir.scratchdir(document)
        if create:
            scratch.saveDocument()
            if filename:
                for block in tokeniter.allBlocks(document):
                    if "\\include" in tokeniter.tokens(block):
                        includepath.append(os.path.dirname(filename))
                        break
            filename = scratch.path()
        elif scratch.path() and os.path.exists(scratch.path()):
            filename = scratch.path()
    
    return filename, mode_, includepath
    

def includefiles(document, path=()):
    """Returns a set of filenames that are included by the given document.
    
    If a path is given, it must be a list of directories that are also searched
    for files to be included.
    
    """
    files = set()
    basedir = os.path.dirname(document.url().toLocalFile())
    
    def find(source, directory=basedir):
        for token in source:
            if isinstance(token, ly.tokenize.lilypond.Keyword) and token == "\\include":
                for token in source:
                    if not isinstance(token, (ly.tokenize.Space, ly.tokenize.Comment)):
                        break
                if token == '"':
                    f = ''.join(itertools.takewhile(lambda t: t != '"', source))
                    # old include (relative to master file)
                    find_file(os.path.normpath(os.path.join(basedir, f)))
                    # new, recursive, relative include
                    find_file(os.path.normpath(os.path.join(directory, f)))
                    # if path is given, also search there:
                    for p in path:
                        find_file(os.path.normpath(os.path.join(p, f)))
        
    def find_file(filename):
        if os.path.exists(filename) and filename not in files:
            files.add(filename)
            d = app.findDocument(QUrl.fromLocalFile(filename))
            if d:
                source = tokens(d)
            else:
                with open(filename) as f:
                    text = util.decode(f.read())
                mode = variables.variables(text).get("mode")
                if mode not in ly.tokenize.modes:
                    mode = ly.tokenize.guessMode(text)
                source = ly.tokenize.state(mode).tokens(text)
            find(source, os.path.dirname(filename))
    
    find(tokens(document))
    return files


