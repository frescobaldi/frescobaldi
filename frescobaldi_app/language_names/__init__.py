"""
This module provides one function, languageName(), that returns
the human-readable name of a language from a codename (like 'nl').

The data is in the data.py file.
The file generate.py can be used by developers to (re-)generate
the data file.

Thanks go to the KDE developers for their translated language names
which are used currently in data.py.

"""



import itertools
import locale

from .data import language_names


__all__ = ['languageName']


def languageName(code, language=None):
    """Returns a human-readable name for a language.

    The language must be given in the 'code' attribute.
    The 'language' attribute specifies in which language
    the name must be translated and defaults to the current locale.

    """
    if language is None:
        try:
            language = locale.getdefaultlocale()[0]
        except ValueError:
            pass

    langs = []
    if language:
        langs.append(language)
        if '_' in language:
            langs.append(language.split('_')[0])
    langs.append("C")

    codes = [code]
    if '_' in code:
        codes.append(code.split('_')[0])

    for lang in langs:
        try:
            d = language_names[lang]
        except KeyError:
            continue

        for c in codes:
            try:
                return d[c]
            except KeyError:
                continue
        break
    return code


