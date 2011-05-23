#! python
# PostInstall script for Frescobaldi on Windows

import sys

from frescobaldi_app.wininst import install, remove

if sys.argv[1] == '-install':
    install()
elif sys.argv[1] == '-remove':
    remove()

