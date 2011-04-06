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

rx = re.compile(br"(?:^|[^{])\{([a-z]+)")

def fields(text):
    return set(rx.findall(text))


def molint(filename):
    """Checks filename for superfluous fields in the translated messages.
    
    Returns True if there are no errors, otherwise prints messages to stderr
    and returns False.
    
    """
    correct = True
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
            correct = False
            sys.stderr.write(
                "\n{0}: Translation contains fields that are not in message!\n"
                "  Message{1}:\n".format(filename, '' if len(messages) == 1 else "s"))
            for m in messages:
                sys.stderr.write("    {0}\n".format(m))
            
            sys.stderr.write("  Offending translation{0}:\n".format('' if len(errors) == 1 else "s"))
            
            totalsuperfluous = set()
            for t, superfluous in errors:
                sys.stderr.write("    {0}\n".format(t))
                totalsuperfluous |= superfluous
            
            fieldlist = ["{{{0}}}".format(name) for name in totalsuperfluous]
            sys.stderr.write("  Fields not in message: {0}\n".format(", ".join(fieldlist)))
    
    return correct


filenames = sys.argv[1:]
if not filenames:
    sys.stderr.write(
        "usage: python molint.py <mofiles> ...\n"
        "\n"
        "checks the given MO files if the translations contain erroneous\n"
        "embedded variable names.\n"
    )
    sys.exit(2)

errorfiles = []
for filename in filenames:
    if not molint(filename):
        errorfiles.append(filename)

if errorfiles:
    sys.stderr.write("\nFiles containing errors: {0}\n".format(", ".join(errorfiles)))

sys.exit(1 if errorfiles else 0)
