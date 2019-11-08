"""
This module contains a loader for MO files, written in 2011 by Wilbert Berendsen.

The module is heavily inspired by the Python gettext library, but allows for reading
all contents of a MO file, also the msgid2's, which are not needed for translating
but are useful e.g. when checking messages and translations for wrong Python
variable fields. Also the msgctxt is supported (the *pgettext methods).

The module provides a MoFile class, representing a MO file.

MoFile(filename)          reads the messages from the given filename,
MoFile.fromData(buffer)   reads the messages from the given bytes-string,
MoFile.fromStream(stream) reads the messages from the given stream.

The four methods 'gettext', 'pgettext', 'ngettext', 'npgettext' are like the
ones in the GNU Gettext library. If a message can't be found the fallback (settable
with the set_fallback() method is consulted. By default a NullMoFile() is used
that returns the messages untranslated. All messages are returned as unicode
strings.

The *lgettext methods are not provided but a wrapper class could easily be
created to return encoded messages.

Besides the MoFile and NullMoFile classes, the module provides some functions
that iterate over the contents of a MO file in different ways.

There are no functions to locate MO files, or to install a MoFile object
as a global translator. You can do this easily yourself e.g.:

import __builtin__
__builtin__._ = lambda *args: translation[len(args)](*args)

mo_instance = MoFile('/path/to/file.mo')

translation = [
    None,
    mo_instance.gettext,
    mo_instance.pgettext,
    mo_instance.ngettext,
    mo_instance.npgettext,
]

This way, the _( ... ) function can be called with one to four arguments, and
calls the correct method to return a translated message.

"""

__all__ = [
    'NullMoFile', 'MoFile',
    'parse_mo', 'parse_mo_split', 'parse_mo_decode',
    'parse_header', 'parse_plural_expr',
]

import re
from struct import unpack

LE_MAGIC = 0x950412de
BE_MAGIC = 0xde120495


class NullMoFile(object):
    """Empty "mo file", returning messages untranslated."""
    def gettext(self, message):
        return message

    def ngettext(self, message, message_plural, n):
        return message if n == 1 else message_plural

    def pgettext(self, context, message):
        return message

    def npgettext(self, context, message, message_plural, n):
        return message if n == 1 else message_plural

    def fallback(self):
        return None


class MoFile(NullMoFile):
    """Represents a MO translation file and provides methods to translate messages."""
    @classmethod
    def fromData(cls, buf):
        """Constructs the MoFile object, reading the messages from a bytes buffer."""
        obj = cls.__new__(cls)
        obj._load(buf)
        return obj

    @classmethod
    def fromStream(cls, stream):
        """Constructs the MoFile object, reading the messages from an open stream."""
        return cls.fromData(stream.read())

    def __init__(self, filename):
        """The default constructor reads the messages from the given filename."""
        with open(filename, 'rb') as f:
            self._load(f.read())

    def _load(self, buf):
        catalog = {}
        context_catalog = {}
        charset = 'UTF-8'
        self._plural = lambda n: int(n != 1)
        self._info = {}
        for context, msgs, tmsgs in parse_mo_split(buf):
            if msgs[0] == b'':
                # header
                info = parse_header(tmsgs[0])
                try:
                    charset = info.get(b'content-type', b'').split(b'charset=')[1].decode('ascii')
                except IndexError:
                    pass
                try:
                    plural = info.get(b'plural-forms', b'').split(b';')[1].split(b'plural=')[1]
                except IndexError:
                    pass
                else:
                    f = parse_plural_expr(plural.decode(charset))
                    if f:
                        self._plural = f
                # store as well
                self._info = dict((k, v.decode(charset)) for k, v in info.items())
            else:
                # decode
                d = context_catalog.setdefault(context.decode(charset), {}) if context else catalog
                msgid1 = msgs[0].decode(charset)
                if len(msgs) > 1:
                    # plural
                    for i, t in enumerate(tmsgs):
                        d[(msgid1, i)] = t.decode(charset)
                else:
                    # singular
                    d[msgid1] = tmsgs[0].decode(charset)
        self._catalog = catalog
        self._context_catalog = context_catalog
        self._fallback = NullMoFile()

    def set_fallback(self, fallback):
        """Sets a fallback class to return translations for messages not in this MO file.

        If fallback is None, AttributeError is raised when translations are not found.
        By default, fallback is set to a NullMoFile instance that returns the message
        untranslated.

        """
        self._fallback = fallback

    def fallback(self):
        """Returns the fallback MoFile or NullMoFile object or None.

        The fallback is called when a message is not found in our own catalog.
        By default, fallback is set to a NullMoFile instance that returns the message
        untranslated.

        """
        return self._fallback

    def info(self):
        """Returns the header (catalog description) from the MO-file as a dictionary.

        The keys are the header names in lower case, the values unicode strings.

        """
        return self._info

    def gettext(self, message):
        """Returns the translation of the message."""
        try:
            return self._catalog[message]
        except KeyError:
            return self._fallback.gettext(message)

    def ngettext(self, message, message_plural, n):
        """Returns the correct translation (singular or plural) depending on n."""
        try:
            return self._catalog[(message, self._plural(n))]
        except KeyError:
            return self._fallback.ngettext(message, message_plural, n)

    def pgettext(self, context, message):
        """Returns the translation of the message in the given context."""
        try:
            return self._context_catalog[context][message]
        except KeyError:
            return self._fallback.pgettext(context, message)

    def npgettext(self, context, message, message_plural, n):
        """Returns the correct translation (singular or plural) depending on n, in the given context."""
        try:
            return self._context_catalog[context][(message, self._plural(n))]
        except KeyError:
            return self._fallback.npgettext(context, message, message_plural, n)


