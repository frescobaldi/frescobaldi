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
Finds out which files are created by running the engraver.
"""


import app
import documentinfo
import jobmanager
import plugin


def results(document):
    return Results.instance(document)


# Set the basenames of the resulting documents to expect when a job starts
@app.jobStarted.connect
def _init_basenames(document):
    results(document).setBasenames(documentinfo.info(document).basenames())
    


class Results(plugin.DocumentPlugin):
    """Can be queried to get the files created by running the engraver (LilyPond) on our document."""
    def __init__(self, document):
        self._basenames = None
        document.saved.connect(self.documentSaved)
        
    def documentSaved(self):
        """Called when the user saves a Document.
        
        'Forgets' the basenames if set, but only if no job is currently running.
        
        """
        if not jobmanager.isRunning(self.document()):
            self._basenames = None
            
    def basenames(self):
        """Returns the list of basenames the last or running Job is expected to create."""
        if self._basenames is None:
            return documentinfo.info(self.document()).basenames()
        return self._basenames
    
    def setBasenames(self, basenames):
        """Sets our basenames. Esp. used when a job starts."""
        self._basenames = basenames




