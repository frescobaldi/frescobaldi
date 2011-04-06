#! python

"""
This script reads a MO file and checks that translated messages do not use named
string formatting fields that do not appear in the original messages.

This would cause keyword errors when the format method is called on a translated
string.
"""

import gettext
import re
import sys

try:
    mofile = sys.argv[1]
except IndexError:
    print("usage: python molint.py <mofile.mo>")
    sys.exit(1)


t = gettext.GNUTranslations(file(mofile))
rx = re.compile(r"(?:^|[^{])\{([a-z]+)")

def fields(text):
    return set(rx.findall(text))

# this trick works hopefully elsewhere as well...
for key, value in t._catalog.items():
    if isinstance(key, tuple):
        key = key[0]
    superfluous = fields(value) - fields(key)
    if superfluous:
        print('')
        print("{0}: Translation contains fields that are not in message!".format(mofile))
        print("  Message: {0}".format(key))
        print("  Translation: {0}".format(value))
        fieldlist = ["{{{0}}}".format(name) for name in superfluous]
        print("  Field(s) not in message: {0}".format(", ".join(fieldlist)))



