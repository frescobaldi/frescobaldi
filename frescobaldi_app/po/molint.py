#! python

"""
This script reads a MO file and checks that translated messages do not use named
string formatting fields that do not appear in the original messages.

This would cause keyword errors when the format method is called on a translated
string.
"""

import re
import sys

import mofile

try:
    filename = sys.argv[1]
except IndexError:
    print("usage: python molint.py <mofile.mo>")
    sys.exit(1)


rx = re.compile(br"(?:^|[^{])\{([a-z]+)")

def fields(text):
    return set(rx.findall(text))


def molint(filename):
    """Checks filename for superfluous fields in the translated messages."""
    exitCode = 0
    for context, messages, translations in mofile.parse_mo_decode(open(filename, 'rb').read()):

        # collect fields in messages
        s = set()
        for m in messages:
            s |= fields(m)
        
        # collect superfluous fields in translations
        errors = []
        for t in translations:
            superfluous = fields(t) - s
            if superfluous:
                errors.append((t, superfluous))
        
        # write out errors if any
        if errors:
            exitCode = 1
            print('')
            print("{0}: Translation contains fields that are not in message!".format(filename))
            
            print("  Message{0}:".format('' if len(messages) == 1 else "s"))
            for m in messages:
                print("    " + m)
            
            print("  Offending translation{0}:".format('' if len(errors) == 1 else "s"))
            
            totalsuperfluous = set()
            for t, superfluous in errors:
                print("    " + t)
                totalsuperfluous |= superfluous
            
            fieldlist = ["{{{0}}}".format(name) for name in totalsuperfluous]
            print("  Field(s) not in message: {0}".format(", ".join(fieldlist)))
    
    return exitCode


sys.exit(molint(filename))
