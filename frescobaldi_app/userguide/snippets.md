=== Snippets ===

With the snippets manager you can store often used pieces of text called
"snippets", and easily paste them into the text editor.

The snippets manager can be activated via the menu {menu_snippets} or
by pressing {key_snippets}.

Snippets can be searched by browsing the list or by typing some characters
in the search entry.
Snippets can also have keyboard shortcuts applied to them.
Some snippets have a special mnemonic (short name) which you can also type
in the search entry to select the snippet. Pressing the Return key will then
apply the snippet to the text editor and hide the snippets manager.

Add new snippets using {key_add}. Edit the selected snippet with {key_edit}.
Remove selected snippets using {key_delete}. Warning: this cannot be undone!

Snippets can also be put in the menu (see {link}).
And finally, there are snippets which can include or alter selected text.
Some snippets do this by using special variables, while others are small
scripts written in Python.


#SUBDOCS
snippet_editor
snippet_lib
snippet_import_export

#VARS
link help snippet_editor
key_snippets shortcut snippettool snippettool_activate
menu_snippets menu insert -> &Snippets...
key_add text INS
key_edit text F2
key_delete text Ctrl+DEL
