#! python

# This small script creates a POT file for the translations by extracting all messages
# from Python source files.

# Usage:
# python update-pot.py


import glob
import os
import subprocess
import sys

sys.path.insert(0, "..")
import info
import md2pot

# 1. create a temp POT file for the messages, harvested from the source code
command = [
    'xgettext',
    '--language=python',
    '--output=temp1.pot',
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

result = subprocess.call(command)

# 2. create a temp POT file for the user guide
md2pot.md2pot('temp2.pot', glob.glob('../userguide/*.md'))

# 3. uniq that one
subprocess.call('msguniq -t UTF-8 -o temp3.pot temp2.pot'.split())

# 4. merge the two
subprocess.call('msgcat temp1.pot temp3.pot -o {0}.pot'.format(info.name).split())

# 5. remove the unneeded temp files
os.remove('temp1.pot')
os.remove('temp2.pot')
os.remove('temp3.pot')


