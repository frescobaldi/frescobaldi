#!/usr/bin/env python

"""
This script reads a MO file and checks that translated messages do not use named
string formatting fields that do not appear in the original messages.

This would cause keyword errors when the format method is called on a translated
string.
"""


import string
import sys

import mofile

_parse = string.Formatter().parse

def fields(text):
    """Returns the format field names in text as a set().

    If the text contains erroneous formatting delimiters, ValueError is raised.

    """
    return set(i[1] for i in _parse(text) if i[1] and i[1][0].isalpha())


def molint(filename):
    """Checks filename for superfluous fields in the translated messages.

    Returns True if there are no errors, otherwise prints messages to stderr
    and returns False.

    """
    correct = True
    with open(filename, 'rb') as f:
        buf = f.read()
    for context, messages, translations in mofile.parse_mo_decode(buf):

        # collect fields in messages
        s = set()
        for m in messages:
            try:
                s |= fields(m)
            except ValueError:
                pass

        if not s:
            continue

        # collect superfluous fields in translations
        errors = []
        for t in translations:
            try:
                superfluous = fields(t) - s
            except ValueError:
                errors.append((t, "Erroneous format string"))
            else:
                if superfluous:
                    errors.append((t, "Field{0} {1} not in message".format(
                        's' if len(superfluous) > 1 else '',
                        ', '.join('{{{0}}}'.format(name) for name in superfluous))))

        # write out errors if any
        if errors:
            correct = False
            sys.stderr.write(
                "\n{0}: Translation contains errors!\n"
                "  Message{1}:\n".format(filename, '' if len(messages) == 1 else "s"))
            for m in messages:
                sys.stderr.write("    {0}\n".format(m))

            sys.stderr.write("  Offending translation{0}:\n".format('' if len(errors) == 1 else "s"))

            for t, errmsg in errors:
                sys.stderr.write("    {0}:\n      {1}\n".format(errmsg, t))

    return correct


if __name__ == '__main__':
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
