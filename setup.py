import os
import sys
from frescobaldi_app import appinfo

try:
    from setuptools import setup
    USE_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    USE_SETUPTOOLS = False


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
    'frescobaldi_app.svgview': ['*.js', '*.html'],
    'frescobaldi_app.symbols': ['*.svg'],
    'frescobaldi_app.userguide': ['*.md', '*.png'],
}
options = {
    'sdist': {
        'force_manifest': 1,
    }
}

if sys.platform.startswith('win'):
    scripts.append('windows/frescobaldi-wininst.py')
    options['bdist_wininst'] = {
        'install_script': 'windows/frescobaldi-wininst.py',
        'bitmap': 'windows/frescobaldi-wininst.bmp',
    }
    data_files = []
else:
    data_files = [
        ('share/icons/hicolor/scalable/apps', ['frescobaldi_app/icons/frescobaldi.svg']),
        ('share/applications', ['frescobaldi.desktop']),
        ('share/man/man1', ['frescobaldi.1']),
    ]

setup_extra_args = {}
if USE_SETUPTOOLS:
    setup_extra_args['install_requires'] = ['python-ly', 'python-poppler-qt5']

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: MacOS X',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications :: Qt',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    # Natural Language :: Chinese (Hong Kong) is not yet accepted by pypi
    #'Natural Language :: Chinese (Hong Kong)',
    'Natural Language :: Chinese (Simplified)',
    'Natural Language :: Chinese (Traditional)',
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
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Graphics',
    'Topic :: Text Editors',
]

setup(
    name = appinfo.name,
    version = appinfo.version,
    description = appinfo.description,
    long_description = appinfo.long_description,
    maintainer = appinfo.maintainer,
    maintainer_email = appinfo.maintainer_email,
    url = appinfo.url,
    license = appinfo.license,

    scripts = scripts,
    packages = packages,
    package_data = package_data,
    data_files = data_files,
    classifiers = classifiers,
    options = options,
    **setup_extra_args
)

