#! python

# This script freezes Frescobaldi to a standalone application without
# needing to install any dependencies.
#
# Usage:
# C:\Python27\Python freeze.py
#
# How it works:
# It creates, using cx_Freeze, a frescobaldi executable inside the frozen/
# directory, along with all used (manually specified) Python modules.
# Then the whole frescobaldi_app directory is copied and the Python scripts
# byte-compiled.
# Finally, an installer is created using the Inno Setup console-mode compiler.

# the Inno Setup console-mode compiler
iscc = 'c:\\Program Files\\Inno Setup 5\\ISCC'

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
    'PyQt5.QtWebKit',
    'PyQt5.QtNetwork',
    'PyQt5.QtSvg',
    'PyQt5.QtXml',
    'popplerqt5',
    'pypm',

    '__future__',
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
    icon = '../frescobaldi_app/icons/frescobaldi.ico',
    appendScriptToExe = True,
    base = 'Win32GUI', # no console
)

f = Freezer(
    [frescobaldi],
    includes = includes,
    packages = packages,
    excludes = excludes,
    targetDir = target_dir,
    copyDependentFiles = True,
    compress = False,
    # silent = True,
)

f.Freeze()

def copy_plugins(name):
    """Copies a folder from the Qt4 plugins directory."""
    path = imp.find_module('PyQt5')[1]
    folder = os.path.join(path, 'plugins', name)
    target = os.path.join(target_dir, name)
    shutil.rmtree(target, ignore_errors = True)
    shutil.copytree(folder, target)

# copy Qt4 imageformat plugins
copy_plugins('imageformats')

# copy Qt4 iconengine plugins
copy_plugins('iconengines')

# copy the frescobaldi_app directory
subprocess.call(
    [sys.executable, 'setup.py', 'build_py',
     '--build-lib', os.path.join('windows', target_dir), '--compile'],
    cwd="..")

# make an Inno Setup installer
inno_script = b'''
[Setup]
AppName=Frescobaldi
AppVersion={version}
AppVerName=Frescobaldi {version}
AppPublisher={author}
AppPublisherURL={homepage}
AppComments={comments}

DefaultDirName={{pf}}\\Frescobaldi
DefaultGroupName=Frescobaldi
UninstallDisplayIcon={{app}}\\frescobaldi.exe
Compression=lzma2
SolidCompression=yes

SourceDir={target}\\
OutputDir=..\\..\\dist\\
OutputBaseFilename="Frescobaldi Setup {version}"
SetupIconFile=frescobaldi_app\\icons\\frescobaldi.ico
LicenseFile=..\\..\\COPYING
WizardImageFile=..\\frescobaldi-wininst.bmp
WizardImageStretch=no

[InstallDelete]
Type: filesandordirs; Name: "{{app}}\\frescobaldi_app"

[Files]
Source: "*.*"; DestDir: "{{app}}"; Flags: recursesubdirs;

[Icons]
Name: "{{group}}\Frescobaldi"; Filename: "{{app}}\\frescobaldi.exe";

[Tasks]
Name: assocly; Description: "{{cm:AssocFileExtension,Frescobaldi,.ly}}";

[Registry]
Root: HKCR; Subkey: "LilyPond\\shell\\frescobaldi";\
 ValueType: string; ValueName: ""; ValueData: "Edit with &Frescobaldi...";\
 Flags: uninsdeletekey
Root: HKCR; Subkey: "LilyPond\\shell\\frescobaldi\\command";\
 ValueType: string; ValueName: ""; ValueData: """{{app}}\\frescobaldi.exe"" ""%1"""
Tasks: assocly; Root: HKCR; Subkey: "LilyPond\\shell";\
 ValueType: string; ValueName: ""; ValueData: "frescobaldi";

[Run]
Filename: "{{app}}\\frescobaldi.exe";\
 Description: {{cm:LaunchProgram,Frescobaldi}};\
 Flags: postinstall nowait skipifsilent;

'''.format(
    version=appinfo.version,
    homepage=appinfo.url,
    author=appinfo.maintainer,
    comments=appinfo.description,
    target=target_dir,
)

subprocess.Popen([iscc, '-'], stdin=subprocess.PIPE).communicate(inno_script)

