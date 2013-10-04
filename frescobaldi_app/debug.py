#! python
# This module helps with debugging Frescobaldi.
#
# Start a Python shell
# Enter: from frescobaldi_app.debug import *
# This runs Frescobaldi, installs some nice __repr__() methods, connects some
# signals to debug-print functions, and imports the most important modules such
# as app.


try:
    from . import main
    del main
except (ImportError, ValueError):
    pass # this was a reload()


import app
import document


def setup():
    def doc_repr(self):
        index = app.documents.index(self)
        return '<Document #{0} "{1}">'.format(index, self.url().toString())
    document.Document.__repr__ = doc_repr

    # more to add...
    

setup()
del setup

