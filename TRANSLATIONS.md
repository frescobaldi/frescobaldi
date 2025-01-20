TRANSLATIONS
============

Frescobaldi is translated using GNU Gettext and PO files.

The application PO files live in the `i18n/frescobaldi`
directory. The user guide has its own PO files under `i18n/userguide`.


## For translators

If your language is not present already, you should create the PO files.
The translation of the userguide, separated from the main application, is
optional but recommended. In order to add the language 'xx_CC', enter:

$ touch i18n/frescobaldi/xx_CC.po i18n/userguide/xx_CC.po

where 'xx_CC' is your language, e.g. 'nl_NL' (or simply 'nl').
Then add your 'xx_CC' language code to the respective LINGUAS file in
each subdirectory.

Before starting to work on the translation for your language, you
should run

  tox -e po-update -- LANG

where LANG is the language code ("de", "nl", ...). This will update
i18n/frescobaldi/LANG.po and i18n/userguide/LANG.po to match the
latest sources.

Now you can edit the xx_CC.po files in each directory with a tool like
Lokalize or Poedit. When done, you can send the translated po file(s)
to the Frescobaldi mailing list or (better) open a pull request on GitHub,
to contribute it to the Frescobaldi project.

Variable names between brackets in the messages like "Viewing page {number} of
{total}" should not be translated but exactly copied to the translation.

Finally you may want to see how your changes look in the application.
You should generate a MO (Message Object) file that Frescobaldi can read.
Simply run:

$ tox -e mo-generate

The generated MO file contains the translations from both the application
and the userguide. It will be checked for wrong variable names in translated
messages.

MO files are placed in the 'frescobaldi/i18n/' directory, so they
are packaged and installed along with Frescobaldi.


## For developers

All translatable strings should be wrapped in a _( ... ) construct.
You can use this function with one up to four arguments:

_("String")

        Simply returns a translation for the given string.

_("Context", "String")

        Returns a translation for the string in the given context.

_("Singular text", "Plural text", count)

        Returns a suitable translation (singular/plural) depending on the count.

_("Context", "Singular text", "Plural text", count)

        Returns singular or plural translation within the given context.


The context makes it possible to have different translations for the same source
message.

E.g. _("The music view, noun", "View") can return something like "Weergave",
while _("Command to view the music, verb", "View") should return "Weergeven".

Additionally, when you write a comment starting with L10N (short for
localisation), just before the line containing the string to be translated, it
will be included as a comment in the POT file.

If translatable strings need arguments, you should use named variables, e.g:

    _("About {appname}").format(appname = ...)

Always use full text sentences, without whitespace around it.

Use:        _("The file '{name}' can't be found.")
and not:    _("The file '") + name + _("' can't be found.")

Use:        _("The command exited with an error message:") + "\n\n" + errmsg
and not:    _("The command exited with an error message:\n\n") + errmsg

(You could write:

    _("The command exited with an error message:\n\n{msg}").format(msg=errmsg)

in the last case, but the first solution is the preferred one.)

Don't use empty or numbered format braces; always have a meaningful variable
name, because in other languages the order of the arguments could be different.

Use:        _("Printing page {num} of {total}...").format(num=num, total=count)
and not:    _("Printing page {} of {}...").format(num, count)

Be sure the string is translated first, then formatted. The following won't
work, although syntactically correct, because the formatted string can't be
found in the translation database:

    _("Can't find file: '{name}'".format(name=filename))

Instead, you should write:

    _("Can't find file: '{name}'").format(name=filename)
