#! python

# Freezes Frescobaldi to a standalone application without
# needing to install any dependencies

import imp
import sys

from cx_Freeze import Executable, Freezer

# find pypm by adding the dir of pygame to sys.path
file_handle, path, desc = imp.find_module('pygame')
sys.path.append(path)


includes = [
    'sip',
    'PyQt4.QtCore',
    'PyQt4.QtGui',
    'PyQt4.QtWebKit',
    'PyQt4.QtNetwork',
    'popplerqt4',
    'pypm',
    
    '__future__',
    'contextlib',
    'difflib',
    'fractions',
    'glob',
    'json',
    'itertools',
    'functools',
    'optparse',
    'os',
    're',
    'sys',
    'shutil',
    'struct',
    'subprocess',
    'traceback',
    'types',
    'unicodedata',
    'weakref',
]

excludes = [
    'frescobaldi_app',  # we'll add this one manually
    
]

frescobaldi = Executable(
    'frescobaldi',
    icon = 'frescobaldi_app/icons/frescobaldi.ico',
    appendScriptToExe = True,
    #base = 'Win32GUI', # no console
)

f = Freezer(
    [frescobaldi],
    includes = includes,
    excludes = excludes,
    targetDir = 'frozen',
    copyDependentFiles = True,
    compress = False,
    # silent = True,
)

f.Freeze()

