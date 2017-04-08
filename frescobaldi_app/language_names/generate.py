#!/usr/bin/env python
# -*- coding: utf-8 -*-


import codecs
import collections
import re

"""
This script van generate a dictionary of language names.
This dictionary looks as follows:

language_names = {
    "C": {
        "nl": "Dutch",
        "de": "German",
        "en": "English",
    },
    "nl": {
        "nl": "Nederlands",
        "de": "Duits",
        "en": "Engels",
    },
}

Etcetera.

It can be created from:

- the 'all_languages' file that is part of KDE (currently the only option).


This generate.py script writes the dictionary to a file named
data.py.

This script needs not to be installed to be able to use the language_names package.

"""

# Here you should name the language names to be extracted.
# If empty, all are used. "C" must be named.

# lang_names = []
lang_names = [
    "C", "en", "de", "fr", "es", "nl", "pl", "pt_BR",
    "cs", "ru", "hu", "gl", "it", "tr", "uk",
    "ja", "zh_CN", "zh_HK", "zh_TW",
]


def generate_kde(fileName="/usr/share/locale/all_languages"):
    """Uses the KDE file to extract language names.

    Returns the dictionary. All strings are in unicode form.

    """
    langs = collections.defaultdict(dict)

    group = None
    with codecs.open(fileName, "r", "utf-8") as langfile:
        for line in langfile:
            line = line.strip()
            m = re.match(r"\[([^]]+)\]", line)
            if m:
                group = m.group(1)
            elif group and group != 'x-test':
                m = re.match(r"Name(?:\[([^]]+)\])?\s*=(.*)$", line)
                if m:
                    lang, name = m.group(1) or "C", m.group(2)
                    langs[lang][group] = name

    # correct KDE mistake
    langs["cs"]["gl"] = "Galicijský"
    langs["zh_HK"]["gl"] = "加利西亞語"
    langs["zh_HK"]["zh_HK"] = "繁體中文（香港）"
    return dict(langs)


def makestring(text):
    """Returns the text wrapped in quotes, usable as Python input (expecting unicode_literals)."""
    return '"' + re.sub(r'([\\"])', r'\\\1', text) + '"'


def write_dict(langs):
    """Writes the dictionary file to the 'data.py' file."""

    keys = sorted(filter(lambda k: k in langs, lang_names) if lang_names else langs)

    with codecs.open("data.py", "w", "utf-8") as output:
        output.write("# -*- coding: utf-8;\n\n")
        output.write("# Do not edit, this file is generated. See generate.py.\n")
        output.write("\nfrom __future__ import unicode_literals\n")
        output.write("\n\n")

        output.write("language_names = {\n")
        for key in keys:
            output.write('{0}: {{\n'.format(makestring(key)))
            for lang in sorted(langs[key]):
                output.write(' {0}:{1},\n'.format(makestring(lang), makestring(langs[key][lang])))
            output.write('},\n')
        output.write("}\n\n# End of data.py\n")


if __name__ == "__main__":
    langs = generate_kde()
    langs['zh'] = langs['zh_CN']
    write_dict(langs)

