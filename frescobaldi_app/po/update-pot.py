#! python

# This small script creates a POT file for the translations by extracting all messages
# from Python source files.

# Usage:
# python update-pot.py


import os
import subprocess
import sys

from frescobaldi_app import info

command = [
    'xgettext',
    '--language=python',
    '--output={0}.pot'.format(info.name),
    '--package-name={0}'.format(info.name),
    '--package-version={0}'.format(info.version),
    '--msgid-bugs-address={0}'.format(info.maintainer_email),
    '--keyword',                # empty the default keyword list
    '--keyword=_:1c,2,3,4t',    # context, message, plural, count
    '--keyword=_:1,2,3t',       # message, plural, count
    '--keyword=_:1c,2,2t',      # context, message
    '--keyword=_:1,1t',         # message
    '--add-comments=L10N',
]

for root, dirs, files in sorted(os.walk('..')):
    for f in sorted(files):
        if f.endswith('.py') and f[0] != '.':
            command.append(os.path.join(root, f))

sys.exit(subprocess.call(command))
