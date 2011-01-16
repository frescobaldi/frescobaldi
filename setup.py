from distutils.core import setup
from frescobaldi_app import info

setup(
    name = info.name,
    version = info.version,
    description = info.description,
    long_description = info.long_description,
    maintainer = info.maintainer,
    maintainer_email = info.maintainer_email,
    url = info.url,
    license = info.license,
    
    scripts = ['frescobaldi'],
    packages = [
        'frescobaldi_app',
        'frescobaldi_app.hyphdicts',
        'frescobaldi_app.icons',
        'frescobaldi_app.language_names',
        'frescobaldi_app.ly',
        'frescobaldi_app.ly.tokenize',
        'frescobaldi_app.po',
        'frescobaldi_app.preferences',
        'frescobaldi_app.symbols',
        'frescobaldi_app.widgets',
    ],
    package_data = {
        'frescobaldi_app.hyphdicts': ['*.dic'],
        'frescobaldi_app.icons': ['*.svg', '*.png'],
        'frescobaldi_app.po': ['*.mo'],
        'frescobaldi_app.symbols': ['*.svg'],
    },
    data_files = [
        ('share/icons/hicolor/scalable/apps', ['frescobaldi_app/icons/frescobaldi.svg']),
        ('share/applications', ['frescobaldi.desktop']),
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Graphics',
    ],
)
