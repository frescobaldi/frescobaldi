=== Creating new files ===

= New document =

By default, Frescobaldi always creates one empty document, where you can start
right away with typing LilyPond music.

It is recommended to always include the LilyPond version you plan to use for
the document at the top of the file. This way, you can always recognize which
LilyPond version you need to use to compile the document. LilyPond evolves
quite fast, so although efforts are undertaken to not change the basic syntax,
lots of new features and reorganisations of the LilyPond code sometimes
make small changes to the language necessary.

You can type {key} to insert the LilyPond version you have set as default
in the document.

If you want the version always written in any new document you create,
you can enable that in the {preferences}. It is even possible to specify
any template as the default one.

= New from template =

You can also select {menu} and select a template there.

A template is simply a snippet that has the `template` variable set.

You can define templates by creating them and then choosing {save_as_template}.
You can edit already defined templates using the command {manage_templates}.

= Using the Score Wizard =

A third way to create a new document is to use the [scorewiz Score Wizard].



#VARS
key shortcut snippets ly_version
preferences help prefs_general
menu menu file -> New from &Template
save_as_template menu file -> Save as Template...
manage_templates menu file -> New from &Template -> Manage Templates...

#SEEALSO
snippets
