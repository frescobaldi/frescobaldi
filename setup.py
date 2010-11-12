from distutils.core import setup
from frescobaldi_app import info

setup(
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
    **dict((k, getattr(info, k)) for k in dir(info) if not k.startswith('_'))
)
