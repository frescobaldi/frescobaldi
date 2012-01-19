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
        '*.svg', '*x*/.png',
        'tango/*.svg', 'tango/*x*/*.png',
        ],
    'frescobaldi_app.po': ['*.mo'],
    'frescobaldi_app.scorewiz': ['*.png'],
    'frescobaldi_app.symbols': ['*.svg'],
}

if sys.platform.startswith('win'):
    scripts.append('frescobaldi-wininst.py')
    data_files = []
else:
    data_files = [
        ('share/icons/hicolor/scalable/apps', ['frescobaldi_app/icons/frescobaldi.svg']),
        ('share/applications', ['frescobaldi.desktop']),
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
    'Natural Language :: Portuguese (Brazilian)'
    'Natural Language :: Russian',
    'Natural Language :: Spanish',
    'Natural Language :: Turkish',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Graphics',
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

