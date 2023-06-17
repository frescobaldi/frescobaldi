"""

This small script creates a POT file ('frescobaldi.pot') for the translations
by extracting all messages from Python source files.

It also creates a POT file ('userguide.pot') for the translation of all
paragraphs of the user guide.

The userguide.pot does not contain translatable strings that also appear in
frescobaldi.pot.

"""

import argparse
import glob
import os
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("language", help="language to update")
language = parser.parse_args().language

frescobaldi_app = "frescobaldi_app/"
sys.path[0:0] = [frescobaldi_app, "i18n/"]

import appinfo
import md2pot

# 1. create a POT file for the messages, harvested from the source code
command = [
    'xgettext',
    '-D', 'i18n/frescobaldi',
    '-o', 'frescobaldi.pot',
    '--package-name={0}'.format(appinfo.name),
    '--package-version={0}'.format(appinfo.version),
    '--msgid-bugs-address={0}'.format(appinfo.maintainer_email),
    '--add-comments=L10N',
    # Empty the default keyword list
    '--keyword',
    # Custom keywords for python files.
    '--keyword=_:1c,2,3,4t',    # context, message, plural, count
    '--keyword=_:1,2,3t',       # message, plural, count
    '--keyword=_:1c,2,2t',      # context, message
    '--keyword=_:1,1t',         # message
    # Default keywords for .desktop file
    '--keyword=Name',
    '--keyword=GenericName',
    '--keyword=Comment',
    '--keyword=Icon',
    '--keyword=Keywords',
]

for root, dirs, files in sorted(os.walk("frescobaldi_app")):
    for f in sorted(files):
        if f.endswith('.py') and f[0] != '.':
            command.append(os.path.join("../../", root, f))
command.append('../../i18n/messages.py')   # dummy messages file with some Qt i18n strings
command.extend(['../../linux/org.frescobaldi.Frescobaldi.desktop.in', '../../linux/org.frescobaldi.Frescobaldi.metainfo.xml.in'])
result = subprocess.call(command)

# 2. create a POT file for the user guide
userguide = sorted(glob.glob(os.path.join(frescobaldi_app, 'userguide', '*.md')))
md2pot.md2pot('temp1.pot', userguide)

# 3. uniq that one
subprocess.call('msguniq -t UTF-8 -o temp2.pot temp1.pot'.split())
os.remove('temp1.pot')

# 4. remove dups with frescobaldi.pot from user guide
subprocess.call('msgcat --more-than=1 -o common.pot frescobaldi.pot temp2.pot'.split())
subprocess.call('msgcat --less-than=2 -o userguide.pot common.pot temp2.pot'.split())
os.remove('common.pot')
os.remove('temp2.pot')

# now we have frescobaldi.pot, and userguide.pot which does not
# contain double messages from frescobaldi.pot

frescobaldi_po = f"i18n/frescobaldi/{language}.po"
userguide_po = f"i18n/userguide/{language}.po"
subprocess.run(["msgmerge", "-U", frescobaldi_po, "frescobaldi.pot"])
subprocess.run(["msgmerge", "-U", userguide_po, "userguide.pot"])

os.remove("frescobaldi.pot")
os.remove("userguide.pot")
