=== Snippet Editor ===

Here you can edit the text of the snippet.

If you start the first line(s) with '`-*- `' (note the space),
the remainder of that line(s) defines variables like `name: value;` or
simply `name;` which influence the behaviour of the snippet.

The following variables can be used:

!`menu`
: Place the snippet in the insert menu, grouped by the (optional) value.

!`template`
: Place the snippet in the menu {file_new_from_template}, grouped by the
  (optional) value. When triggered via the menu, the snippet is inserted into a
  new document.

!`name`
: The mnemonic to type to select the snippet.

!`indent: no;`
: Do not auto-indent the snippet after inserting.

!`icon`
: The icon to show in menu and snippet list.

!`symbol`
: The symbol to show in menu and snippet list. Symbols are icons that use the
  default text color and can be found in {directory}.

!`python`
: Execute the snippet as a Python script. See {link}.

!`selection`
: !_(One of more of the following words (separated with spaces or commas):)_
  `yes`: _(Requires text to be selected.)_
  `strip`: _(Adjusts the selection to not include starting and trialing
             whitespace.)_
  `keep`: _(Selects all inserted text.)_

The other lines of the snippet define the text to be inserted in the editor. 
Here, you can insert variables prefixed with a `$`. A double `$` will be 
replaced with a single one. The following variables are recognized:
        
{snippet_editor_expander}

#SUBDOCS
snippet_python

#VARS
directory md `frescobaldi_app/symbols`
link help snippet_python
file_new_from_template menu file -> New from &Template
