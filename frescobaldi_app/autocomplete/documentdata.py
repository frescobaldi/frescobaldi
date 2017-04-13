# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 - 2014 by Wilbert Berendsen
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
Completions data harvested from a Document.
"""


import itertools
import os

import listmodel
import plugin
import ly.words
import ly.data

from . import completiondata
from . import harvest
from . import util


def doc(document):
    """Returns the DocumentDataSource for the specified Document."""
    return DocumentDataSource.instance(document)


class DocumentDataSource(plugin.DocumentPlugin):
    @util.keep
    def words(self):
        """Returns the list of words in comments, markup etc."""
        return listmodel.ListModel(
            sorted(set(harvest.words(self.document()))))

    @util.keep
    def schemewords(self):
        """Scheme names, including those harvested from document."""
        schemewords = set(itertools.chain(
            ly.data.all_scheme_words(),
            (str(t)
                for t in harvest.schemewords(self.document())
                if len(t) > 2),
            ))
        return listmodel.ListModel(sorted(schemewords))

    @util.keep
    def markup(self, cursor):
        """Completes markup commands and normal text from the document."""
        return listmodel.ListModel(
            ['\\' + w for w in sorted(ly.words.markupcommands)]
            + [ '\\' + w for w in sorted(set(itertools.chain(
                harvest.markup_commands(cursor),
                harvest.include_markup_commands(cursor))))]
            + sorted(set(harvest.words(self.document()))))

    @util.keep
    def scorecommands(self, cursor):
        """Stuff inside \\score { }. """
        return listmodel.ListModel(sorted(set(itertools.chain(
            completiondata.score,
            harvest.include_identifiers(cursor),
            harvest.names(cursor)))), display = util.command)

    @util.keep
    def bookpartcommands(self, cursor):
        """Stuff inside \\bookpart { }. """
        return listmodel.ListModel(sorted(set(itertools.chain(
            completiondata.bookpart,
            harvest.include_identifiers(cursor),
            harvest.names(cursor)))), display = util.command)

    @util.keep
    def bookcommands(self, cursor):
        """Stuff inside \\book { }. """
        return listmodel.ListModel(sorted(set(itertools.chain(
            completiondata.book,
            harvest.include_identifiers(cursor),
            harvest.names(cursor)))), display = util.command)


    @util.keep
    def musiccommands(self, cursor):
        return listmodel.ListModel(sorted(set(itertools.chain(
            ly.words.lilypond_keywords,
            ly.words.lilypond_music_commands,
            ly.words.articulations,
            ly.words.ornaments,
            ly.words.fermatas,
            ly.words.instrument_scripts,
            ly.words.repeat_scripts,
            harvest.include_identifiers(cursor),
            harvest.names(cursor)))), display = util.command)

    @util.keep
    def lyriccommands(self, cursor):
        return listmodel.ListModel(sorted(set(itertools.chain(
            ('set stanza = ', 'set', 'override', 'markup', 'notemode', 'repeat'),
            harvest.include_identifiers(cursor),
            harvest.names(cursor)))), display = util.command)

    def includenames(self, cursor, directory=None):
        """Finds files relative to the directory of the cursor's document.

        If the document has a local filename, looks in that directory,
        also in a subdirectory of it, if the directory argument is given.

        Then looks recursively in the user-set include paths,
        and finally in LilyPond's own ly/ folder.

        """
        names = []
        # names in current dir
        path = self.document().url().toLocalFile()
        if path:
            basedir = os.path.dirname(path)
            if directory:
                basedir = os.path.join(basedir, directory)
                names.extend(sorted(os.path.join(directory, f)
                    for f in get_filenames(basedir, True)))
            else:
                names.extend(sorted(get_filenames(basedir, True)))

        # names in specified include paths
        import documentinfo
        for basedir in documentinfo.info(self.document()).includepath():

            # store dir relative to specified include path root
            reldir = directory if directory else ""
            # look for files in the current relative directory
            for f in sorted(get_filenames(os.path.join(basedir, reldir), True)):
                names.append(os.path.join(reldir, f))

        # names from LilyPond itself
        import engrave.command
        datadir = engrave.command.info(self.document()).datadir()
        if datadir:
            basedir = os.path.join(datadir, 'ly')
            # get the filenames but avoid the -init files here
            names.extend(sorted(f for f in get_filenames(basedir)
                if not f.endswith('init.ly')
                and f.islower()))

        # forward slashes on Windows (issue #804)
        if os.name == "nt":
            names = [name.replace('\\', '/') for name in names]

        return listmodel.ListModel(names)


def get_filenames(path, directories = False):
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                if f and f[0] not in '.~':
                    name, ext = os.path.splitext(f)
                    if ext.lower() in ('.ly', '.lyi', '.ily'):
                        yield f
            if directories:
                for f in dirs:
                    if f and not f.startswith('.'):
                        yield f + os.sep
            return
    except UnicodeDecodeError:
        # this only happens when there are filenames in the wrong encoding,
        # but never ever bug the user about this while typing :)
        pass


