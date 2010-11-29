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
        'frescobaldi_app.po',
        'frescobaldi_app.icons',
        #'frescobaldi_app.ly',
        #'frescobaldi_app.util',
        #'frescobaldi_app.data',
    ],
    package_data = {
        'frescobaldi_app.po': ['*.mo'],
        'frescobaldi_app.icons': ['*.svg', '*.png'],
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
