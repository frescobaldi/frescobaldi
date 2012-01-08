#! python

# Freezes Frescobaldi to a standalone application without
# needing to install any dependencies

import imp
import os
import shutil
import sys

from cx_Freeze import Executable, Freezer

# where to build the frozen program folder
target_dir = 'frozen'

# find pypm by adding the dir of pygame to sys.path
file_handle, path, desc = imp.find_module('pygame')
sys.path.append(path)

includes = [
    'sip',
    'PyQt4.QtCore',
    'PyQt4.QtGui',
    'PyQt4.QtWebKit',
    'PyQt4.QtNetwork',
    'PyQt4.QtSvg',
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
    base = 'Win32GUI', # no console
)

f = Freezer(
    [frescobaldi],
    includes = includes,
    excludes = excludes,
    targetDir = target_dir,
    copyDependentFiles = True,
    compress = False,
    # silent = True,
)

f.Freeze()

# copy over pyqt4 imageformat plugins
file_handle, path, desc = imp.find_module('PyQt4')
img_formats = os.path.join(path, 'plugins', 'imageformats')
img_formats_target = os.path.join(target_dir, 'imageformats')
shutil.rmtree(img_formats_target, ignore_errors = True)
shutil.copytree(img_formats, img_formats_target)

# copy the frescobaldi_app directory, TODO: bytecompile?
f_app = os.path.join(target_dir, 'frescobaldi_app')
shutil.rmtree(f_app, ignore_errors=True)
shutil.copytree('frescobaldi_app', f_app, ignore=shutil.ignore_patterns('*~'))

