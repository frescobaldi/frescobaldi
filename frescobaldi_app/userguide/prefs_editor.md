=== Editor Preferences ===

= Highlighting Options =

Here you can define how long "matching" items like matching brackets or the 
items linked through Point-and-Click are highlighted.

Use the value 0 for infinite.


= Indenting Preferences =

Here you can specify how you want to handle Tabs and indenting.

The entry *Tab Width* specifies the visual distance between tab stops. It 
does not change the indenting behaviour or the document contents.

Using the entry *Indent with* you can specify how many spaces will be 
inserted it you press Tab once at the beginning of the line, or when you 
press enter after a character that starts a new level of indent
(and {menu_autoindent} is enabled).

By default 2 spaces are inserted, but you can move the number to zero to use 
a literal Tab character for every level of indent.

The entry *Tab outside indent inserts* specifies what happens when you press 
Tab while in the middle of a line of text. Also here you can choose to insert
a real Tab by moving the number to zero.

You can also set indentation preferences per-document, see
{document_variables}.


#VARS
menu_autoindent menu tools -> &Automatic Indent
document_variables help docvars

#SEEALSO
indent_format
