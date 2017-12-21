#!/usr/bin/env python
# coding=utf-8

"""
A setup file to build Frescobaldi.app with py2app.

Use the '-h' flag to see the usage notes.
"""
from __future__ import print_function

import argparse
import os
import sys
from setuptools import setup
import shutil
from subprocess import Popen

# Python 2 text strings: basestring = str (ASCII) + unicode (Unicode)
# Python 3 text strings: str (Unicode)
# See https://docs.python.org/3/howto/pyporting.html for details.
try:
    string_types = basestring
except NameError:
    string_types = str

macosx = os.path.realpath(os.path.dirname(__file__))
root = os.path.dirname(macosx)

sys.path.insert(0, root)

from frescobaldi_app import toplevel
toplevel.install()
import appinfo
try:
    from portmidi import pm_ctypes
    dylib_name = pm_ctypes.dll_name
except ImportError:
    dylib_name = None

icon = '{0}/icons/{1}.icns'.format(macosx, appinfo.name)
ipstrings = '{0}/app_resources/InfoPlist.strings'.format(macosx)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--force', action = 'store_true', \
  help = 'force execution even if SCRIPT does not exist')
parser.add_argument('-v', '--version', \
  help = 'version string for the application bundle, \
  visible e.g. in \'Get Info\' and in \'Open with...\'', default = appinfo.version)
parser.add_argument('-s', '--script', \
  help = 'path of {0}\'s main script; you should use an absolute path, \
  so that the application bundle can be moved to another \
  directory'.format(appinfo.appname), default = '{0}/{1}'.format(root, appinfo.name))
parser.add_argument('-a', '--standalone', action = 'store_true', \
  help = 'build a standalone application bundle \
  (WARNING: some manual steps are required after the execution of this script)')
parser.add_argument('-p', '--portmidi', \
  help = 'full path of PortMIDI library (used only with \'-a\')', \
  default = dylib_name)
parser.add_argument('-r', '--arch', \
  help = 'architecture set to include, e.g. i386, x86_64, intel; \
  if the value is None, the architecture of the current Python binary is used \
  (used only with \'-a\')')
args = parser.parse_args()

if not (os.path.isfile(args.script) or args.force):
    sys.exit('Error: \'{0}\' does not exist or is not a file.\n\
If you really want to point the application bundle to \'{0}\',\n\
use the \'-f\' or \'--force\' flag.'.format(args.script))

if args.standalone and not (isinstance(args.portmidi, string_types) and os.path.isfile(args.portmidi)):
    sys.exit('Error: \'{0}\' does not exist or is not a file.'.format(args.portmidi))

plist = dict(
    CFBundleName                  = appinfo.appname,
    CFBundleDisplayName           = appinfo.appname,
    CFBundleShortVersionString    = args.version,
    CFBundleVersion               = args.version,
    CFBundleExecutable            = appinfo.appname,
    CFBundleIdentifier            = 'org.{0}.{0}'.format(appinfo.name),
    CFBundleIconFile              = '{0}.icns'.format(appinfo.name),
    NSHumanReadableCopyright      = u'Copyright © 2008-2014 Wilbert Berendsen.',
    CFBundleDocumentTypes         = [
        {
            'CFBundleTypeExtensions': ['ly', 'lyi', 'ily'],
            'CFBundleTypeName': 'LilyPond file',
            'CFBundleTypeRole': 'Editor',
        },
        {
            'CFBundleTypeExtensions': ['tex', 'lytex', 'latex'],
            'CFBundleTypeName': 'LaTeX file',
            'CFBundleTypeRole': 'Editor',
        },
        {
            'CFBundleTypeExtensions': ['docbook', 'lyxml'],
            'CFBundleTypeName': 'DocBook file',
            'CFBundleTypeRole': 'Editor',
        },
        {
            'CFBundleTypeExtensions': ['html'],
            'CFBundleTypeName': 'HTML file',
            'CFBundleTypeRole': 'Editor',
            'LSItemContentTypes': ['public.html']
        },
        {
            'CFBundleTypeExtensions': ['xml'],
            'CFBundleTypeName': 'XML file',
            'CFBundleTypeRole': 'Editor',
            'LSItemContentTypes': ['public.xml']
        },
        {
            'CFBundleTypeExtensions': ['itely', 'tely', 'texi', 'texinfo'],
            'CFBundleTypeName': 'Texinfo file',
            'CFBundleTypeRole': 'Editor',
        },
        {
            'CFBundleTypeExtensions': ['scm'],
            'CFBundleTypeName': 'Scheme file',
            'CFBundleTypeRole': 'Editor',
        },
        {
            'CFBundleTypeExtensions': ['*'],
            'CFBundleTypeName': 'Text file',
            'CFBundleTypeRole': 'Editor',
            'LSItemContentTypes': ['public.text']
        }
    ]
)

options = {
    'argv_emulation': True,
    'plist': plist
}

if args.standalone:
    options.update({
        'packages': ['frescobaldi_app'],
        'frameworks': [args.portmidi],
    })
    if args.arch:
        options.update({
            'arch': args.arch
        })
    try:
        patchlist = [f for f in os.listdir('patch') if f.endswith(".diff")]
    except OSError:
        patchlist = []
    for patchfile in patchlist:
        with open('patch/{0}'.format(patchfile), 'r') as input:
            Popen(["patch", "-d..", "-p0"], stdin=input)
else:
    options.update({
        'semi_standalone': True,
        'alias': True
    })

setup(
    app = [args.script],
    name = appinfo.appname,
    options = {'py2app': options},
    setup_requires = ['py2app'],
    script_args = ['py2app']
)

app_resources = 'dist/{0}.app/Contents/Resources'.format(appinfo.appname)
icon_dest = '{0}/{1}.icns'.format(app_resources, appinfo.name)
print('copying file {0} -> {1}'.format(icon, icon_dest))
shutil.copyfile(icon, icon_dest)
os.chmod(icon_dest, 0o0644)
locales = ['cs', 'de', 'en', 'es', 'fr', 'gl', 'it', 'nl', 'pl', 'pt', 'ru', 'tr', 'uk', 'zh_CN', 'zh_HK', 'zh_TW']
for l in locales:
    app_lproj = '{0}/{1}.lproj'.format(app_resources, l)
    os.mkdir(app_lproj, 0o0755)
    ipstrings_dest = '{0}/InfoPlist.strings'.format(app_lproj)
    print('copying file {0} -> {1}'.format(ipstrings, ipstrings_dest))
    shutil.copyfile(ipstrings, ipstrings_dest)
    os.chmod(ipstrings_dest, 0o0644)

if args.standalone:
    if patchlist:
        print('reversing patches:')
    for patchfile in patchlist:
        with open('patch/{0}'.format(patchfile), 'r') as input:
            Popen(["patch", "-R", "-d..", "-p0"], stdin=input)
    print('removing file {0}/qt.conf'.format(app_resources))
    os.remove('{0}/qt.conf'.format(app_resources))
    imageformats_dest = 'dist/{0}.app/Contents/PlugIns/imageformats'.format(appinfo.appname)
    print('creating directory {0}'.format(imageformats_dest))
    os.makedirs(imageformats_dest, 0o0755)
    print("""
WARNING: To complete the creation of the standalone application bundle \
you need to perform the following steps manually:

- copy libqsvg.dylib from Qt's 'plugins/imageformats' directory to '{1}',
- execute Qt's macdeployqt tool on dist/{0}.app \
(you can safely ignore the error about the failed copy of libqsvg.dylib).
""".format(appinfo.appname, imageformats_dest))
