import os
import sys
from distutils.core import setup
from frescobaldi_app import info

def packagelist(directory):
    """Returns a sorted list with package names for all packages under the given directory."""
    return list(sorted(root.replace(os.sep, '.')
        for root, dirs, files in os.walk(directory)
        if '__init__.py' in files))

scripts = ['frescobaldi']
packages = packagelist('frescobaldi_app')
package_data = {
    'frescobaldi_app.css': ['*.png'],
    'frescobaldi_app.help': ['*.png'],
    'frescobaldi_app.hyphdicts': ['*.dic'],
    'frescobaldi_app.icons': [
        '*.ico',
        '*.svg',
        '*x*/*.png',
        'Tango/index.theme',
        'Tango/scalable/*.svg',
        'TangoExt/index.theme',
        'TangoExt/scalable/*.svg',
    ],
    'frescobaldi_app.layoutcontrol': ['*.ly', '*.ily'],
    'frescobaldi_app.po': ['*.mo'],
    'frescobaldi_app.scorewiz': ['*.png'],
    'frescobaldi_app.splashscreen': ['*.png'],
    'frescobaldi_app.svgview': ['*.js'],
    'frescobaldi_app.symbols': ['*.svg'],
    'frescobaldi_app.userguide': ['*.md', '*.png'],
}

if sys.platform.startswith('win'):
    scripts.append('frescobaldi-wininst.py')
    data_files = []
else:
    data_files = [
        ('share/icons/hicolor/scalable/apps', ['frescobaldi_app/icons/frescobaldi.svg']),
        ('share/applications', ['frescobaldi.desktop']),
        ('share/man/man1', ['frescobaldi.1']),
    ]

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: MacOS X',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: Qt',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: Czech',
    'Natural Language :: Dutch',
    'Natural Language :: English',
    'Natural Language :: French',
    'Natural Language :: Galician',
    'Natural Language :: German',
    'Natural Language :: Italian',
    'Natural Language :: Polish',
    'Natural Language :: Portuguese (Brazilian)',
    'Natural Language :: Russian',
    'Natural Language :: Spanish',
    'Natural Language :: Turkish',
    'Natural Language :: Ukranian',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Graphics',
    'Topic :: Text Editors',
]

setup(
    name = info.name,
    version = info.version,
    description = info.description,
    long_description = info.long_description,
    maintainer = info.maintainer,
    maintainer_email = info.maintainer_email,
    url = info.url,
    license = info.license,
    
    scripts = scripts,
    packages = packages,
    package_data = package_data,
    data_files = data_files,
    classifiers = classifiers,
)

