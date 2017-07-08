#! python

# This script freezes Frescobaldi to a standalone application without
# needing to install any dependencies.
#
# Usage:
# C:\Python35\Python freeze.py
#
# How it works:
# It creates, using cx_Freeze, a frescobaldi executable inside the frozen/
# directory, along with all used (manually specified) Python modules.
# Then the whole frescobaldi_app directory is copied and the Python scripts
# byte-compiled.
# Finally, an installer is created using the Inno Setup console-mode compiler.

# the Inno Setup console-mode compiler
iscc = 'C:\Program Files (x86)\Inno Setup 5\ISCC'

# where to build the frozen program folder
target_dir = 'frozen'

# import standard modules and cx_Freeze
import imp
import os
import py_compile
import shutil
import subprocess
import sys
from cx_Freeze import Executable, Freezer

# access the frescobaldi_app package
sys.path.insert(0, '..')

# access meta-information such as version, etc.
from frescobaldi_app import appinfo

# find pypm by adding the dir of pygame to sys.path
sys.path.append(imp.find_module('pygame')[1])

includes = [
    'sip',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebEngine',
    'PyQt5.QtNetwork',
    'PyQt5.QtSvg',
    'PyQt5.QtXml',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'popplerqt5',
	'freetype',
    'pypm',

    'argparse',
    'bisect',
    'contextlib',
    'difflib',
    'fractions',
    'glob',
    'json',
    'itertools',
    'functools',
    'optparse',
    'os',
    'platform',
    're',
    'sys',
    'shutil',
    'struct',
    'subprocess',
    'traceback',
    'types',
    'unicodedata',
    'weakref',
    'xml.etree.ElementTree',
]



packages = [
    'ly',
]

excludes = [
    'frescobaldi_app',  # we'll add this one manually
]

# be sure the target dir is removed
shutil.rmtree(target_dir, ignore_errors = True)

frescobaldi = Executable(
    '../frescobaldi',
	base = 'Win32GUI', # no console
    icon = '../frescobaldi_app/icons/frescobaldi.ico',
#    appendScriptToExe = True,

)

f = Freezer(
    [frescobaldi],
    includes = includes,
    packages = packages,
    excludes = excludes,
    targetDir = target_dir,
    # copyDependentFiles = True,
    compress = False,
    # silent = True,
    includeMSVCR = True,
)

f.Freeze()

def copy_plugins(name):
    """Copies a folder from the Qt5 plugins directory."""
    path = imp.find_module('PyQt5')[1]
    folder = os.path.join(path, 'qt/plugins', name)
    target = os.path.join(target_dir, name)
    shutil.rmtree(target, ignore_errors = True)
    shutil.copytree(folder, target)

def copy_folder(name):
    """Copies a folder from the Qt5 plugins directory."""
    path = '../'
    folder = os.path.join(path, name)
    target = os.path.join(target_dir, name)
    shutil.rmtree(target, ignore_errors = True)
    shutil.copytree(folder, target)

def copy_file(name):
	"""Copies a folder from the Qt5 plugins directory."""	
	path = '../'
	file = os.path.join(path, name)
	target = os.path.join(target_dir, name)
	shutil.copyfile(file,target)
  


# copy Qt5 imageformat plugins
copy_plugins('imageformats')

# copy Qt5 iconengine plugins
copy_plugins('iconengines')

# copy Qt5 iconengine plugins
copy_plugins('printsupport')

test=os.getcwd()

# copy the frescobaldi_app directory
subprocess.call(
    [sys.executable, 'setup.py', 'build_py',
     '--build-lib', os.path.join('windows', target_dir), '--compile'],
    cwd="..")

subprocess.run([iscc, "/Dhomepage="+appinfo.url , "/Dversion="+appinfo.version , "/Dauthor="+appinfo.maintainer , "/Dcomments="+appinfo.description, "/Dtarget="+target_dir, "setup.iss" ])
