# This module helps with debugging Frescobaldi.
#
# Start a Python shell
# Enter: from frescobaldi_app.debug import *
# This runs Frescobaldi, installs some nice __repr__() methods, connects some
# signals to debug-print functions, and imports the most important modules such
# as app.

from __future__ import print_function

import sys

from . import toplevel
toplevel.install()

import main
import app
import document


def doc_repr(self):
    index = app.documents.index(self)
    return '<Document #{0} "{1}">'.format(index, self.url().toString())
document.Document.__repr__ = doc_repr

@app.documentCreated.connect
def f(doc):
    print("created:", doc)

@app.documentLoaded.connect
def f(doc):
    print("loaded:", doc)

@app.documentClosed.connect
def f(doc):
    print("closed:", doc)

@app.jobStarted.connect
def f(doc, job):
    print('job started:', doc)
    print(job.command)

@app.jobFinished.connect
def f(doc, job, success):
    print('job finished', doc)
    print('success:', success)


# more to add...


# delete unneeded stuff
del f, doc_repr

def modules():
    """Print the list of loaded modules."""
    print('\n'.join(v.__name__ for k, v in sorted(sys.modules.items()) if v is not None))


# avoid builtins._ being overwritten
sys.displayhook = app.displayhook

# instantiate app and create a mainwindow, etc
app.instantiate()
main.main()
app.appStarted()

# be friendly and import Qt stuff
from PyQt5.QtCore import *
from PyQt5.QtGui import *


