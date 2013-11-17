=== Search and replace ===

In the menu {menu_edit} the commands Find ({key_search})
and Replace ({key_replace}) can be found, which open a small window at the
bottom of the view.
It is possible to search for plain text or regular expressions.

Regular expressions are advanced search texts that contain characters that can
match multiple characters in the document.
When replacing text, it is also possible to refer to parenthesized parts of the
search text.

In regular expression search mode, some characters have a special meaning:

!`*`
: matches the preceding character or group zero or more times

!`+`
: matches the preceding character or group one or more times

!`?`
: matches the preceding character or group zero or one time

!`[ ]`
: matches one of the contained characters

!`( )`
: group characters. This also saves the matched text in the group.

  When replacing, you can use characters like `\1`, `\2` etcetera,
  to write the text of the corresponding group in the replacement text.

!`\\ \n \t \s \d \w`
: match, respectively, a backslash, a newline, a tab, any whitespace
  character, a digit, a generic word-like character.

A full discussion on regular expressions can be found in the
[http://docs.python.org/library/re.html#regular-expression-syntax
Python documentation].

#VARS
key_search shortcut main edit_find
key_replace shortcut main edit_replace
menu_edit menu edit
