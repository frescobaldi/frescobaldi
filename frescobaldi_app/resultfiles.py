# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
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
Finds out which files are created by running the engraver.
"""

from __future__ import unicode_literals

import itertools
import glob
import os

import app
import documentinfo
import jobmanager
import plugin
import util


def results(document):
    return Results.instance(document)


# Set the basenames of the resulting documents to expect when a job starts
@app.jobStarted.connect
def _init_basenames(document):
    results(document).saveDocumentInfo()
    


class Results(plugin.DocumentPlugin):
    """Can be queried to get the files created by running the engraver (LilyPond) on our document."""
    def __init__(self, document):
        self._jobfile = None
        self._basenames = None
        document.saved.connect(self.forgetDocumentInfo)
        
    def saveDocumentInfo(self):
        """Takes over some vital information from a DocumentInfo instance.
        
        The file a job is run on and the basenames expected to be created are saved.
        When the user saves a Document after a Job has run, this information is 'forgotten' again.
        
        Otherwise the results of a Job would not be seen if the user starts a Job and then
        saves the Document while the job is still running.  The Job uses the scratcharea if the
        document was modified but saving it would result in DocumentInfo.jobinfo()[0] pointing
        to the real document instead.
        
        """
        info = documentinfo.info(self.document())
        self._jobfile = info.jobinfo()[0]
        self._basenames = info.basenames()

    def forgetDocumentInfo(self):
        """Called when the user saves a Document.
        
        'Forgets' the basenames and job filename if set, but only if no job is currently running.
        
        """
        if not jobmanager.isRunning(self.document()):
            self._jobfile = None
            self._basenames = None
            
    def jobfile(self):
        """Returns the file that is currently being, or will be, engraved."""
        if self._jobfile is None:
            return documentinfo.info(self.document()).jobinfo()[0]
        return self._jobfile

    def basenames(self):
        """Returns the list of basenames the last or running Job is expected to create."""
        if self._basenames is None:
            return documentinfo.info(self.document()).basenames()
        return self._basenames

    def files(self, extension = '*', newer = True):
        """Returns a list of existing files matching our basenames and the given extension.
        
        First the files basename + extension are returned,
        then basename + '-[0-9]+' + extension,
        then basename + '-.+' + extension.
        
        If newer is True (the default), only files that are newer than the jobfile() are returned.
        
        """
        jobfile = self.jobfile()
        if jobfile:
            files = util.files(self.basenames(), extension)
            if newer:
                try:
                    mtime = os.path.getmtime(jobfile)
                    files = filter(lambda fname: os.path.getmtime(fname) >= mtime, files)
                except (OSError, IOError):
                    pass
            return list(files)
        return []
    
    def is_newer(self, filename):
        """Return True if the given (generated) file is newer than the jobfile().
        
        Also return True if the mtime of one of the files could not be read.
        
        """
        jobfile = self.jobfile()
        if jobfile:
            try:
                return os.path.getmtime(filename) > os.path.getmtime(jobfile)
            except (OSError, IOError):
                pass
        return True
        
    def currentDirectory(self):
        """Returns the directory the document resides in.
        
        Returns the temporary directory if that was used last.
        
        """
        directory = os.path.dirname(self.jobfile())
        if os.path.isdir(directory):
            return directory


