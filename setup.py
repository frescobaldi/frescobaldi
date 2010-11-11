from distutils.core import setup
from frescobaldi_app import info

setup(
    scripts = ['frescobaldi'],
    packages = [
        'frescobaldi_app',
        'frescobaldi_app.po',
        #'frescobaldi_app.ly',
        #'frescobaldi_app.app',
        #'frescobaldi_app.util',
        #'frescobaldi_app.data',
    ],
    package_data = {
        'frescobaldi_app.po': ['*.mo'],
    },
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)', #FIXME
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Multimedia', #FIXME
    ],
    **dict((k, getattr(info, k)) for k in dir(info) if not k.startswith('_'))
)