def parse_mo(buf):
    """Parses the given buffer (a bytes instance) as a MO file.

    Yields raw message/translation pairs, not decoded or handled in any other way.

    """
    # are we LE or BE?
    magic = unpack('<I', buf[:4])[0]
    if magic == LE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
        ii = '<II'
    elif magic == BE_MAGIC:
        version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
        ii = '>II'
    else:
        raise IOError(0, 'Invalid MO data')

    buflen = len(buf)

    # read the MO buffer and store all data
    for i in range(msgcount):
        mlen, moff = unpack(ii, buf[masteridx:masteridx+8])
        mend = moff + mlen
        tlen, toff = unpack(ii, buf[transidx:transidx+8])
        tend = toff + tlen
        if mend < buflen and tend < buflen:
            msg = buf[moff:mend]
            tmsg = buf[toff:tend]
        else:
            raise IOError(0, 'Corrupt MO data')

        yield msg, tmsg

        masteridx += 8
        transidx += 8


def parse_header(data):
    """Parses the "header" (the msgstr of the first, empty, msgid) and returns it as a dict.

    The names are made lower-case.

    """
    info = {}
    lastkey = key = None
    for line in data.splitlines():
        line = line.strip()
        if line:
            if b':' in line:
                key, val = line.split(b':', 1)
                key = key.strip().lower()
                val = val.strip()
                info[key] = val
                lastkey = key
            elif lastkey:
                info[lastkey] += b'\n' + line
    return info


def parse_mo_split(buf):
    """Parses the mo file and splits up all messages/translation pairs.

    Yields three-element tuples: (context, messages, translations)

    where context is None or bytes, and messages and translations are both lists
    of undecoded bytes objects.

    """
    for msg, tmsg in parse_mo(buf):
        try:
            context, msg = msg.split(b'\x04')
        except ValueError:
            context = None
        yield context, msg.split(b'\x00'), tmsg.split(b'\x00')


def parse_mo_decode(buf, default_charset="UTF-8"):
    """Parses and splits, returns three-tuples like parse_mo_split but decoded to unicode."""
    charset = default_charset
    for context, msgs, tmsgs in parse_mo_split(buf):
        if msgs[0] == b'':
            info = parse_header(tmsgs[0])
            try:
                charset = info.get(b'content-type', '').split(b'charset=')[1].decode("ascii")
            except IndexError:
                pass
        yield (context.decode(charset) if context else None,
               [msg.decode(charset) for msg in msgs],
               [tmsg.decode(charset) for tmsg in tmsgs])



expr_re = re.compile(r"\d+|>>|<<|[<>!=]=|&&|\|\||[-+*/%^&<>?:|!()n]")


def parse_plural_expr(text):
    """Parses an expression such as the 'plural=<expression>' found in PO/MO files.

    Returns a lambda function taking the 'n' argument and returning the plural number.
    Returns None if the expression could not be parsed.

    """
    source = iter(expr_re.findall(text))

    def _expr():
        result = []
        for token in source:
            if token == '?':
                result.insert(0, 'if')
                result[0:0] = _expr()
                result.append('else')
                result.extend(_expr())
            elif token == ':':
                return result
            elif token == '&&':
                result.append('and')
            elif token == '||':
                result.append('or')
            elif token == '!':
                result.append('not')
            else:
                result.append(token)
                if token == '(':
                    result.extend(_expr())
                elif token == ')':
                    return result
        return result

    py_expression = ' '.join(_expr())
    if py_expression:
        code = "lambda n: int({0})".format(py_expression)
        compiled_code = compile(code, '<plural_expression>', 'eval')
        return eval(compiled_code, {}, {})

