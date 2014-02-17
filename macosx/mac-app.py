#!/usr/bin/env python
# coding=utf-8

"""
A setup file to build Frescobaldi.app with py2app.

Use the '-h' flag to see the usage notes.
"""

import argparse
import os
import sys
from setuptools import setup
import shutil

macosx = os.path.realpath(os.path.dirname(__file__))
root = os.path.dirname(macosx)

sys.path.append(root)

from frescobaldi_app import info

icon = '{0}/icons/{1}.icns'.format(macosx, info.name)
ipstrings = '{0}/app_resources/InfoPlist.strings'.format(macosx)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--force', action = 'store_true', \
  help = 'force execution even if SCRIPT does not exist')
parser.add_argument('-v', '--version', \
  help = 'version string for the application bundle, \
  visible e.g. in \'Get Info\' and in \'Open with...\'', default = info.version)
parser.add_argument('-s', '--script', \
  help = 'path of {0}\'s main script; you should use an absolute path, \
  so that the application bundle can be moved to another \
  directory'.format(info.appname), default = '{0}/{1}'.format(root, info.name))
args = parser.parse_args()

if not (os.path.isfile(args.script) or args.force):
    sys.exit('Error: \'{0}\' does not exist or is not a file.\n\
If you really want to point the application bundle to \'{0}\',\n\
use the \'-f\' or \'--force\' flag.'.format(args.script))

plist = dict(
    CFBundleName                  = info.appname,
    CFBundleDisplayName           = info.appname,
    CFBundleShortVersionString    = args.version,
    CFBundleVersion               = args.version,
    CFBundleExecutable            = info.appname,
    CFBundleIdentifier            = 'org.{0}.{0}'.format(info.name),
    CFBundleIconFile              = '{0}.icns'.format(info.name),
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
    'semi_standalone': True,
    'alias': True,
    'plist': plist
}

setup(
    app = [args.script],
    name = info.appname,
    options = {'py2app': options},
    setup_requires = ['py2app'],
    script_args = ['py2app']
)

app_resources = 'dist/{0}.app/Contents/Resources'.format(info.appname)
icon_dest = '{0}/{1}.icns'.format(app_resources, info.name)
shutil.copyfile(icon, icon_dest)
os.chmod(icon_dest, 0644)
locales = ['cs', 'de', 'en', 'es', 'fr', 'gl', 'it', 'nl', 'pl', 'pt', 'ru', 'tr', 'uk']
for l in locales:
    app_lproj = '{0}/{1}.lproj'.format(app_resources, l)
    os.mkdir(app_lproj, 0755)
    ipstrings_dest = '{0}/InfoPlist.strings'.format(app_lproj)
    shutil.copyfile(ipstrings, ipstrings_dest)
    os.chmod(ipstrings_dest, 0644)
