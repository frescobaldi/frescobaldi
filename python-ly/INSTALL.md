Installing
==========

This package uses a distutils setup script. As the module is written in pure
Python, no build procedure is needed. You can install python-ly using:

    python setup.py install


If you want to install into /usr instead of /usr/local:

    python setup.py install --prefix=/usr


If you have a Debian-based system such as Ubuntu, and you get an error
message like "ImportError: No module named ly.cli.main", try:

    python setup.py install --install-layout=deb


See the distutils documentation for more install options.

